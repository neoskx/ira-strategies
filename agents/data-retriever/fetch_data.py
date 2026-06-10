#!/usr/bin/env python3
"""
Data retriever agent — manages the yfinance price cache.

Usage:
  python fetch_data.py check               # check cache status
  python fetch_data.py refresh             # force fresh download
  python fetch_data.py check --json        # machine-readable status
"""
import sys
import json
import argparse
import pickle
from pathlib import Path
from datetime import date, timedelta

import yfinance as yf
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CACHE = PROJECT_ROOT / "data" / "prices.pkl"
START_DATE = "2016-01-01"
END_DATE = date.today().isoformat()
TICKERS = [
    "QQQ", "VOO", "SPY", "VTI", "VXUS", "EEM", "IWM",
    "SPMO", "SCHG", "VBR",
    "VGT", "SOXX", "XLE", "XLV", "XLF",
    "TQQQ", "UPRO", "TMF",
    "GLD", "VNQ", "DBC", "BTC-USD",
    "BND", "HYG", "TIP", "TLT", "SHY",
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL",
]


def load_config():
    return TICKERS, START_DATE, END_DATE


def check_cache(cache_path: Path, required_tickers: list, start: str, end: str) -> dict:
    if not cache_path.exists():
        return {"status": "miss", "reason": "cache file not found"}

    with open(cache_path, "rb") as f:
        cache = pickle.load(f)

    prices = _prices_from_cache(cache, required_tickers, start, end)
    if prices is None:
        return {"status": "miss", "reason": "cache key not found"}

    prices = _clean_prices(prices)
    if prices.empty:
        return {"status": "miss", "reason": "cached price data is empty"}

    cached = set(prices.columns.tolist())
    missing = sorted(set(required_tickers) - cached)
    cache_end = prices.index[-1].date()
    stale_cutoff = date.today() - timedelta(days=7)

    if missing:
        return {"status": "partial", "missing_tickers": missing, "cached": sorted(cached), "end": str(cache_end)}
    if cache_end < stale_cutoff:
        return {"status": "stale", "cache_end": str(cache_end), "cutoff": str(stale_cutoff)}

    return {
        "status": "hit",
        "tickers": sorted(cached),
        "start": str(prices.index[0].date()),
        "end": str(cache_end),
        "rows": len(prices),
    }


def refresh_cache(tickers: list, start: str, end: str, cache_path: Path) -> dict:
    print(f"Downloading {len(tickers)} tickers ({start} → {end})...", flush=True)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    prices = raw["Close"] if "Close" in raw.columns.get_level_values(0) else raw
    if isinstance(prices, pd.Series):
        prices = prices.to_frame(tickers[0])

    failed = [t for t in tickers if t not in prices.columns or prices[t].isna().all()]
    prices = _clean_prices(prices)

    cache = {}
    if cache_path.exists():
        with open(cache_path, "rb") as f:
            try:
                existing = pickle.load(f)
                cache = existing if isinstance(existing, dict) else {}
            except Exception:
                cache = {}
    cache[_cache_key(tickers, start, end)] = prices
    with open(cache_path, "wb") as f:
        pickle.dump(cache, f)

    return {
        "status": "refreshed",
        "downloaded": [t for t in tickers if t not in failed],
        "failed": failed,
        "start": str(prices.index[0].date()),
        "end": str(prices.index[-1].date()),
        "rows": len(prices),
        "cache_path": str(cache_path),
    }


def _cache_key(tickers: list, start: str, end: str):
    return (tuple(sorted(tickers)), start, end)


def _prices_from_cache(cache, tickers: list, start: str, end: str):
    if isinstance(cache, pd.DataFrame):
        return cache
    if not isinstance(cache, dict):
        return None
    return cache.get(_cache_key(tickers, start, end))


def _clean_prices(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.sort_index().dropna(how="all").ffill().dropna(how="all")


def main():
    parser = argparse.ArgumentParser(description="Price data cache manager")
    parser.add_argument("command", choices=["check", "refresh"])
    parser.add_argument("--cache", default=str(DEFAULT_CACHE))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    cache_path = Path(args.cache)
    tickers, start, end = load_config()

    if args.command == "check":
        result = check_cache(cache_path, tickers, start, end)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            s = result["status"]
            if s == "hit":
                print(f"Cache OK — {len(result['tickers'])} tickers, {result['start']} → {result['end']}")
            elif s == "miss":
                print(f"Cache MISSING: {result['reason']}")
            elif s == "partial":
                print(f"Cache PARTIAL — missing: {result['missing_tickers']}")
            elif s == "stale":
                print(f"Cache STALE — last updated {result['cache_end']}")

    elif args.command == "refresh":
        result = refresh_cache(tickers, start, end, cache_path)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Downloaded {len(result['downloaded'])} tickers → {result['cache_path']}")
            if result["failed"]:
                print(f"Failed tickers: {result['failed']}", file=sys.stderr)


if __name__ == "__main__":
    main()
