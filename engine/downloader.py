"""Download and cache adjusted close prices via yfinance."""

import os
import pickle
import pandas as pd
import yfinance as yf
from config import DATA_CACHE


def fetch_prices(tickers: list[str], start: str, end: str, use_cache: bool = True) -> pd.DataFrame:
    """
    Return a DataFrame of adjusted close prices (daily).
    Columns = tickers, Index = date.
    Uses a local pickle cache to avoid repeated downloads.
    """
    os.makedirs(os.path.dirname(DATA_CACHE), exist_ok=True)

    cache_key = _cache_key(tickers, start, end)
    if use_cache and os.path.exists(DATA_CACHE):
        with open(DATA_CACHE, "rb") as f:
            cache = pickle.load(f)
        if cache_key in cache:
            print(f"  [cache] Loaded {len(tickers)} tickers from cache")
            return cache[cache_key]

    print(f"  [download] Fetching {len(tickers)} tickers from {start} to {end}...")
    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)

    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw[["Close"]] if "Close" in raw.columns else raw

    prices = prices.dropna(how="all")

    _save_cache(cache_key, prices)
    print(f"  [download] Done — {prices.shape[0]} trading days, {prices.shape[1]} tickers")
    return prices


def _cache_key(tickers, start, end):
    return (tuple(sorted(tickers)), start, end)


def _save_cache(key, df):
    cache = {}
    if os.path.exists(DATA_CACHE):
        with open(DATA_CACHE, "rb") as f:
            try:
                cache = pickle.load(f)
            except Exception:
                cache = {}
    cache[key] = df
    with open(DATA_CACHE, "wb") as f:
        pickle.dump(cache, f)
