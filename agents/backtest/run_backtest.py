#!/usr/bin/env python3
"""
Backtest agent — runs a single strategy by index and saves the result.

Strategies are discovered from data/strategies/<name>/strategy.py (sorted by folder name).
Each file must export METADATA, STRATEGY_CLASS, and RULE.
The runner injects Strategy, RULES, pd, np into every file's namespace.

Usage:
  python run_backtest.py --index 3 --total 19
  python run_backtest.py --index 3 --total 19 --results-dir data/results
  python run_backtest.py --index 3 --total 19 --json
"""
import sys
import json
import importlib.util
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from backtest_core import (
    END_DATE, INITIAL_CAPITAL, START_DATE, TICKERS,
    Strategy, RebalanceRule, RULES,
    fetch_prices, run_backtest, save_result,
)

PROJECT_ROOT   = Path(__file__).resolve().parent.parent.parent
STRATEGIES_DIR = PROJECT_ROOT / "data" / "strategies"

_INJECTED = {
    "Strategy": Strategy,
    "RULES": RULES,
    "pd": pd,
    "np": np,
}


def _load_strategies_dir(strategies_dir: Path) -> list[tuple]:
    """Discover strategy.py in each subdirectory of strategies_dir (sorted by folder name)."""
    if not strategies_dir.exists():
        return []
    pairs = []
    for subdir in sorted(d for d in strategies_dir.iterdir() if d.is_dir()):
        py_files = sorted(subdir.glob("*.py"))
        if not py_files:
            continue
        py_file = py_files[0]
        try:
            spec = importlib.util.spec_from_file_location(subdir.name, py_file)
            module = importlib.util.module_from_spec(spec)
            module.__dict__.update(_INJECTED)
            spec.loader.exec_module(module)
            if hasattr(module, "STRATEGY_CLASS") and hasattr(module, "RULE"):
                pairs.append((module.STRATEGY_CLASS, module.RULE))
        except Exception as exc:
            print(f"  [warn] Could not load {subdir.name}: {exc}", file=sys.stderr)
    return pairs


def all_strategy_pairs(tickers: list[str]) -> list[tuple]:
    """Return (strategy, rule) pairs from all strategy subdirectories."""
    pairs = []
    for factory, rule in _load_strategies_dir(STRATEGIES_DIR):
        strategy = factory(tickers) if callable(factory) else factory
        pairs.append((strategy, rule))
    return pairs


def main():
    parser = argparse.ArgumentParser(description="Single strategy backtest runner")
    parser.add_argument("--index", type=int, required=True)
    parser.add_argument("--total", type=int, required=True)
    parser.add_argument("--results-dir", default="data/results")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    pairs = all_strategy_pairs(TICKERS)
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
        print(json.dumps({
            "index": args.index,
            "label": label,
            "cagr": round(m["cagr"], 4),
            "sharpe": round(m["sharpe"], 4),
            "sortino": round(m.get("sortino", 0), 4),
            "max_drawdown": round(m["max_drawdown"], 4),
            "result_path": str(out_path),
        }))


if __name__ == "__main__":
    main()
