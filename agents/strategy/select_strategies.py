#!/usr/bin/env python3
"""
Strategy agent — lists and filters strategies by user constraints.

Usage:
  python select_strategies.py list [--json]
  python select_strategies.py filter --risk moderate --years 20 [--max-drawdown -0.40] [--json]
  python select_strategies.py filter --profile data/user_profile.yaml [--json]
"""
import sys
import json
import argparse
from pathlib import Path

from strategy_catalog import load_all_strategies


def filter_strategies(
    strategies: list,
    risk_tolerance: str = None,
    years_to_retirement: int = None,
    max_drawdown_tolerance: float = None,
    excluded_tickers: list = None,
) -> list:
    excluded = set(excluded_tickers or [])
    filtered = []
    for s in strategies:
        sf = s.get("suitable_for", {})
        if not sf:
            filtered.append(s)
            continue

        if years_to_retirement is not None:
            if years_to_retirement < sf.get("min_horizon_years", 0):
                continue

        if risk_tolerance is not None:
            allowed = sf.get("risk_tolerance", [])
            if allowed and risk_tolerance not in allowed:
                continue

        if max_drawdown_tolerance is not None:
            allowed_dd = sf.get("max_drawdown_tolerance", -1.0)
            # strategy's worst-case drawdown must be within user's tolerance
            # e.g. user tolerates -0.40; strategy may go -0.35 ✓ but not -0.70 ✗
            if allowed_dd < max_drawdown_tolerance:
                continue

        filtered.append(s)
    return filtered


def main():
    parser = argparse.ArgumentParser(description="Strategy selector")
    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="List all strategies")
    list_p.add_argument("--json", action="store_true")

    filt_p = sub.add_parser("filter", help="Filter by user constraints")
    filt_p.add_argument("--risk", choices=["conservative", "moderate", "aggressive"])
    filt_p.add_argument("--years", type=int, help="Years to retirement")
    filt_p.add_argument("--max-drawdown", type=float, help="e.g. -0.40")
    filt_p.add_argument("--profile", help="Path to user_profile.yaml (overrides other flags)")
    filt_p.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if args.command == "list":
        strategies = load_all_strategies()
        if args.json:
            print(json.dumps(strategies, indent=2))
        else:
            for s in strategies:
                sf = s["suitable_for"]
                note = f" — {sf.get('notes', '')}" if sf.get("notes") else ""
                risk = "/".join(sf.get("risk_tolerance", [])) if sf else "any"
                horizon = f"{sf.get('min_horizon_years','?')}yr+" if sf else "any"
                print(f"[{s['index']:2d}] {s['label']}")
                print(f"      risk={risk}  horizon≥{horizon}  maxDD≤{sf.get('max_drawdown_tolerance', '?') if sf else '?'}{note}")

    elif args.command == "filter":
        risk = args.risk
        years = args.years
        max_dd = args.max_drawdown
        excluded = []

        if args.profile:
            import yaml
            profile = yaml.safe_load(Path(args.profile).read_text())
            p = profile.get("personal", {})
            c = profile.get("constraints", {})
            risk = risk or p.get("risk_tolerance")
            years = years or p.get("years_to_retirement")
            max_dd = max_dd or c.get("max_drawdown_tolerance")
            excluded = c.get("excluded_tickers", [])

        all_strategies = load_all_strategies()
        filtered = filter_strategies(all_strategies, risk, years, max_dd, excluded)

        if args.json:
            print(json.dumps(filtered, indent=2))
        else:
            print(f"Matching strategies: {len(filtered)} / {len(all_strategies)}")
            for s in filtered:
                sf = s.get("suitable_for", {})
                print(f"  [{s['index']:2d}] {s['label']}")
                if sf.get("notes"):
                    print(f"         {sf['notes']}")


if __name__ == "__main__":
    main()
