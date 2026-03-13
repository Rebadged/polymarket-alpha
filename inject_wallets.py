#!/usr/bin/env python3
"""
Polymarket Scraper → PolyTrader CopyBot Bridge v3
===================================================
Time-aware wallet injection with category-based scheduling.

Windows (Pacific Time):
  - PRIME TIME  (5pm - 11pm): Sports-heavy, all categories active
  - OVERNIGHT   (11pm - 9am): Crypto/Geopolitics/Politics focus, sports deprioritized
  - DAYTIME     (9am - 5pm):  Mixed, slight pre-game sports boost

Behaviors:
  - Top 5 wallets by raw score ALWAYS stay regardless of time window
  - Sports-heavy wallets get score penalties overnight
  - 24/7 categories (Crypto, Geopolitics, Politics) get bonus overnight
  - Replaces previous scraper wallets, preserves dashboard hand-added
  - Bot hot-reloads automatically

Usage:
    python inject_wallets.py --source polymarket_wallets.json --docker polytrader_bot
    python inject_wallets.py --source polymarket_wallets.json --docker polytrader_bot --dry-run
    python inject_wallets.py --source polymarket_wallets.json --docker polytrader_bot --force-window overnight
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta

# ── Defaults ─────────────────────────────────────────────────────────
DEFAULT_MAX_WALLETS = 20
DEFAULT_MIN_WIN_RATE = 50.0
DEFAULT_MIN_ROI = 0.0
DEFAULT_MIN_TRADES = 5
DEFAULT_MAX_INACTIVE_HOURS = 48
DEFAULT_TOP_KEEP = 5  # Always keep top N regardless of time window
TIMEZONE_OFFSET = -7  # Pacific Daylight Time (UTC-7). Change to -8 for PST.

# Paths inside the PolyTrader container
BOT_LOGS_DIR = "/app/logs"
TRACKED_MANUAL = "tracked_wallets_manual.json"

SCRAPER_SOURCE = "scraper"
RUNTIME_CONFIG = "runtime_config.json"

# ── Bot Settings Per Window ──────────────────────────────────────────
# These get written to runtime_config.json and hot-reloaded by the bot.
# Only the keys listed here are touched — everything else is preserved.
WINDOW_BOT_SETTINGS = {
    "primetime": {
        "COPY_MAX_EVENT_DAYS_AHEAD": 1,   # Sports: today + tomorrow only
        "TAKE_PROFIT_PCT": 0.0,            # Let sports winners ride to resolution
        "STOP_LOSS_PCT": 15.0,             # Tight stop on losers
    },
    "overnight": {
        "COPY_MAX_EVENT_DAYS_AHEAD": 0,   # No restriction (politics/crypto don't have "game day")
        "TAKE_PROFIT_PCT": 20.0,           # Cash out politics/crypto gains, free capital
        "STOP_LOSS_PCT": 15.0,             # Same tight stop
    },
    "daytime": {
        "COPY_MAX_EVENT_DAYS_AHEAD": 1,   # Pre-game: today + tomorrow
        "TAKE_PROFIT_PCT": 0.0,            # No TP — games approaching, let them ride
        "STOP_LOSS_PCT": 15.0,             # Tight stop
    },
}

# ── Time Windows ─────────────────────────────────────────────────────
# Categories that are active 24/7 (don't depend on game schedules)
ALWAYS_ON_CATEGORIES = {"Crypto", "Geopolitics", "Politics", "Economics", "Tech", "Weather"}
# Categories tied to game schedules
SPORTS_CATEGORIES = {"Sports"}
# Categories that are mixed
CULTURE_CATEGORIES = {"Culture", "Finance", "Other"}

def get_current_window(force_window=None):
    """Determine the current time window based on Pacific Time."""
    if force_window:
        return force_window

    utc_now = datetime.now(timezone.utc)
    pacific = utc_now + timedelta(hours=TIMEZONE_OFFSET)
    hour = pacific.hour

    if 17 <= hour < 23:           # 5pm - 11pm PT
        return "primetime"
    elif 23 <= hour or hour < 9:  # 11pm - 9am PT
        return "overnight"
    else:                         # 9am - 5pm PT
        return "daytime"


def get_window_config(window):
    """Return scoring adjustments for each time window."""
    configs = {
        "primetime": {
            "label": "PRIME TIME (5pm-11pm PT)",
            "emoji": "🏀",
            "description": "Sports live — all categories active, sports boosted",
            # Score multipliers by category presence
            "sports_bonus": 1.3,        # 30% boost if wallet trades sports
            "always_on_bonus": 1.0,     # No change
            "sports_only_penalty": 0.8, # Slight penalty if ONLY sports (no diversification)
        },
        "overnight": {
            "label": "OVERNIGHT (11pm-9am PT)",
            "emoji": "🌙",
            "description": "Sports quiet — prioritizing 24/7 markets",
            "sports_bonus": 0.5,        # 50% penalty for sports-heavy wallets
            "always_on_bonus": 1.4,     # 40% boost for crypto/geopolitics/politics
            "sports_only_penalty": 0.2, # Heavy penalty if ONLY sports
        },
        "daytime": {
            "label": "DAYTIME (9am-5pm PT)",
            "emoji": "☀️",
            "description": "Mixed — pre-game sports + all categories",
            "sports_bonus": 1.1,        # Slight boost for sports (games coming)
            "always_on_bonus": 1.1,     # Slight boost for always-on too
            "sports_only_penalty": 0.7, # Mild penalty for sports-only
        },
    }
    return configs.get(window, configs["daytime"])


def classify_wallet_categories(categories):
    """Classify a wallet's category mix."""
    cats = set(categories) if categories else set()
    has_sports = bool(cats & SPORTS_CATEGORIES)
    has_always_on = bool(cats & ALWAYS_ON_CATEGORIES)
    is_sports_only = has_sports and not has_always_on
    is_always_on_only = has_always_on and not has_sports
    is_mixed = has_sports and has_always_on

    return {
        "has_sports": has_sports,
        "has_always_on": has_always_on,
        "is_sports_only": is_sports_only,
        "is_always_on_only": is_always_on_only,
        "is_mixed": is_mixed,
        "categories": cats,
    }


