"""Backtest infrastructure — abstract base class, rebalance rules, and data functions.

Strategy implementations live in data/strategies/<name>/strategy.py.
This file contains no concrete strategy classes.
"""

from __future__ import annotations

import hashlib
import json
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_CACHE = PROJECT_ROOT / "data" / "prices.pkl"

START_DATE = "2016-01-01"
END_DATE = date.today().isoformat()
INITIAL_CAPITAL = 100_000
RISK_FREE_RATE = 0.045
TRADING_DAYS_PER_YEAR = 252
THRESHOLD_TIGHT = 0.05
THRESHOLD_LOOSE = 0.10
MIN_REBALANCE_INTERVAL_DAYS = 21
WINDOW_STABILITY_YEARS = (3, 5, 7)

ASSETS = [
    {"ticker": "QQQ",     "category": "Broad ETF"},
    {"ticker": "VOO",     "category": "Broad ETF"},
    {"ticker": "SPY",     "category": "Broad ETF"},
    {"ticker": "VTI",     "category": "Broad ETF"},
    {"ticker": "DIA",     "category": "Broad ETF"},
    {"ticker": "IWF",     "category": "Broad ETF"},
    {"ticker": "IWD",     "category": "Broad ETF"},
    {"ticker": "IVE",     "category": "Broad ETF"},
    {"ticker": "IJR",     "category": "Broad ETF"},
    {"ticker": "VXUS",    "category": "Broad ETF"},
    {"ticker": "EEM",     "category": "Broad ETF"},
    {"ticker": "IWM",     "category": "Broad ETF"},
    {"ticker": "VEA",     "category": "Broad ETF"},
    {"ticker": "VWO",     "category": "Broad ETF"},
    {"ticker": "IEMG",    "category": "Broad ETF"},
    {"ticker": "EFA",     "category": "Broad ETF"},
    {"ticker": "EWJ",     "category": "Broad ETF"},
    {"ticker": "EWG",     "category": "Broad ETF"},
    {"ticker": "EWU",     "category": "Broad ETF"},
    {"ticker": "INDA",    "category": "Broad ETF"},
    {"ticker": "SPMO",    "category": "Factor ETF"},
    {"ticker": "SCHG",    "category": "Factor ETF"},
    {"ticker": "VBR",     "category": "Factor ETF"},
    {"ticker": "VIG",     "category": "Factor ETF"},
    {"ticker": "SCHD",    "category": "Factor ETF"},
    {"ticker": "QUAL",    "category": "Factor ETF"},
    {"ticker": "MTUM",    "category": "Factor ETF"},
    {"ticker": "USMV",    "category": "Factor ETF"},
    {"ticker": "MDY",     "category": "Broad ETF"},
    {"ticker": "IJH",     "category": "Broad ETF"},
    {"ticker": "IWO",     "category": "Broad ETF"},
    {"ticker": "IWN",     "category": "Broad ETF"},
    {"ticker": "VGT",     "category": "Sector ETF"},
    {"ticker": "SOXX",    "category": "Sector ETF"},
    {"ticker": "XLE",     "category": "Sector ETF"},
    {"ticker": "XLB",     "category": "Sector ETF"},
    {"ticker": "XLI",     "category": "Sector ETF"},
    {"ticker": "XLP",     "category": "Sector ETF"},
    {"ticker": "XLV",     "category": "Sector ETF"},
    {"ticker": "XLF",     "category": "Sector ETF"},
    {"ticker": "XLK",     "category": "Sector ETF"},
    {"ticker": "XLU",     "category": "Sector ETF"},
    {"ticker": "XLY",     "category": "Sector ETF"},
    {"ticker": "XLRE",    "category": "Sector ETF"},
    {"ticker": "SMH",     "category": "Sector ETF"},
    {"ticker": "XBI",     "category": "Sector ETF"},
    {"ticker": "TQQQ",    "category": "Leveraged ETF"},
    {"ticker": "UPRO",    "category": "Leveraged ETF"},
    {"ticker": "TMF",     "category": "Leveraged ETF"},
    {"ticker": "GLD",     "category": "Alternative"},
    {"ticker": "IAU",     "category": "Alternative"},
    {"ticker": "SLV",     "category": "Alternative"},
    {"ticker": "VNQ",     "category": "Alternative"},
    {"ticker": "DBC",     "category": "Alternative"},
    {"ticker": "USO",     "category": "Alternative"},
    {"ticker": "BTC-USD", "category": "Alternative"},
    {"ticker": "BND",     "category": "Fixed Income"},
    {"ticker": "AGG",     "category": "Fixed Income"},
    {"ticker": "IEF",     "category": "Fixed Income"},
    {"ticker": "HYG",     "category": "Fixed Income"},
    {"ticker": "LQD",     "category": "Fixed Income"},
    {"ticker": "MUB",     "category": "Fixed Income"},
    {"ticker": "BSV",     "category": "Fixed Income"},
    {"ticker": "VCIT",    "category": "Fixed Income"},
    {"ticker": "EMB",     "category": "Fixed Income"},
    {"ticker": "BIL",     "category": "Fixed Income"},
    {"ticker": "TIP",     "category": "Fixed Income"},
    {"ticker": "TLT",     "category": "Fixed Income"},
    {"ticker": "SHY",     "category": "Fixed Income"},
    {"ticker": "SHV",     "category": "Fixed Income"},
    {"ticker": "UNG",     "category": "Alternative"},
    {"ticker": "AAPL",    "category": "Mega-Cap Stock"},
    {"ticker": "MSFT",    "category": "Mega-Cap Stock"},
    {"ticker": "NVDA",    "category": "Mega-Cap Stock"},
    {"ticker": "AMZN",    "category": "Mega-Cap Stock"},
    {"ticker": "GOOGL",   "category": "Mega-Cap Stock"},
    {"ticker": "META",    "category": "Mega-Cap Stock"},
    {"ticker": "TSLA",    "category": "Mega-Cap Stock"},
    {"ticker": "JPM",     "category": "Mega-Cap Stock"},
    {"ticker": "UNH",     "category": "Mega-Cap Stock"},
    {"ticker": "BRK-B",   "category": "Mega-Cap Stock"},
]
TICKERS = [asset["ticker"] for asset in ASSETS]


