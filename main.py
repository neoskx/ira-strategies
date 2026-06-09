"""
IRA Strategy Backtester — entry point.

Usage:
  python main.py              # full run, all strategies
  python main.py --quick      # fast run, subset of strategies, cached data
"""

import argparse
import sys
from config import START_DATE, END_DATE, INITIAL_CAPITAL
from universe.assets import TICKERS, get_tickers
from engine.downloader import fetch_prices
from engine.runner import run_backtest
from report.generator import generate_report
from rebalancing.rules import RULES

from strategies.static import FixedWeight, EqualWeight
from strategies.momentum import MomentumRotation, DualMomentum, TrendFollowing
from strategies.optimization import MaxSharpe, MinVariance, RiskParity, AdaptiveAssetAllocation


def build_strategies(tickers: list[str]) -> list[tuple]:
    """
    Returns list of (strategy, rebalance_rule) pairs.
    Edit this function to add/remove strategies.
    """
    # Convenience subsets
    risky = get_tickers(["Broad ETF", "Factor ETF", "Sector ETF"])
    safe = "BND"
    tbill = "SHY"
    leveraged = ["TQQQ", "TMF"]

    return [
        # ── Static ──────────────────────────────────────────────
        (FixedWeight(tickers, {"QQQ": 0.60, "SPMO": 0.40}),             RULES["annual"]),
        (FixedWeight(tickers, {"QQQ": 0.40, "SPMO": 0.25, "VTI": 0.25, "VXUS": 0.10}),
                                                                          RULES["annual"]),
        (FixedWeight(tickers, {"TQQQ": 0.55, "TMF": 0.45}),             RULES["monthly"]),
        (FixedWeight(tickers, {"QQQ": 1.0}),                             RULES["annual"]),
        (FixedWeight(tickers, {"VOO": 1.0}),                             RULES["annual"]),
        (FixedWeight(tickers, {"VTI": 0.60, "BND": 0.40}),              RULES["annual"]),
        (FixedWeight(tickers, {"VTI": 0.60, "VXUS": 0.30, "BND": 0.10}), RULES["annual"]),
        (EqualWeight(tickers),                                            RULES["monthly"]),

        # ── Momentum ─────────────────────────────────────────────
        (MomentumRotation(tickers, top_n=3),                             RULES["monthly"]),
        (MomentumRotation(tickers, top_n=5),                             RULES["monthly"]),
        (DualMomentum(tickers, risky_tickers=["QQQ", "VXUS"],
                      safe_ticker=safe, tbill_ticker=tbill),             RULES["monthly"]),
        (TrendFollowing(tickers, risky_tickers=risky,
                        safe_ticker=safe),                               RULES["monthly"]),

        # ── Optimization ─────────────────────────────────────────
        (MaxSharpe(tickers),                                             RULES["quarterly"]),
        (MinVariance(tickers),                                           RULES["quarterly"]),
        (RiskParity(tickers),                                            RULES["monthly"]),
        (AdaptiveAssetAllocation(tickers, top_n=3),                     RULES["monthly"]),
        (AdaptiveAssetAllocation(tickers, top_n=5),                     RULES["monthly"]),
    ]


def main():
    parser = argparse.ArgumentParser(description="IRA Strategy Backtester")
    parser.add_argument("--quick", action="store_true", help="Run subset of strategies, use cache")
    parser.add_argument("--start", default=START_DATE, help="Backtest start date")
    parser.add_argument("--end", default=END_DATE, help="Backtest end date")
    parser.add_argument("--no-cache", action="store_true", help="Force fresh data download")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  IRA Strategy Backtester")
    print(f"  Period : {args.start} → {args.end}")
    print(f"  Capital: ${INITIAL_CAPITAL:,.0f}")
    print(f"{'='*60}\n")

    # Download price data
    print("[1/3] Downloading price data...")
    prices = fetch_prices(TICKERS, args.start, args.end, use_cache=not args.no_cache)

    # Build and run strategies
    print("\n[2/3] Running backtests...")
    strategy_pairs = build_strategies(TICKERS)

    if args.quick:
        strategy_pairs = strategy_pairs[:5]
        print(f"  [quick mode] Running {len(strategy_pairs)} strategies")

    results = []
    for i, (strategy, rule) in enumerate(strategy_pairs):
        label = f"{strategy.name} | {rule.name}"
        print(f"  [{i+1}/{len(strategy_pairs)}] {label[:70]}...")
        try:
            result = run_backtest(strategy, rule, prices, args.start, args.end, INITIAL_CAPITAL)
            results.append(result)
            m = result["metrics"]
            print(f"         CAGR={m['cagr']:.1%}  Sharpe={m['sharpe']:.2f}  MaxDD={m['max_drawdown']:.1%}")
        except Exception as e:
            print(f"         ERROR: {e}", file=sys.stderr)

    if not results:
        print("No results — check your asset universe and date range.", file=sys.stderr)
        sys.exit(1)

    # Generate report
    print(f"\n[3/3] Generating report...")
    generate_report(results)

    # Print summary to terminal
    print(f"\n{'='*60}")
    print(f"  RESULTS (ranked by Sharpe ratio)")
    print(f"{'='*60}")
    ranked = sorted(results, key=lambda r: r["metrics"]["sharpe"], reverse=True)
    for r in ranked:
        m = r["metrics"]
        final = r["equity"].iloc[-1]
        print(f"  {r['label'][:55]:<55} "
              f"CAGR={m['cagr']:>6.1%}  Sharpe={m['sharpe']:>5.2f}  "
              f"MaxDD={m['max_drawdown']:>6.1%}  ${final:>10,.0f}")

    print(f"\n  Report: docs/index.html")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