def load_source(source: str) -> dict:
    if source.startswith("http://") or source.startswith("https://"):
        import requests
        print(f"  Fetching from URL: {source}")
        resp = requests.get(source, timeout=30)
        resp.raise_for_status()
        return resp.json()
    else:
        print(f"  Loading from file: {source}")
        with open(source, "r") as f:
            return json.load(f)


def filter_and_rank(wallets: list, max_wallets: int, min_win_rate: float,
                     min_roi: float, min_trades: int, max_inactive_hours: int,
                     window: str, top_keep: int) -> list:
    """Filter, apply time-aware scoring, and rank wallets."""
    wconfig = get_window_config(window)
    candidates = []
    skipped_inactive = 0
    skipped_filters = 0

    for w in wallets:
        enriched = w.get("enriched")
        if not enriched:
            continue

        addr = w.get("proxyWallet", "")
        if not addr.startswith("0x") or len(addr) != 42:
            continue

        win_rate = enriched.get("winRate", 0)
        roi = enriched.get("roi", 0)
        total_trades = enriched.get("totalTrades", 0)
        categories = enriched.get("categories", [])

        # Activity check
        if max_inactive_hours > 0:
            last_ts = enriched.get("lastTradeTimestamp", 0)
            if last_ts and last_ts > 0:
                hours_ago = (time.time() - last_ts) / 3600
                if hours_ago > max_inactive_hours:
                    skipped_inactive += 1
                    continue

        # Quality filters
        if win_rate < min_win_rate:
            skipped_filters += 1
            continue
        if roi < min_roi:
            skipped_filters += 1
            continue
        if total_trades < min_trades:
            skipped_filters += 1
            continue

        # Base score (same as scraper)
        activity_bonus = min(10, enriched.get("tradesInWindow", 0) * 0.5)
        base_score = (
            roi * 0.25 +
            win_rate * 0.3 +
            enriched.get("sharpe", 0) * 20 +
            enriched.get("consistency", 0) * 0.1 +
            activity_bonus
        )

        # Time-aware score adjustment
        cat_info = classify_wallet_categories(categories)
        time_multiplier = 1.0

        if cat_info["is_sports_only"]:
            time_multiplier = wconfig["sports_only_penalty"]
        elif cat_info["has_sports"] and cat_info["has_always_on"]:
            # Mixed wallet — blend the bonuses
            time_multiplier = (wconfig["sports_bonus"] + wconfig["always_on_bonus"]) / 2
        elif cat_info["has_sports"]:
            time_multiplier = wconfig["sports_bonus"]
        elif cat_info["has_always_on"]:
            time_multiplier = wconfig["always_on_bonus"]

        adjusted_score = base_score * time_multiplier

        candidates.append({
            "address": addr,
            "base_score": round(base_score, 2),
            "score": round(adjusted_score, 2),
            "time_multiplier": round(time_multiplier, 2),
            "win_rate": round(win_rate / 100, 4),
            "roi": round(roi / 100, 6),
            "total_pnl": round(w.get("pnl", 0), 2),
            "total_invested": round(enriched.get("totalInvested", 0), 2),
            "total_trades": total_trades,
            "resolved_trades": total_trades,
            "wins": enriched.get("wins", 0),
            "losses": enriched.get("losses", 0),
            "trades_per_day": 0,
            "crypto_ratio": 0,
            "rank": w.get("rank", 999),
            "name": w.get("userName", ""),
            "label": w.get("userName", "") or f"scraper-{addr[:8]}",
            "scored_at": time.time(),
            "source": SCRAPER_SOURCE,
            "_categories": categories,
            "_cat_type": "sports-only" if cat_info["is_sports_only"] else
                         "24/7" if cat_info["is_always_on_only"] else
                         "mixed" if cat_info["is_mixed"] else "other",
            "_lastTradeAge": enriched.get("lastTradeAge", "unknown"),
            "_tradesInWindow": enriched.get("tradesInWindow", 0),
        })

    # Sort by BASE score first to find the true top N
    candidates.sort(key=lambda x: x["base_score"], reverse=True)

    # Lock in the top N by base score — these always stay
    locked = []
    remaining = []
    locked_addrs = set()

    for c in candidates:
        if len(locked) < top_keep:
            locked.append(c)
            locked_addrs.add(c["address"])
        else:
            remaining.append(c)

    # Sort remaining by TIME-ADJUSTED score
    remaining.sort(key=lambda x: x["score"], reverse=True)

    # Fill remaining slots
    slots_left = max_wallets - len(locked)
    selected_remaining = remaining[:slots_left]

    # Combine: locked first, then time-adjusted picks
    final = locked + selected_remaining

    # Stats
    cat_types = {}
    for w in final:
        ct = w.get("_cat_type", "other")
        cat_types[ct] = cat_types.get(ct, 0) + 1

    print(f"  Filtered: {len(wallets)} total -> {len(candidates)} passed"
          f" (skipped: {skipped_filters} quality, {skipped_inactive} inactive)")
    print(f"  Locked top {top_keep}: {', '.join(w['name'] or w['address'][:10] for w in locked)}")
    print(f"  Time-adjusted picks: {len(selected_remaining)}")
    print(f"  Composition: {', '.join(f'{k}={v}' for k, v in sorted(cat_types.items()))}")
    print(f"  Total selected: {len(final)} (max {max_wallets})")

    return final