# ── Abstract base ─────────────────────────────────────────────────────────────

class Strategy(ABC):
    name = "BaseStrategy"
    min_rebalance_frequency = "annual"

    def __init__(self, tickers: list[str], **_kwargs):
        self.tickers = tickers

    @abstractmethod
    def get_weights(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
        ...

    def _available_prices(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
        return prices[prices.index <= as_of]


# ── Rebalance rules ───────────────────────────────────────────────────────────

@dataclass
class RebalanceRule:
    name: str
    description: str


class CalendarRebalance(RebalanceRule):
    FREQ_MAP = {"daily": "B", "monthly": "MS", "quarterly": "QS", "annual": "YS"}

    def __init__(self, frequency: str = "monthly"):
        self.frequency = frequency
        super().__init__(
            name=f"Calendar({frequency})",
            description=f"Rebalance on every {frequency} boundary.",
        )

    def rebalance_dates(self, start: str, end: str) -> pd.DatetimeIndex:
        return pd.date_range(start=start, end=end, freq=self.FREQ_MAP[self.frequency])


class ThresholdRebalance(RebalanceRule):
    def __init__(self, threshold: float = THRESHOLD_TIGHT,
                 min_interval_days: int = MIN_REBALANCE_INTERVAL_DAYS):
        self.threshold = threshold
        self.min_interval_days = min_interval_days
        super().__init__(
            name=f"Threshold({threshold:.0%})",
            description=f"Rebalance when any asset drifts >{threshold:.0%} from target.",
        )

    def needs_rebalance(self, current_weights: dict, target_weights: dict,
                        last_rebalance: pd.Timestamp, today: pd.Timestamp) -> bool:
        if (today - last_rebalance).days < self.min_interval_days:
            return False
        return any(abs(current_weights.get(t, 0.0) - w) > self.threshold
                   for t, w in target_weights.items())


class HybridRebalance(RebalanceRule):
    def __init__(self, frequency: str = "monthly", threshold: float = THRESHOLD_LOOSE):
        self.calendar = CalendarRebalance(frequency)
        self.threshold = threshold
        super().__init__(
            name=f"Hybrid({frequency}, {threshold:.0%})",
            description=f"Check {frequency}; rebalance only if drift >{threshold:.0%}.",
        )

    def rebalance_dates(self, start: str, end: str) -> pd.DatetimeIndex:
        return self.calendar.rebalance_dates(start, end)

    def needs_rebalance(self, current_weights: dict, target_weights: dict) -> bool:
        return any(abs(current_weights.get(t, 0.0) - w) > self.threshold
                   for t, w in target_weights.items())


RULES = {
    "daily":          CalendarRebalance("daily"),
    "monthly":        CalendarRebalance("monthly"),
    "quarterly":      CalendarRebalance("quarterly"),
    "annual":         CalendarRebalance("annual"),
    "hybrid_monthly": HybridRebalance("monthly", THRESHOLD_LOOSE),
}


# ── Data fetching ─────────────────────────────────────────────────────────────

def fetch_prices(tickers: list[str], start: str, end: str,
                 use_cache: bool = True) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    DATA_CACHE.parent.mkdir(parents=True, exist_ok=True)
    cache_key = _cache_key(tickers, start, end)
    cached_prices = None
    cached_raw = None
    if use_cache and DATA_CACHE.exists():
        with open(DATA_CACHE, "rb") as f:
            cache = pickle.load(f)
        if isinstance(cache, dict) and cache_key in cache:
            cached = cache[cache_key]
            if isinstance(cached, dict):
                cached_prices = _clean_prices(cached.get("adj_close", pd.DataFrame()))
                cached_raw = _clean_prices(cached.get("raw_close", pd.DataFrame()))
                if not cached_prices.empty and not cached_raw.empty:
                    print(f"  [cache] Loaded {len(tickers)} tickers from cache")
                    return cached_prices, cached_raw
            else:
                cached_prices = _clean_prices(cached)
                if not cached_prices.empty:
                    print(f"  [cache] Loaded {len(tickers)} tickers from cache")
    print(f"  [download] Fetching {len(tickers)} tickers from {start} to {end}...")
    raw = yf.download(tickers, start=start, end=end, auto_adjust=False, progress=False)
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Adj Close"]
        raw_prices = raw["Close"]
    else:
        prices = raw["Adj Close"] if "Adj Close" in raw.columns else raw["Close"]
        raw_prices = raw["Close"]
        if isinstance(prices, pd.Series):
            prices = prices.to_frame(tickers[0])
        if isinstance(raw_prices, pd.Series):
            raw_prices = raw_prices.to_frame(tickers[0])
    prices = _clean_prices(cached_prices if cached_prices is not None else prices)
    raw_prices = _clean_prices(raw_prices)
    if not prices.empty:
        _save_cache(cache_key, {"adj_close": prices, "raw_close": raw_prices})
    print(f"  [download] Done - {prices.shape[0]} trading days, {prices.shape[1]} tickers")
    return prices, (raw_prices if not raw_prices.empty else None)


# ── Backtest engine ───────────────────────────────────────────────────────────

def run_backtest(strategy: Strategy, rebalance_rule: RebalanceRule,
                 prices: pd.DataFrame, raw_prices: pd.DataFrame | None,
                 start: str, end: str,
                 initial_capital: float = INITIAL_CAPITAL) -> dict:
    prices = prices[start:end].copy()
    if raw_prices is not None:
        raw_prices = raw_prices[start:end].copy()
    if prices.empty:
        raise ValueError(f"No price data in range {start}–{end}")
    if raw_prices is not None and raw_prices.empty:
        raw_prices = None

    rebalance_dates = _get_rebalance_dates(rebalance_rule, start, end, prices.index)
    equity = pd.Series(index=prices.index, dtype=float)
    holdings: dict[str, float] = {}
    cash = initial_capital
    current_weights: dict[str, float] = {}
    last_rebalance = prices.index[0] - pd.Timedelta(days=999)
    rebalance_count = 0
    rebalance_log: list[dict] = []

    for date_value in prices.index:
        row = prices.loc[date_value]
        raw_row = raw_prices.loc[date_value] if raw_prices is not None and date_value in raw_prices.index else row
        portfolio_value = cash + sum(
            holdings.get(t, 0) * row.get(t, np.nan)
            for t in holdings
            if not pd.isna(row.get(t, np.nan))
        )
        equity[date_value] = portfolio_value

        if _should_rebalance(rebalance_rule, rebalance_dates, date_value, last_rebalance) or not holdings:
            target = strategy.get_weights(prices, date_value)
            if not target:
                continue
            if isinstance(rebalance_rule, ThresholdRebalance):
                if not rebalance_rule.needs_rebalance(current_weights, target, last_rebalance, date_value):
                    continue
            elif isinstance(rebalance_rule, HybridRebalance):
                if date_value != prices.index[0] and not rebalance_rule.needs_rebalance(current_weights, target):
                    continue

            valid = {t: w for t, w in target.items()
                     if not pd.isna(row.get(t, np.nan)) and row.get(t, np.nan) > 0}
            total_w = sum(valid.values())
            if total_w <= 0:
                continue
            valid = {t: w / total_w for t, w in valid.items()}

            for t, shares in holdings.items():
                price = row.get(t, np.nan)
                if not pd.isna(price) and shares > 0:
                    cash += shares * price
            holdings = {}
            for t, w in valid.items():
                alloc = portfolio_value * w
                holdings[t] = alloc / row[t]
                cash -= alloc

            current_weights = valid.copy()
            last_rebalance = date_value
            rebalance_count += 1
            rebalance_holdings = []
            for t, w in valid.items():
                price = float(row[t])
                raw_close_val = raw_row.get(t, np.nan)
                raw_close = float(raw_close_val) if not pd.isna(raw_close_val) else price
                shares = float(holdings[t])
                rebalance_holdings.append({
                    "ticker": t,
                    "weight": round(float(w), 4),
                    "price": round(price, 4),
                    "raw_close": round(raw_close, 4),
                    "price_type": "adjusted_close",
                    "shares": round(shares, 6),
                    "share_type": "synthetic",
                    "market_value": round(price * shares, 2),
                })
            rebalance_log.append({
                "date": date_value.strftime("%Y-%m-%d"),
                "portfolio_value": round(float(portfolio_value), 2),
                "weights": {t: round(w, 4) for t, w in valid.items()},
                "holdings": rebalance_holdings,
            })

    equity = equity.dropna()
    metrics = compute_metrics(equity)
    metrics["rebalance_count"] = rebalance_count
    benchmarks = [
        benchmark for benchmark in (
            _build_buy_and_hold_benchmark(prices, raw_prices, ticker, start, end, initial_capital)
            for ticker in ("QQQ", "SPY", "VOO")
        )
        if benchmark is not None
    ]
    return {
        "strategy": strategy.name,
        "rebalance_rule": rebalance_rule.name,
        "label": f"{strategy.name} | {rebalance_rule.name}",
        "backtest_window": {"start": start, "end": end},
        "equity": equity,
        "metrics": metrics,
        "rebalance_log": rebalance_log,
        "benchmarks": benchmarks,
    }


def compute_metrics(equity: pd.Series) -> dict:
    returns = equity.pct_change().dropna()
    total_return = (equity.iloc[-1] / equity.iloc[0]) - 1
    n_years = len(equity) / TRADING_DAYS_PER_YEAR
    cagr = (1 + total_return) ** (1 / n_years) - 1 if n_years > 0 else 0
    volatility = returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    rf_daily = (1 + RISK_FREE_RATE) ** (1 / TRADING_DAYS_PER_YEAR) - 1
    excess = returns - rf_daily
    sharpe = (excess.mean() / returns.std()) * np.sqrt(TRADING_DAYS_PER_YEAR) if returns.std() > 0 else 0
    downside = returns[returns < rf_daily]
    sortino_denom = downside.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    sortino = (returns.mean() - rf_daily) * TRADING_DAYS_PER_YEAR / sortino_denom if sortino_denom > 0 else 0
    max_drawdown = _max_drawdown(equity)
    annual_returns = _annual_returns(equity)
    return {
        "cagr": cagr,
        "total_return": total_return,
        "volatility": volatility,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": max_drawdown,
        "calmar": cagr / abs(max_drawdown) if max_drawdown != 0 else 0,
        "recovery_months": _recovery_months(equity),
        "best_year": max(annual_returns.values()) if annual_returns else None,
        "worst_year": min(annual_returns.values()) if annual_returns else None,
        "annual_returns": annual_returns,
        **_stress_returns(equity),
    }


def save_result(result: dict, results_dir: str = "data/results") -> Path:
    label = result["label"]
    out_dir = PROJECT_ROOT / results_dir if not Path(results_dir).is_absolute() else Path(results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    equity: pd.Series = result["equity"]
    metrics = dict(result["metrics"])
    if "annual_returns" in metrics:
        metrics["annual_returns"] = {str(k): v for k, v in metrics["annual_returns"].items()}
    payload = {
        "label": label,
        "strategy": result["strategy"],
        "rebalance_rule": result["rebalance_rule"],
        "backtest_window": result.get("backtest_window", {}),
        "metrics": metrics,
        "equity_dates": [d.isoformat() for d in equity.index],
        "equity_values": [round(float(v), 2) for v in equity.values],
        "rebalance_log": result.get("rebalance_log", []),
        "benchmarks": result.get("benchmarks", []),
        "window_stability": result.get("window_stability", []),
    }
    out_path = out_dir / f"{hashlib.md5(label.encode()).hexdigest()[:8]}.json"
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)
    return out_path


# ── Private helpers ───────────────────────────────────────────────────────────

def _cache_key(tickers: list[str], start: str, end: str):
    return (tuple(sorted(tickers)), start, end)


def _clean_prices(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.sort_index().dropna(how="all").ffill().dropna(how="all")


def _save_cache(key, prices):
    cache = {}
    if DATA_CACHE.exists():
        with open(DATA_CACHE, "rb") as f:
            try:
                existing = pickle.load(f)
                cache = existing if isinstance(existing, dict) else {}
            except Exception:
                cache = {}
    cache[key] = prices
    with open(DATA_CACHE, "wb") as f:
        pickle.dump(cache, f)


def _get_rebalance_dates(rule, start: str, end: str, index: pd.DatetimeIndex) -> set:
    if isinstance(rule, (CalendarRebalance, HybridRebalance)):
        calendar_dates = rule.rebalance_dates(start, end)
        return set(index[index.searchsorted(calendar_dates, side="left").clip(0, len(index) - 1)])
    return set()


def _should_rebalance(rule, rebalance_dates, date_value, _last_rebalance) -> bool:
    if isinstance(rule, ThresholdRebalance):
        return True
    return date_value in rebalance_dates


def _max_drawdown(equity: pd.Series) -> float:
    rolling_max = equity.cummax()
    return ((equity - rolling_max) / rolling_max).min()


def _recovery_months(equity: pd.Series) -> int | None:
    rolling_max = equity.cummax()
    drawdown = (equity - rolling_max) / rolling_max
    trough_idx = drawdown.idxmin()
    recovered = equity[trough_idx:][equity[trough_idx:] >= rolling_max[trough_idx]]
    if recovered.empty:
        return None
    return int((recovered.index[0] - trough_idx).days / 30)


def _annual_returns(equity: pd.Series) -> dict:
    yearly = equity.resample("YE").last()
    return {
        yearly.index[i].year: (yearly.iloc[i] / yearly.iloc[i - 1]) - 1
        for i in range(1, len(yearly))
    }


def _stress_returns(equity: pd.Series) -> dict:
    result = {}
    y2022 = equity["2022-01-01":"2022-12-31"]
    if len(y2022) > 5:
        result["return_2022"] = (y2022.iloc[-1] / y2022.iloc[0]) - 1
    covid = equity["2020-02-19":"2020-03-23"]
    if len(covid) > 3:
        result["covid_crash"] = (covid.iloc[-1] / covid.iloc[0]) - 1
    q4_2018 = equity["2018-10-01":"2018-12-31"]
    if len(q4_2018) > 3:
        result["return_2018q4"] = (q4_2018.iloc[-1] / q4_2018.iloc[0]) - 1
    return result


def _build_buy_and_hold_benchmark(
    prices: pd.DataFrame,
    raw_prices: pd.DataFrame | None,
    ticker: str,
    start: str,
    end: str,
    initial_capital: float,
) -> dict | None:
    adj_series = None
    raw_series = None

    if ticker in prices.columns:
        adj_series = prices[ticker].dropna()
    if raw_prices is not None and ticker in raw_prices.columns:
        raw_series = raw_prices[ticker].dropna()

    if adj_series is None or adj_series.empty:
        fresh = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
        if isinstance(fresh.columns, pd.MultiIndex):
            adj_series = fresh["Close"][ticker].dropna() if "Close" in fresh.columns.get_level_values(0) else pd.Series(dtype=float)
        else:
            adj_series = fresh["Close"].dropna() if "Close" in fresh.columns else pd.Series(dtype=float)

    if raw_series is None or raw_series.empty:
        fresh_raw = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False)
        if isinstance(fresh_raw.columns, pd.MultiIndex):
            raw_series = fresh_raw["Close"][ticker].dropna() if "Close" in fresh_raw.columns.get_level_values(0) else pd.Series(dtype=float)
        else:
            raw_series = fresh_raw["Close"].dropna() if "Close" in fresh_raw.columns else pd.Series(dtype=float)

    series = adj_series if adj_series is not None and not adj_series.empty else raw_series
    if series is None or series.empty:
        return None

    start_price = float(series.iloc[0])
    if start_price <= 0:
        return None
    values = initial_capital * (series / start_price)
    return {
        "label": f"{ticker} buy & hold",
        "ticker": ticker,
        "price_type": "adjusted_close" if adj_series is not None and not adj_series.empty else "raw_close",
        "share_type": "synthetic",
        "start_price": round(start_price, 4),
        "dates": [d.isoformat() for d in series.index],
        "values": [round(float(v), 2) for v in values.values],
    }


def build_window_stability(strategy: Strategy, rebalance_rule: RebalanceRule,
                           prices: pd.DataFrame, raw_prices: pd.DataFrame | None,
                           start: str, end: str,
                           initial_capital: float = INITIAL_CAPITAL,
                           base_result: dict | None = None) -> list[dict]:
    stability: list[dict] = []
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)

    for years in WINDOW_STABILITY_YEARS:
        window_start_ts = max(start_ts, end_ts - pd.DateOffset(years=years))
        window_start = window_start_ts.date().isoformat()
        if window_start >= end:
            continue
        window_result = run_backtest(strategy, rebalance_rule, prices, raw_prices,
                                     window_start, end, initial_capital)
        stability.append(_summarize_window_result(
            label=f"{years}Y",
            start=window_start,
            end=end,
            result=window_result,
        ))

    stability.append(_summarize_window_result(
        label="Full",
        start=start,
        end=end,
        result=base_result or run_backtest(strategy, rebalance_rule, prices, raw_prices, start, end, initial_capital),
    ))
    return stability


def _summarize_window_result(label: str, start: str, end: str, result: dict) -> dict:
    metrics = result.get("metrics", {})
    keys = ("cagr", "sharpe", "sortino", "max_drawdown", "calmar", "volatility", "total_return",
            "recovery_months", "best_year", "worst_year")
    return {
        "window": label,
        "start": start,
        "end": end,
        "days": len(result.get("equity", [])),
        "metrics": {k: metrics.get(k) for k in keys},
    }
