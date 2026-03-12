#!/usr/bin/env python3
"""
Polymarket Leaderboard Scraper v3
---------------------------------
- Activity filter: only keeps wallets active within last N hours
- Fixed win rate: sorts by TIMESTAMP not REALIZEDPNL (no winner bias)
- Expanded categories: Sports, Politics, Geopolitics, Crypto, Culture,
  Economics, Weather, Tech, Finance
- Paginates up to 250 closed positions for better accuracy

Usage:
    pip install requests
    python polymarket_scraper.py

Output:
    polymarket_wallets.json
"""

import requests
import json
import time
import re
import math
import sys
from datetime import datetime, timezone, timedelta

# ============================================================
# CONFIG
# ============================================================
CATEGORY = "OVERALL"         # OVERALL, POLITICS, SPORTS, CRYPTO, CULTURE
TIME_PERIOD = "ALL"          # ALL, MONTH, WEEK, DAY
TOP_N = 100                  # Wallets to pull from leaderboard
ACTIVITY_WINDOW_HOURS = 24   # Only keep wallets active within this window (0 = no filter)
RATE_LIMIT_DELAY = 0.25      # Seconds between API calls
OUTPUT_FILE = "polymarket_wallets.json"
# ============================================================

LEADERBOARD_URL = "https://data-api.polymarket.com/v1/leaderboard"
CLOSED_POS_URL  = "https://data-api.polymarket.com/closed-positions"
OPEN_POS_URL    = "https://data-api.polymarket.com/positions"
TRADES_URL      = "https://data-api.polymarket.com/trades"
ACTIVITY_URL    = "https://data-api.polymarket.com/activity"

# --- Category patterns ---
CATEGORIES = {
    "Sports": re.compile(
        r'nba|nfl|mlb|nhl|soccer|football|tennis|ufc|boxing|f1|sport|game|match|'
        r'series|playoff|championship|super bowl|world cup|premier league|score|'
        r'goals|points|winner.*game|ncaa|march madness|stanley cup|world series|'
        r'lakers|celtics|yankees|dodgers|mls|la liga|bundesliga|serie a|cricket|'
        r'olympics|medal|grand slam|pga|golf|nascar|formula|epl|champions league|'
        r'touchdown|home run|three.pointer|penalty|red card|knockout|round.*fight',
        re.IGNORECASE),
    "Politics": re.compile(
        r'president|election|congress|senate|governor|democrat|republican|trump|'
        r'biden|harris|poll|vote|political|gop|dnc|rnc|primary|caucus|cabinet|'
        r'impeach|legislation|bill.*pass|supreme court|scotus|veto|executive order|'
        r'approval rating|midterm|runoff|speaker|majority|filibuster|pardon|'
        r'attorney general|secretary|confirmation|swing state|electoral',
        re.IGNORECASE),
    "Geopolitics": re.compile(
        r'war|conflict|nato|un\b|china|russia|ukraine|iran|israel|gaza|taiwan|'
        r'sanctions|geopolit|military|troops|missile|ceasefire|invasion|tariff|'
        r'trade war|embargo|nuclear|north korea|houthi|yemen|syria|coup|'
        r'peace deal|treaty|annexation|territorial|drone strike|proxy war|'
        r'diplomatic|ambassador|sovereignty|occupation|border dispute',
        re.IGNORECASE),
    "Crypto": re.compile(
        r'bitcoin|btc|ethereum|eth|crypto|solana|sol|token|defi|nft|blockchain|'
        r'altcoin|binance|coinbase|memecoin|dogecoin|shib|ripple|xrp|cardano|'
        r'polygon|matic|avalanche|avax|stablecoin|usdc|usdt|tether|mining|'
        r'halving|etf.*crypto|crypto.*etf|web3|layer.?2|rollup',
        re.IGNORECASE),
    "Economics": re.compile(
        r'fed\b|federal reserve|interest rate|inflation|cpi|gdp|recession|'
        r'unemployment|jobs report|nonfarm|payroll|treasury|yield|bond|'
        r'rate cut|rate hike|fomc|monetary policy|fiscal|stimulus|debt ceiling|'
        r'housing market|consumer confidence|retail sales|manufacturing|pmi|'
        r'trade deficit|tariff|import|export|wage growth|labor market',
        re.IGNORECASE),
    "Tech": re.compile(
        r'ai\b|artificial intelligence|openai|google|apple|microsoft|meta\b|'
        r'amazon|nvidia|tesla|spacex|launch|rocket|starship|gpt|llm|chatbot|'
        r'chip|semiconductor|tsmc|antitrust|data breach|cybersecurity|hack|'
        r'iphone|android|tiktok|ban|regulation.*tech|robot|autonomous|self.driving|'
        r'quantum|fusion|starlink|satellite',
        re.IGNORECASE),
    "Culture": re.compile(
        r'oscar|grammy|emmy|award|movie|film|album|song|artist|celebrity|'
        r'viral|tiktok|youtube|streamer|twitch|kardashian|swift|beyonce|'
        r'drake|kanye|musk.*tweet|reality tv|bachelor|survivor|squid game|'
        r'netflix|disney|box office|concert|festival|fashion|met gala',
        re.IGNORECASE),
    "Weather": re.compile(
        r'hurricane|tornado|earthquake|flood|wildfire|temperature|record.*hot|'
        r'record.*cold|snowfall|drought|el nino|la nina|climate|storm|typhoon|'
        r'cyclone|blizzard|heat wave|cold snap|rainfall|weather',
        re.IGNORECASE),
    "Finance": re.compile(
        r's&p|s\&p|dow jones|nasdaq|stock|market cap|ipo|earnings|revenue|'
        r'profit|share price|bull|bear|correction|crash|rally|volatility|'
        r'vix|hedge fund|short.*squeeze|margin|dividend|buyback|merger|'
        r'acquisition|bankruptcy|sec\b|insider trading',
        re.IGNORECASE),
}


