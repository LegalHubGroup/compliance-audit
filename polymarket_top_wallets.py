#!/usr/bin/env python3
"""
Polymarket Most Profitable Wallet Finder

Queries the Polymarket Data API to identify the most profitable wallets
across multiple time windows (daily, weekly, monthly, all-time).

Usage:
    python polymarket_top_wallets.py [--window WINDOW] [--top N] [--json]

Options:
    --window   Time window: 1d, 7d, 30d, all (default: all)
    --top      Number of top wallets to display (default: 25)
    --json     Output raw JSON instead of formatted table

No API key required — the Polymarket Data API is fully public.
"""

import argparse
import json
import sys
import urllib.request
import urllib.error

DATA_API = "https://data-api.polymarket.com"
LEADERBOARD_ENDPOINT = f"{DATA_API}/leaderboard"
PROFILE_BASE = "https://polymarket.com/profile"

VALID_WINDOWS = ["1d", "7d", "30d", "all"]


def fetch_leaderboard(window="all"):
    """Fetch the profit leaderboard for a given time window."""
    url = f"{LEADERBOARD_ENDPOINT}?window={window}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP error {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason}", file=sys.stderr)
        sys.exit(1)

    return data


def format_usd(value):
    """Format a number as USD string."""
    if value is None:
        return "N/A"
    v = float(value)
    sign = "-" if v < 0 else ""
    return f"{sign}${abs(v):,.2f}"


def format_volume(value):
    """Format volume with K/M suffixes for readability."""
    if value is None:
        return "N/A"
    v = float(value)
    if v >= 1_000_000:
        return f"${v / 1_000_000:,.1f}M"
    if v >= 1_000:
        return f"${v / 1_000:,.1f}K"
    return f"${v:,.2f}"


def shorten_address(addr):
    """Shorten a 0x address to 0x1234...abcd format."""
    if not addr or len(addr) < 10:
        return addr or "N/A"
    return f"{addr[:6]}...{addr[-4:]}"


def print_table(traders, window, top_n):
    """Print a formatted leaderboard table to stdout."""
    # Sort by PnL descending
    sorted_traders = sorted(
        traders,
        key=lambda t: float(t.get("pnl", 0) or 0),
        reverse=True,
    )[:top_n]

    if not sorted_traders:
        print("No leaderboard data returned.")
        return

    window_labels = {
        "1d": "24 Hours",
        "7d": "7 Days",
        "30d": "30 Days",
        "all": "All Time",
    }
    header = f"Polymarket Top {len(sorted_traders)} Most Profitable Wallets ({window_labels.get(window, window)})"
    print(f"\n{'=' * 96}")
    print(f"  {header}")
    print(f"{'=' * 96}")
    print(
        f"{'Rank':<6} {'Username':<20} {'Proxy Wallet':<16} "
        f"{'Profit (PnL)':>16} {'Volume':>14} {'Verified':<8}"
    )
    print(f"{'-' * 96}")

    for i, t in enumerate(sorted_traders, start=1):
        username = t.get("userName") or "anonymous"
        wallet = shorten_address(t.get("proxyWallet", ""))
        pnl = format_usd(t.get("pnl"))
        vol = format_volume(t.get("vol"))
        verified = "Yes" if t.get("verifiedBadge") else ""

        print(
            f"{i:<6} {username:<20} {wallet:<16} "
            f"{pnl:>16} {vol:>14} {verified:<8}"
        )

    print(f"{'=' * 96}")

    # Highlight #1
    top = sorted_traders[0]
    top_name = top.get("userName") or "anonymous"
    top_wallet = top.get("proxyWallet", "N/A")
    top_pnl = format_usd(top.get("pnl"))
    top_vol = format_volume(top.get("vol"))
    profile_url = f"{PROFILE_BASE}/{top_wallet}" if top_wallet != "N/A" else "N/A"

    print(f"\n  Most Profitable Wallet")
    print(f"  ----------------------")
    print(f"  Username     : {top_name}")
    print(f"  Proxy Wallet : {top_wallet}")
    print(f"  Profit (PnL) : {top_pnl}")
    print(f"  Volume       : {top_vol}")
    print(f"  Profile      : {profile_url}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Find the most profitable wallets on Polymarket."
    )
    parser.add_argument(
        "--window",
        choices=VALID_WINDOWS,
        default="all",
        help="Time window for leaderboard (default: all)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=25,
        help="Number of top wallets to show (default: 25, max: 100)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output raw JSON sorted by PnL",
    )
    parser.add_argument(
        "--all-windows",
        action="store_true",
        help="Show leaderboards for all time windows",
    )
    args = parser.parse_args()
    top_n = min(max(args.top, 1), 100)

    if args.all_windows:
        for w in VALID_WINDOWS:
            traders = fetch_leaderboard(window=w)
            if args.output_json:
                sorted_traders = sorted(
                    traders,
                    key=lambda t: float(t.get("pnl", 0) or 0),
                    reverse=True,
                )[:top_n]
                print(json.dumps({"window": w, "traders": sorted_traders}, indent=2))
            else:
                print_table(traders, w, top_n)
    else:
        traders = fetch_leaderboard(window=args.window)
        if args.output_json:
            sorted_traders = sorted(
                traders,
                key=lambda t: float(t.get("pnl", 0) or 0),
                reverse=True,
            )[:top_n]
            print(json.dumps(sorted_traders, indent=2))
        else:
            print_table(traders, args.window, top_n)


if __name__ == "__main__":
    main()