def read_from_docker(container: str, filename: str) -> list:
    path = f"{BOT_LOGS_DIR}/{filename}"
    try:
        result = subprocess.run(
            ["docker", "exec", container, "cat", path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except Exception:
        pass
    return []


def write_to_docker(container: str, filename: str, data) -> bool:
    path = f"{BOT_LOGS_DIR}/{filename}"
    json_str = json.dumps(data, indent=2)
    subprocess.run(
        ["docker", "exec", container, "mkdir", "-p", BOT_LOGS_DIR],
        capture_output=True, timeout=10
    )
    try:
        result = subprocess.run(
            ["docker", "exec", "-i", container, "tee", path],
            input=json_str, capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def smart_merge_manual(existing: list, new_scraper_wallets: list) -> list:
    hand_added = []
    removed_scraper = 0
    for w in existing:
        if w.get("source") == SCRAPER_SOURCE:
            removed_scraper += 1
        else:
            hand_added.append(w)

    if removed_scraper > 0:
        print(f"  Replacing {removed_scraper} previous scraper wallets")
    if hand_added:
        print(f"  Preserving {len(hand_added)} hand-added wallets")

    seen = set()
    merged = []
    for w in hand_added:
        addr = (w.get("address") or "").strip().lower()
        if addr and addr not in seen:
            seen.add(addr)
            merged.append(w)
    for w in new_scraper_wallets:
        addr = (w.get("address") or "").strip().lower()
        if addr and addr not in seen:
            seen.add(addr)
            merged.append(w)
    return merged


def clean_for_write(wallets: list) -> list:
    clean = []
    for w in wallets:
        cw = {k: v for k, v in w.items() if not k.startswith("_")}
        clean.append(cw)
    return clean


def update_runtime_config(container: str, window: str, dry_run: bool = False):
    """Update the bot's runtime_config.json with time-window-specific settings.

    Reads the existing config, updates only the window-specific keys,
    and writes it back. The bot hot-reloads this file automatically.
    """
    settings = WINDOW_BOT_SETTINGS.get(window, {})
    if not settings:
        return

    # Read existing runtime config
    existing = {}
    try:
        result = subprocess.run(
            ["docker", "exec", container, "cat", f"{BOT_LOGS_DIR}/{RUNTIME_CONFIG}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            existing = json.loads(result.stdout)
    except Exception:
        pass

    # Check what's changing
    changes = {}
    for key, new_val in settings.items():
        old_val = existing.get(key)
        if old_val != new_val:
            changes[key] = {"from": old_val, "to": new_val}
        existing[key] = new_val

    if not changes:
        print(f"  Bot settings unchanged for {window} window")
        return

    # Show what's changing
    for key, diff in changes.items():
        print(f"  {key}: {diff['from']} -> {diff['to']}")

    if dry_run:
        print("  (dry run — not writing)")
        return

    # Write back
    json_str = json.dumps(existing, indent=2)
    try:
        result = subprocess.run(
            ["docker", "exec", "-i", container, "tee", f"{BOT_LOGS_DIR}/{RUNTIME_CONFIG}"],
            input=json_str, capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print(f"  OK  Bot settings updated for {window} window")
        else:
            print(f"  WARN  Failed to update runtime config")
    except Exception as e:
        print(f"  WARN  Failed to update runtime config: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Time-aware wallet injection into PolyTrader CopyBot"
    )
    parser.add_argument("--source", required=True, help="Path or URL to polymarket_wallets.json")
    parser.add_argument("--docker", default=None, help="Docker container name")
    parser.add_argument("--bot-dir", default=None, help="Local bot directory")
    parser.add_argument("--max-wallets", type=int, default=DEFAULT_MAX_WALLETS)
    parser.add_argument("--min-win-rate", type=float, default=DEFAULT_MIN_WIN_RATE)
    parser.add_argument("--min-roi", type=float, default=DEFAULT_MIN_ROI)
    parser.add_argument("--min-trades", type=int, default=DEFAULT_MIN_TRADES)
    parser.add_argument("--max-inactive-hours", type=int, default=DEFAULT_MAX_INACTIVE_HOURS)
    parser.add_argument("--top-keep", type=int, default=DEFAULT_TOP_KEEP,
                        help=f"Always keep top N wallets regardless of time (default: {DEFAULT_TOP_KEEP})")
    parser.add_argument("--force-window", choices=["primetime", "overnight", "daytime"], default=None,
                        help="Force a specific time window (for testing)")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    # Determine time window
    window = get_current_window(args.force_window)
    wconfig = get_window_config(window)

    print("=" * 60)
    print("  POLYMARKET SCRAPER -> POLYTRADER BRIDGE v3")
    print(f"  {wconfig['emoji']}  Window: {wconfig['label']}")
    print(f"     {wconfig['description']}")
    print(f"  Source:  {args.source}")
    print(f"  Max:     {args.max_wallets} wallets (top {args.top_keep} locked)")
    print(f"  Filters: WR>={args.min_win_rate}%  ROI>={args.min_roi}%  Trades>={args.min_trades}")
    if args.docker:
        print(f"  Docker:  {args.docker}")
    print("=" * 60)
    print()

    # 1. Load
    print("[1/5] Loading scraper data...")
    try:
        data = load_source(args.source)
    except Exception as e:
        print(f"  FAILED: {e}")
        sys.exit(1)

    wallets = data.get("wallets", [])
    metadata = data.get("metadata", {})
    print(f"  Loaded {len(wallets)} wallets (scraped: {metadata.get('scraped_at', 'unknown')})")
    print()

    # 2. Filter and rank with time awareness
    print(f"[2/5] Filtering with {wconfig['label']} scoring...")
    selected = filter_and_rank(
        wallets, args.max_wallets, args.min_win_rate,
        args.min_roi, args.min_trades, args.max_inactive_hours,
        window, args.top_keep
    )

    if not selected:
        print("  No wallets passed filters.")
        sys.exit(0)

    # 3. Preview
    print()
    print(f"[3/5] Selected wallets ({wconfig['emoji']} {window}):")
    print(f"  {'#':<4} {'Name':<22} {'Score':>7} {'Base':>7} {'Mult':>6} {'WR%':>7} {'Type':>12}  {'Active':>10}")
    print("  " + "-" * 95)
    for i, w in enumerate(selected):
        name = (w.get("name") or w["address"][:14])[:20]
        locked = " *" if i < args.top_keep else ""
        print(
            f"  {i+1:<4} {name:<22} "
            f"{w['score']:>7.1f} "
            f"{w['base_score']:>7.1f} "
            f"{w.get('time_multiplier', 1.0):>5.1f}x "
            f"{w.get('win_rate', 0)*100:>6.1f}% "
            f"{w.get('_cat_type', '?'):>12}  "
            f"{w.get('_lastTradeAge', '?'):>10}"
            f"{locked}"
        )
    print()
    print(f"  * = locked (top {args.top_keep} by raw score, always included)")
    print()

    if args.dry_run:
        print("  DRY RUN -- no changes written.")
        if args.docker:
            print()
            print("  Bot settings that WOULD change:")
            update_runtime_config(args.docker, window, dry_run=True)
        return

    # 4. Merge
    print("[4/6] Merging with existing manual list...")
    if args.docker:
        existing = read_from_docker(args.docker, TRACKED_MANUAL)
    elif args.bot_dir:
        from pathlib import Path
        existing = json.loads((Path(args.bot_dir) / "logs" / TRACKED_MANUAL).read_text()) if (Path(args.bot_dir) / "logs" / TRACKED_MANUAL).exists() else []
    else:
        existing = []

    hand_count = sum(1 for w in existing if w.get("source") != SCRAPER_SOURCE)
    scraper_count = sum(1 for w in existing if w.get("source") == SCRAPER_SOURCE)
    print(f"  Existing: {len(existing)} ({hand_count} hand-added, {scraper_count} scraper)")

    clean_selected = clean_for_write(selected)
    merged = smart_merge_manual(existing, clean_selected)
    final_hand = sum(1 for w in merged if w.get("source") != SCRAPER_SOURCE)
    final_scraper = sum(1 for w in merged if w.get("source") == SCRAPER_SOURCE)
    print(f"  After merge: {len(merged)} ({final_hand} hand-added + {final_scraper} scraper)")
    print()

    # 5. Write wallets
    print("[5/6] Writing wallets to bot...")
    if args.docker:
        ok = write_to_docker(args.docker, TRACKED_MANUAL, merged)
        if ok:
            print(f"  OK  Wrote {len(merged)} wallets -> {TRACKED_MANUAL}")
        else:
            print(f"  FAIL")
            sys.exit(1)
    elif args.bot_dir:
        from pathlib import Path
        path = Path(args.bot_dir) / "logs" / TRACKED_MANUAL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(merged, indent=2))
        print(f"  OK  Wrote {len(merged)} wallets -> {path}")
    else:
        out = f"output_{TRACKED_MANUAL}"
        with open(out, "w") as f:
            json.dump(merged, indent=2, fp=f)
        print(f"  OK  Wrote to {out}")
    print()

    # 6. Update bot runtime settings for this window
    print(f"[6/6] Updating bot settings for {window} window...")
    if args.docker:
        update_runtime_config(args.docker, window)

    # Summary
    settings = WINDOW_BOT_SETTINGS.get(window, {})
    print()
    print("  ┌──────────────────────────────────────────────────────┐")
    print(f"  │  {wconfig['emoji']}  Window:  {wconfig['label']:<36} │")
    print(f"  │  Scraper wallets:  {final_scraper:>3}  (time-optimized)            │")
    print(f"  │  Hand-added:       {final_hand:>3}  (preserved)                  │")
    print(f"  │  Top {args.top_keep} locked:     always included                 │")
    print(f"  │  Bot auto-wallets: untouched                        │")
    print(f"  │  Event horizon:    {settings.get('COPY_MAX_EVENT_DAYS_AHEAD', '?')} days                           │")
    print(f"  │  Take profit:      {settings.get('TAKE_PROFIT_PCT', '?')}%                           │")
    print(f"  │  Stop loss:        {settings.get('STOP_LOSS_PCT', '?')}%                           │")
    print("  └──────────────────────────────────────────────────────┘")
    print()


if __name__ == "__main__":
    main()