def fetch_json(url, retries=2):
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep((attempt + 1) * 1.5)
            else:
                return None


def fetch_leaderboard(category, time_period, limit=50, offset=0):
    url = f"{LEADERBOARD_URL}?category={category}&timePeriod={time_period}&orderBy=PNL&limit={limit}&offset={offset}"
    return fetch_json(url)


def fetch_closed_positions(wallet, max_pages=5):
    """Fetch closed positions sorted by TIMESTAMP DESC (not PNL!) to get unbiased win/loss data."""
    all_pos = []
    for page in range(max_pages):
        offset = page * 50
        url = f"{CLOSED_POS_URL}?user={wallet}&limit=50&offset={offset}&sortBy=TIMESTAMP&sortDirection=DESC"
        data = fetch_json(url)
        if not data or len(data) == 0:
            break
        all_pos.extend(data)
        time.sleep(RATE_LIMIT_DELAY)
        if len(data) < 50:
            break
    return all_pos


def fetch_open_positions(wallet):
    url = f"{OPEN_POS_URL}?user={wallet}&limit=50"
    return fetch_json(url)


def check_activity(wallet, hours=24):
    """Check if wallet has any activity in the last N hours. Returns (is_active, last_timestamp, trade_count)."""
    cutoff = int((datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp())
    url = f"{ACTIVITY_URL}?user={wallet}&limit=50&type=TRADE&start={cutoff}"
    data = fetch_json(url)
    if not data:
        return False, 0, 0
    count = len(data)
    last_ts = max((d.get("timestamp", 0) for d in data), default=0)
    return count > 0, last_ts, count


def categorize(title):
    cats = set()
    if not title:
        return cats
    for name, pattern in CATEGORIES.items():
        if pattern.search(title):
            cats.add(name)
    return cats


def analyze_closed(closed, open_pos):
    if not closed:
        return None

    wins = 0
    losses = 0
    total_invested = 0.0
    total_pnl = 0.0
    all_cats = set()
    pnl_list = []

    for pos in closed:
        pnl = float(pos.get("realizedPnl", 0) or 0)
        avg_price = float(pos.get("avgPrice", 0) or 0)
        total_bought = float(pos.get("totalBought", 0) or 0)
        invested = avg_price * total_bought

        # Determine win/loss from realizedPnl
        # But also check curPrice vs avgPrice as secondary signal
        cur_price = float(pos.get("curPrice", 0) or 0)

        if pnl > 0:
            wins += 1
        elif pnl < 0:
            losses += 1
        else:
            # Zero PNL — check if it was a losing position
            # (resolved to 0 meaning the outcome didn't happen)
            if cur_price == 0 and avg_price > 0:
                losses += 1
            else:
                wins += 1

        total_invested += abs(invested) if invested > 0 else abs(pnl)
        total_pnl += pnl
        pnl_list.append(pnl)

        title = pos.get("title", "") or pos.get("slug", "") or ""
        all_cats.update(categorize(title))

    if not all_cats:
        all_cats.add("Other")

    total = wins + losses
    win_rate = (wins / total * 100) if total > 0 else 0
    roi = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    if len(pnl_list) > 1:
        avg = sum(pnl_list) / len(pnl_list)
        var = sum((p - avg) ** 2 for p in pnl_list) / (len(pnl_list) - 1)
        std = math.sqrt(var)
        sharpe = avg / std if std > 0 else 0
    else:
        sharpe = 0

    max_dd = min(pnl_list) if pnl_list else 0
    consistency = min(100, max(0, win_rate * 0.6 + max(0, 40 - abs(max_dd / (total_pnl or 1)) * 20)))

    sparkline = []
    cum = 0
    step = max(1, len(pnl_list) // 8)
    for i in range(0, len(pnl_list), step):
        cum += pnl_list[i]
        sparkline.append(round(cum, 2))

    return {
        "winRate": round(win_rate, 1),
        "roi": round(roi, 1),
        "totalTrades": total,
        "wins": wins,
        "losses": losses,
        "categories": sorted(all_cats),
        "sharpe": round(sharpe, 2),
        "consistency": round(consistency, 0),
        "maxDrawdown": round(max_dd, 2),
        "sparkline": sparkline,
        "openPositions": len(open_pos) if open_pos else 0,
        "closedPositions": len(closed),
        "hasCrypto": "Crypto" in all_cats,
        "totalPnlFromPositions": round(total_pnl, 2),
        "totalInvested": round(total_invested, 2),
    }


def main():
    print("=" * 60)
    print("  POLYMARKET LEADERBOARD SCRAPER v3")
    print(f"  Category: {CATEGORY} | Period: {TIME_PERIOD} | Top: {TOP_N}")
    print(f"  Activity filter: {ACTIVITY_WINDOW_HOURS}h" if ACTIVITY_WINDOW_HOURS > 0 else "  Activity filter: OFF")
    print("=" * 60)
    print()

    # --- Fetch leaderboard ---
    print("▸ Fetching leaderboard...")
    all_wallets = []
    pages = math.ceil(TOP_N / 50)

    for page in range(pages):
        offset = page * 50
        limit = min(50, TOP_N - offset)
        print(f"  Page {page+1}/{pages} (offset={offset}, limit={limit})")
        data = fetch_leaderboard(CATEGORY, TIME_PERIOD, limit, offset)
        if data:
            all_wallets.extend(data)
        time.sleep(RATE_LIMIT_DELAY)

    seen = set()
    wallets = []
    for w in all_wallets:
        addr = w.get("proxyWallet", "")
        if addr and addr not in seen:
            seen.add(addr)
            wallets.append(w)

    print(f"  ✓ {len(wallets)} unique wallets\n")

    if not wallets:
        print("✗ No wallets found.")
        sys.exit(1)

    # --- Activity filter ---
    if ACTIVITY_WINDOW_HOURS > 0:
        print(f"▸ Checking activity (last {ACTIVITY_WINDOW_HOURS}h)...")
        active_wallets = []
        inactive = 0

        for i, w in enumerate(wallets):
            addr = w.get("proxyWallet", "")
            name = (w.get("userName", "") or addr[:12])[:20]
            sys.stdout.write(f"\r  [{i+1}/{len(wallets)}] Checking {name:<22}")
            sys.stdout.flush()

            is_active, last_ts, trade_count = check_activity(addr, ACTIVITY_WINDOW_HOURS)
            time.sleep(RATE_LIMIT_DELAY)

            if is_active:
                w["_lastTradeTs"] = last_ts
                w["_tradesInWindow"] = trade_count
                active_wallets.append(w)
            else:
                inactive += 1

        print(f"\n  ✓ {len(active_wallets)} active / {inactive} inactive (filtered out)\n")
        wallets = active_wallets

        if not wallets:
            print(f"✗ No wallets with activity in the last {ACTIVITY_WINDOW_HOURS}h.")
            print("  Try increasing ACTIVITY_WINDOW_HOURS in the config.")
            sys.exit(1)
    else:
        for w in wallets:
            w["_lastTradeTs"] = 0
            w["_tradesInWindow"] = 0

    # --- Enrich ---
    print(f"▸ Enriching {len(wallets)} wallets (up to 250 positions each)...")
    results = []
    enriched_count = 0

    for i, w in enumerate(wallets):
        addr = w.get("proxyWallet", "")
        name = (w.get("userName", "") or addr[:12])[:28]
        pct = (i + 1) / len(wallets) * 100

        sys.stdout.write(f"\r  [{i+1}/{len(wallets)}] {pct:5.1f}% — {name:<30}")
        sys.stdout.flush()

        closed = fetch_closed_positions(addr, max_pages=5)
        time.sleep(RATE_LIMIT_DELAY)

        open_pos = fetch_open_positions(addr)
        time.sleep(RATE_LIMIT_DELAY)

        analysis = analyze_closed(closed, open_pos)

        if analysis:
            enriched_count += 1
            # Attach activity data
            analysis["lastTradeTimestamp"] = w.get("_lastTradeTs", 0)
            analysis["tradesInWindow"] = w.get("_tradesInWindow", 0)
            if w.get("_lastTradeTs"):
                analysis["lastTradeAge"] = f"{round((time.time() - w['_lastTradeTs']) / 3600, 1)}h ago"
            else:
                analysis["lastTradeAge"] = "unknown"

        entry = {
            "rank": w.get("rank", i + 1),
            "proxyWallet": addr,
            "userName": w.get("userName", ""),
            "profileImage": w.get("profileImage", ""),
            "xUsername": w.get("xUsername", ""),
            "verifiedBadge": w.get("verifiedBadge", False),
            "pnl": float(w.get("pnl", 0) or 0),
            "vol": float(w.get("vol", 0) or 0),
            "enriched": analysis,
        }
        results.append(entry)

    print(f"\n  ✓ Enriched {enriched_count}/{len(results)} wallets\n")

    # --- Score & sort ---
    def score(r):
        e = r.get("enriched")
        if not e:
            return -999999
        # Activity bonus: more recent trades = higher score
        activity_bonus = min(10, e.get("tradesInWindow", 0) * 0.5)
        return (
            e.get("roi", 0) * 0.25 +
            e.get("winRate", 0) * 0.3 +
            e.get("sharpe", 0) * 20 +
            e.get("consistency", 0) * 0.1 +
            activity_bonus
        )

    results.sort(key=score, reverse=True)
    for i, r in enumerate(results):
        r["scoredRank"] = i + 1

    # --- Summary ---
    print("▸ Top 20 by copy-trading score:")
    print("-" * 110)
    print(f"  {'#':<4} {'Name':<22} {'PNL':>12} {'ROI':>8} {'Win%':>7} {'Sharpe':>7} {'W/L':>9} {'Trades':>7}  {'Active':>8}  Categories")
    print("-" * 110)

    for r in results[:20]:
        e = r.get("enriched") or {}
        cats = ", ".join(sorted(e.get("categories", [])))
        name = (r["userName"] or r["proxyWallet"][:14] + "...")[:20]
        wl = f"{e.get('wins', 0)}/{e.get('losses', 0)}"
        active = e.get("lastTradeAge", "—")
        print(
            f"  {r['scoredRank']:<4} {name:<22} "
            f"{'$'+str(round(r['pnl'])):>12} "
            f"{str(e.get('roi', '—'))+'%':>8} "
            f"{str(e.get('winRate', '—'))+'%':>7} "
            f"{e.get('sharpe', '—'):>7} "
            f"{wl:>9} "
            f"{e.get('totalTrades', '—'):>7}  "
            f"{active:>8}  "
            f"{cats}"
        )

    print("-" * 110)

    # Category distribution
    cat_counts = {}
    for r in results:
        for c in (r.get("enriched") or {}).get("categories", []):
            cat_counts[c] = cat_counts.get(c, 0) + 1
    print("\n  Category distribution:")
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        bar = "█" * min(40, count)
        print(f"    {cat:<14} {count:>3}  {bar}")

    # Win rate distribution
    wr_list = [r["enriched"]["winRate"] for r in results if r.get("enriched")]
    if wr_list:
        avg_wr = sum(wr_list) / len(wr_list)
        above_55 = sum(1 for w in wr_list if w >= 55)
        print(f"\n  Avg win rate: {avg_wr:.1f}% | ≥55%: {above_55}/{len(wr_list)} wallets")

    print()

    # --- Export ---
    output = {
        "metadata": {
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "category": CATEGORY,
            "time_period": TIME_PERIOD,
            "activity_filter_hours": ACTIVITY_WINDOW_HOURS,
            "total_wallets": len(results),
            "enriched_wallets": enriched_count,
            "leaderboard_pulled": TOP_N,
            "active_after_filter": len(results),
        },
        "wallets": results,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  ✓ Exported to {OUTPUT_FILE}")
    print(f"    Upload to the Polymarket Alpha dashboard\n")


if __name__ == "__main__":
    main()
