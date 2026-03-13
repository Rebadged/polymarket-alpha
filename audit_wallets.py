#!/usr/bin/env python3
"""
Wallet Audit — Analyze and prune underperforming wallets
=========================================================
Reads trade history and position data from the bot to calculate
per-wallet PnL, then optionally blocks the worst performers.

Usage:
    python audit_wallets.py --docker polytrader_bot
    python audit_wallets.py --docker polytrader_bot --block-worst 3
    python audit_wallets.py --docker polytrader_bot --block-below-pnl -5
    python audit_wallets.py --docker polytrader_bot --block-below-winrate 40
"""

import argparse
import json
import subprocess
import sys
import time


def read_json(container, filename):
    try:
        result = subprocess.run(
            ["docker", "exec", container, "cat", f"/app/logs/{filename}"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except Exception:
        pass
    return None


def write_json(container, filename, data):
    json_str = json.dumps(data, indent=2)
    try:
        result = subprocess.run(
            ["docker", "exec", "-i", container, "tee", f"/app/logs/{filename}"],
            input=json_str, capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="Audit tracked wallets by PnL performance")
    parser.add_argument("--docker", required=True, help="Docker container name")
    parser.add_argument("--block-worst", type=int, default=0,
                        help="Block the N worst performing wallets")
    parser.add_argument("--block-below-pnl", type=float, default=None,
                        help="Block wallets with total PnL below this (e.g. -5 for -$5)")
    parser.add_argument("--block-below-winrate", type=float, default=None,
                        help="Block wallets with win rate below this %% (e.g. 40)")
    parser.add_argument("--min-trades", type=int, default=3,
                        help="Only evaluate wallets with at least N trades (default: 3)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be blocked without doing it")

    args = parser.parse_args()
    container = args.docker

    print("=" * 60)
    print("  WALLET AUDIT — Performance Analysis")
    print(f"  Container: {container}")
    print("=" * 60)
    print()

    # Load data
    print("[1/4] Loading bot data...")
    trades = read_json(container, "trades.json") or []
    positions = read_json(container, "positions.json") or []
    copy_state = read_json(container, "copy_state.json") or {}
    tracked = read_json(container, "tracked_wallets.json") or []
    manual = read_json(container, "tracked_wallets_manual.json") or []
    blocked = read_json(container, "tracked_wallets_blocked.json") or []

    position_leaders = copy_state.get("position_leaders", {})

    print(f"  Trades: {len(trades)}")
    print(f"  Positions: {len(positions)}")
    print(f"  Position-leader links: {len(position_leaders)}")
    print(f"  Tracked wallets: {len(tracked)} (manual={len(manual)}, blocked={len(blocked)})")
    print()

    # Build per-wallet stats from trades
    print("[2/4] Analyzing per-wallet performance...")

    wallet_stats = {}

    # Map condition_id -> leader wallet from trades
    condition_to_wallet = {}
    for t in trades:
        src = t.get("copy_source_full") or t.get("copy_source") or ""
        cond = t.get("condition_id", "")
        if src and cond:
            condition_to_wallet[cond.lower()] = src.lower()

    # Also use position_leaders mapping
    for cond_short, leader_full in position_leaders.items():
        if leader_full:
            condition_to_wallet["0x" + cond_short.lower() if not cond_short.startswith("0x") else cond_short.lower()] = leader_full.lower()

    # Aggregate trades per wallet
    for t in trades:
        src = (t.get("copy_source_full") or t.get("copy_source") or "unknown").lower()
        if src == "unknown":
            continue

        if src not in wallet_stats:
            wallet_stats[src] = {
                "address": src,
                "short": src[:10] + "..." if len(src) > 10 else src,
                "trades": 0,
                "invested": 0.0,
                "positions": [],
                "pnl": 0.0,
                "wins": 0,
                "losses": 0,
                "neutral": 0,
            }

        wallet_stats[src]["trades"] += 1
        wallet_stats[src]["invested"] += float(t.get("amount_usdc", 0) or 0)

    # Match positions to wallets and calculate PnL
    for pos in positions:
        cond = (pos.get("conditionId") or "").lower()
        pnl = float(pos.get("cashPnl", 0) or 0)
        pct_pnl = float(pos.get("percentPnl", 0) or 0)
        cur_price = float(pos.get("curPrice", 0) or 0)
        avg_price = float(pos.get("avgPrice", 0) or 0)
        title = pos.get("title", "")

        # Find which wallet this position came from
        wallet = condition_to_wallet.get(cond, "")
        if not wallet:
            # Try partial match
            for key, val in condition_to_wallet.items():
                if cond and key and (cond in key or key in cond):
                    wallet = val
                    break

        if not wallet or wallet not in wallet_stats:
            continue

        wallet_stats[wallet]["pnl"] += pnl
        wallet_stats[wallet]["positions"].append({
            "title": title[:40],
            "pnl": round(pnl, 2),
            "pct": round(pct_pnl, 1),
            "cur_price": cur_price,
        })

        if pnl > 0.01:
            wallet_stats[wallet]["wins"] += 1
        elif pnl < -0.01:
            wallet_stats[wallet]["losses"] += 1
        else:
            wallet_stats[wallet]["neutral"] += 1

    # Calculate win rates
    for ws in wallet_stats.values():
        total = ws["wins"] + ws["losses"]
        ws["win_rate"] = round((ws["wins"] / total * 100) if total > 0 else 0, 1)
        ws["pnl"] = round(ws["pnl"], 2)
        ws["roi"] = round((ws["pnl"] / ws["invested"] * 100) if ws["invested"] > 0 else 0, 1)

    # Get wallet names from tracked list
    name_lookup = {}
    for w in tracked + manual:
        addr = (w.get("address") or "").lower()
        name = w.get("name") or w.get("label") or ""
        if addr and name:
            name_lookup[addr] = name

    # Sort by PnL
    sorted_wallets = sorted(wallet_stats.values(), key=lambda x: x["pnl"])

    # Display
    print()
    print(f"  {'#':<4} {'Wallet':<22} {'Trades':>7} {'Invested':>10} {'PnL':>10} {'ROI':>8} {'W/L':>7} {'WR%':>7}")
    print("  " + "-" * 85)

    for i, ws in enumerate(sorted_wallets):
        if ws["trades"] < 1:
            continue
        name = name_lookup.get(ws["address"], ws["short"])[:20]
        wl = str(ws["wins"]) + "/" + str(ws["losses"])
        pnl_color = "" 
        print(
            f"  {i+1:<4} {name:<22} "
            f"{ws['trades']:>7} "
            f"{'$'+str(round(ws['invested'])):>10} "
            f"{'$'+str(ws['pnl']):>10} "
            f"{str(ws['roi'])+'%':>8} "
            f"{wl:>7} "
            f"{str(ws['win_rate'])+'%':>7}"
        )

    print("  " + "-" * 85)
    print()

    # Summary stats
    total_pnl = sum(ws["pnl"] for ws in wallet_stats.values())
    total_invested = sum(ws["invested"] for ws in wallet_stats.values())
    profitable = sum(1 for ws in wallet_stats.values() if ws["pnl"] > 0 and ws["trades"] >= args.min_trades)
    unprofitable = sum(1 for ws in wallet_stats.values() if ws["pnl"] < 0 and ws["trades"] >= args.min_trades)

    print(f"  Total PnL: ${total_pnl:.2f}")
    print(f"  Total invested: ${total_invested:.2f}")
    print(f"  Profitable wallets: {profitable}")
    print(f"  Unprofitable wallets: {unprofitable}")
    print()

    # Determine which wallets to block
    print("[3/4] Identifying underperformers...")

    to_block = []
    eligible = [ws for ws in sorted_wallets if ws["trades"] >= args.min_trades]

    if args.block_worst and args.block_worst > 0:
        worst = eligible[:args.block_worst]
        for ws in worst:
            if ws["pnl"] < 0:
                to_block.append(ws)
        print(f"  Block worst {args.block_worst}: {len(to_block)} wallets qualify (negative PnL + min {args.min_trades} trades)")

    if args.block_below_pnl is not None:
        for ws in eligible:
            if ws["pnl"] < args.block_below_pnl and ws not in to_block:
                to_block.append(ws)
        print(f"  Block below ${args.block_below_pnl} PnL: {len(to_block)} total")

    if args.block_below_winrate is not None:
        for ws in eligible:
            if ws["win_rate"] < args.block_below_winrate and ws not in to_block:
                to_block.append(ws)
        print(f"  Block below {args.block_below_winrate}% win rate: {len(to_block)} total")

    if not to_block:
        if not (args.block_worst or args.block_below_pnl is not None or args.block_below_winrate is not None):
            print("  No blocking criteria specified. Use --block-worst, --block-below-pnl, or --block-below-winrate")
        else:
            print("  No wallets meet blocking criteria.")
        print()
        print("[4/4] Done — no changes made.")
        return

    print()
    print("  Wallets to block:")
    for ws in to_block:
        name = name_lookup.get(ws["address"], ws["short"])[:20]
        print(f"    {name:<22} PnL=${ws['pnl']:<8} WR={ws['win_rate']}% Trades={ws['trades']}")

    if args.dry_run:
        print()
        print("  DRY RUN — no changes made.")
        return

    # Block wallets
    print()
    print("[4/4] Blocking underperformers...")

    # Add to blocked list
    blocked_set = set(str(a).strip().lower() for a in blocked)
    added = 0
    for ws in to_block:
        addr = ws["address"].lower()
        if addr not in blocked_set:
            blocked.append(addr)
            blocked_set.add(addr)
            added += 1

    # Remove from manual list
    manual_before = len(manual)
    manual = [w for w in manual if (w.get("address") or "").lower() not in blocked_set]
    removed_manual = manual_before - len(manual)

    # Write back
    ok1 = write_json(container, "tracked_wallets_blocked.json", sorted(blocked))
    ok2 = write_json(container, "tracked_wallets_manual.json", manual)

    if ok1 and ok2:
        print(f"  OK  Blocked {added} wallets")
        print(f"  OK  Removed {removed_manual} from manual list")
        print(f"  OK  Bot will hot-reload on next cycle")
    else:
        print(f"  WARN  Write may have failed — check manually")

    print()
    print("  TIP: To unblock a wallet later, remove it from tracked_wallets_blocked.json")
    print("       or use the bot's dashboard.")
    print()


if __name__ == "__main__":
    main()
