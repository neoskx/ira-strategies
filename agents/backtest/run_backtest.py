#!/usr/bin/env python3
"""
Backtest agent — runs a single strategy by index and saves the result.

Usage:
  python run_backtest.py --index 3 --total 17
  python run_backtest.py --index 3 --total 17 --results-dir data/results
  python run_backtest.py --index 3 --total 17 --json
"""
import sys
import json
import argparse

from backtest_core import (
    END_DATE,
    INITIAL_CAPITAL,
    START_DATE,
    TICKERS,
    build_strategies,
    fetch_prices,
    run_backtest,
    save_result,
)


def main():
    parser = argparse.ArgumentParser(description="Single strategy backtest runner")
    parser.add_argument("--index", type=int, required=True, help="0-based index in build_strategies()")
    parser.add_argument("--total", type=int, required=True, help="Total strategies being run (for display)")
    parser.add_argument("--results-dir", default="data/results")
    parser.add_argument("--json", action="store_true", help="Emit result summary as JSON on stdout")
    args = parser.parse_args()

    pairs = build_strategies(TICKERS)
    if args.index >= len(pairs):
        print(f"Error: --index {args.index} out of range (0–{len(pairs) - 1})", file=sys.stderr)
        sys.exit(1)

    strategy, rule = pairs[args.index]
    label = f"{strategy.name} | {rule.name}"
    print(f"[{args.index + 1}/{args.total}] {label}", flush=True)

    prices = fetch_prices(TICKERS, START_DATE, END_DATE, use_cache=True)
    result = run_backtest(strategy, rule, prices, START_DATE, END_DATE, INITIAL_CAPITAL)
    out_path = save_result(result, args.results_dir)

    m = result["metrics"]
    print(f"  CAGR={m['cagr']:.1%}  Sharpe={m['sharpe']:.2f}  "
          f"Sortino={m.get('sortino', 0):.2f}  MaxDD={m['max_drawdown']:.1%}")
    print(f"  Saved: {out_path}")

    if args.json:
        summary = {
            "index": args.index,
            "label": label,
            "cagr": round(m["cagr"], 4),
            "sharpe": round(m["sharpe"], 4),
            "sortino": round(m.get("sortino", 0), 4),
            "max_drawdown": round(m["max_drawdown"], 4),
            "result_path": str(out_path),
        }
        print(json.dumps(summary))


if __name__ == "__main__":
    main()
