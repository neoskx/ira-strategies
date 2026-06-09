"""Self-contained backtesting core for the backtest agent."""

from __future__ import annotations

import hashlib
import json
import os
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

try:
    from pypfopt import EfficientFrontier, expected_returns, risk_models
    PYPFOPT_AVAILABLE = True
except ImportError:
    PYPFOPT_AVAILABLE = False


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
MOMENTUM_LOOKBACK_MONTHS = 12
MOMENTUM_SKIP_MONTHS = 1
MOMENTUM_TOP_N = 3
TREND_MA_DAYS = 200

ASSETS = [
    {"ticker": "QQQ", "category": "Broad ETF"},
    {"ticker": "VOO", "category": "Broad ETF"},
    {"ticker": "VTI", "category": "Broad ETF"},
    {"ticker": "VXUS", "category": "Broad ETF"},
    {"ticker": "SPMO", "category": "Factor ETF"},
    {"ticker": "SCHG", "category": "Factor ETF"},
    {"ticker": "VBR", "category": "Factor ETF"},
    {"ticker": "VGT", "category": "Sector ETF"},
    {"ticker": "SOXX", "category": "Sector ETF"},
    {"ticker": "TQQQ", "category": "Leveraged ETF"},
    {"ticker": "UPRO", "category": "Leveraged ETF"},
    {"ticker": "TMF", "category": "Leveraged ETF"},
    {"ticker": "GLD", "category": "Alternative"},
    {"ticker": "VNQ", "category": "Alternative"},
    {"ticker": "BTC-USD", "category": "Alternative"},
    {"ticker": "BND", "category": "Fixed Income"},
    {"ticker": "TLT", "category": "Fixed Income"},
    {"ticker": "SHY", "category": "Fixed Income"},
    {"ticker": "AAPL", "category": "Mega-Cap Stock"},
    {"ticker": "MSFT", "category": "Mega-Cap Stock"},
    {"ticker": "NVDA", "category": "Mega-Cap Stock"},
    {"ticker": "AMZN", "category": "Mega-Cap Stock"},
    {"ticker": "GOOGL", "category": "Mega-Cap Stock"},
]
TICKERS = [asset["ticker"] for asset in ASSETS]


def get_tickers(categories: list[str] | None = None) -> list[str]:
    if categories is None:
        return TICKERS
    return [asset["ticker"] for asset in ASSETS if asset["category"] in categories]


class Strategy(ABC):
    name = "BaseStrategy"
    description = ""
    min_rebalance_frequency = "annual"
    suitable_for: dict = {}

    def __init__(self, tickers: list[str], **_kwargs):
        self.tickers = tickers

    @abstractmethod
    def get_weights(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
        ...

    def _available_prices(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
        return prices[prices.index <= as_of]


class FixedWeight(Strategy):
    min_rebalance_frequency = "annual"

    def __init__(self, tickers: list[str], weights: dict[str, float], **kwargs):
        super().__init__(tickers, **kwargs)
        total = sum(weights.values())
        self.weights = {ticker: weight / total for ticker, weight in weights.items()}
        self.name = "FixedWeight(" + ", ".join(
            f"{ticker}:{weight:.0%}" for ticker, weight in self.weights.items()
        ) + ")"
        self.description = "Fixed target weights, rebalance back to target on schedule."
        self.suitable_for = fixed_weight_suitability(self.weights)

    def get_weights(self, _prices: pd.DataFrame, _as_of: pd.Timestamp) -> dict[str, float]:
        return self.weights.copy()


class EqualWeight(Strategy):
    min_rebalance_frequency = "monthly"
    suitable_for = {
        "min_horizon_years": 10,
        "risk_tolerance": ["moderate", "aggressive"],
        "asset_types": ["ETF"],
        "max_drawdown_tolerance": -0.45,
        "notes": "1/N diversification across all assets. No market view required.",
    }

    def __init__(self, tickers: list[str], **kwargs):
        super().__init__(tickers, **kwargs)
        self.name = f"EqualWeight({len(tickers)} assets)"
        self.description = "1/N allocation across all assets. Monthly rebalance."

    def get_weights(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
        available = self._available_prices(prices, as_of)
        valid = [ticker for ticker in self.tickers if ticker in available.columns and available[ticker].notna().any()]
        weight = 1.0 / len(valid) if valid else 0.0
        return {ticker: weight for ticker in valid}


class MomentumRotation(Strategy):
    min_rebalance_frequency = "monthly"
    suitable_for = {
        "min_horizon_years": 10,
        "risk_tolerance": ["moderate", "aggressive"],
        "asset_types": ["ETF"],
        "max_drawdown_tolerance": -0.55,
        "notes": "Signal-driven rotation. Can underperform in choppy sideways markets.",
    }

    def __init__(self, tickers: list[str], top_n: int = MOMENTUM_TOP_N,
                 lookback_months: int = MOMENTUM_LOOKBACK_MONTHS,
                 skip_months: int = MOMENTUM_SKIP_MONTHS, **kwargs):
        super().__init__(tickers, **kwargs)
        self.top_n = top_n
        self.lookback_months = lookback_months
        self.skip_months = skip_months
        self.name = f"MomentumRotation(top{top_n}, {lookback_months}m)"

    def get_weights(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
        hist = self._available_prices(prices, as_of)
        end = as_of - pd.DateOffset(months=self.skip_months)
        start = end - pd.DateOffset(months=self.lookback_months)
        scores = {}
        for ticker in self.tickers:
            if ticker not in hist.columns:
                continue
            window = hist[ticker].loc[start:end].dropna()
            if len(window) >= 20:
                scores[ticker] = (window.iloc[-1] / window.iloc[0]) - 1
        if not scores:
            return {}
        top = sorted(scores, key=scores.get, reverse=True)[: self.top_n]
        return {ticker: 1.0 / len(top) for ticker in top}


class DualMomentum(Strategy):
    min_rebalance_frequency = "monthly"
    suitable_for = {
        "min_horizon_years": 10,
        "risk_tolerance": ["moderate", "aggressive"],
        "asset_types": ["ETF"],
        "max_drawdown_tolerance": -0.40,
        "notes": "Defensive: switches to bonds in downtrends. Lower drawdown than pure equity.",
    }

    def __init__(self, tickers: list[str], risky_tickers: list[str] | None = None,
                 safe_ticker: str = "BND", tbill_ticker: str = "SHY",
                 lookback_months: int = MOMENTUM_LOOKBACK_MONTHS,
                 skip_months: int = MOMENTUM_SKIP_MONTHS, **kwargs):
        super().__init__(tickers, **kwargs)
        self.risky = risky_tickers or [ticker for ticker in tickers if ticker not in (safe_ticker, tbill_ticker)]
        self.safe = safe_ticker
        self.tbill = tbill_ticker
        self.lookback_months = lookback_months
        self.skip_months = skip_months
        self.name = f"DualMomentum({lookback_months}m)"

    def get_weights(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
        hist = self._available_prices(prices, as_of)
        end = as_of - pd.DateOffset(months=self.skip_months)
        start = end - pd.DateOffset(months=self.lookback_months)
        scores = {}
        for ticker in self.risky:
            if ticker not in hist.columns:
                continue
            window = hist[ticker].loc[start:end].dropna()
            if len(window) >= 20:
                scores[ticker] = (window.iloc[-1] / window.iloc[0]) - 1
        if not scores:
            return {self.safe: 1.0} if self.safe in hist.columns else {}
        winner = max(scores, key=scores.get)
        tbill_return = 0.0
        if self.tbill in hist.columns:
            tbill = hist[self.tbill].loc[start:end].dropna()
            if len(tbill) >= 20:
                tbill_return = (tbill.iloc[-1] / tbill.iloc[0]) - 1
        if scores[winner] > tbill_return:
            return {winner: 1.0}
        return {self.safe: 1.0} if self.safe in hist.columns else {winner: 1.0}


class TrendFollowing(Strategy):
    min_rebalance_frequency = "monthly"
    suitable_for = {
        "min_horizon_years": 10,
        "risk_tolerance": ["moderate"],
        "asset_types": ["ETF"],
        "max_drawdown_tolerance": -0.35,
        "notes": "Moving average filter reduces crash exposure. May lag in fast recoveries.",
    }

    def __init__(self, tickers: list[str], risky_tickers: list[str] | None = None,
                 safe_ticker: str = "BND", ma_days: int = TREND_MA_DAYS, **kwargs):
        super().__init__(tickers, **kwargs)
        self.risky = risky_tickers or [ticker for ticker in tickers if ticker != safe_ticker]
        self.safe = safe_ticker
        self.ma_days = ma_days
        self.name = f"TrendFollowing({ma_days}d MA)"

    def get_weights(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
        hist = self._available_prices(prices, as_of)
        above_ma = []
        for ticker in self.risky:
            if ticker not in hist.columns:
                continue
            series = hist[ticker].dropna()
            if len(series) < self.ma_days:
                continue
            if series.iloc[-1] > series.rolling(self.ma_days).mean().iloc[-1]:
                above_ma.append(ticker)
        if above_ma:
            return {ticker: 1.0 / len(above_ma) for ticker in above_ma}
        return {self.safe: 1.0} if self.safe in hist.columns else {}


class MaxSharpe(Strategy):
    min_rebalance_frequency = "quarterly"
    suitable_for = {
        "min_horizon_years": 15,
        "risk_tolerance": ["moderate", "aggressive"],
        "asset_types": ["ETF"],
        "max_drawdown_tolerance": -0.50,
        "notes": "Model-dependent. Works best with 8+ uncorrelated assets in the universe.",
    }

    def __init__(self, tickers: list[str], lookback_months: int = 36, **kwargs):
        super().__init__(tickers, **kwargs)
        self.lookback_months = lookback_months
        self.name = f"MaxSharpe({lookback_months}m lookback)"

    def get_weights(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
        if not PYPFOPT_AVAILABLE:
            raise ImportError("PyPortfolioOpt not installed. Run: pip install PyPortfolioOpt")
        hist = self._available_prices(prices, as_of)
        window = hist.loc[as_of - pd.DateOffset(months=self.lookback_months):as_of, self.tickers].dropna(axis=1, how="any")
        if window.shape[1] < 2 or window.shape[0] < 60:
            return equal_weights(window.columns.tolist())
        try:
            mu = expected_returns.mean_historical_return(window, returns_data=False)
            cov = risk_models.CovarianceShrinkage(window).ledoit_wolf()
            frontier = EfficientFrontier(mu, cov)
            frontier.max_sharpe(risk_free_rate=RISK_FREE_RATE)
            return {ticker: weight for ticker, weight in frontier.clean_weights().items() if weight > 0.001}
        except Exception:
            return equal_weights(window.columns.tolist())


class MinVariance(Strategy):
    min_rebalance_frequency = "quarterly"
    suitable_for = {
        "min_horizon_years": 5,
        "risk_tolerance": ["conservative", "moderate"],
        "asset_types": ["ETF"],
        "max_drawdown_tolerance": -0.25,
        "notes": "Capital preservation first. Lower returns but very low drawdowns.",
    }

    def __init__(self, tickers: list[str], lookback_months: int = 36, **kwargs):
        super().__init__(tickers, **kwargs)
        self.lookback_months = lookback_months
        self.name = f"MinVariance({lookback_months}m lookback)"

    def get_weights(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
        if not PYPFOPT_AVAILABLE:
            raise ImportError("PyPortfolioOpt not installed.")
        hist = self._available_prices(prices, as_of)
        window = hist.loc[as_of - pd.DateOffset(months=self.lookback_months):as_of, self.tickers].dropna(axis=1, how="any")
        if window.shape[1] < 2 or window.shape[0] < 60:
            return equal_weights(window.columns.tolist())
        try:
            cov = risk_models.CovarianceShrinkage(window).ledoit_wolf()
            frontier = EfficientFrontier(None, cov)
            frontier.min_volatility()
            return {ticker: weight for ticker, weight in frontier.clean_weights().items() if weight > 0.001}
        except Exception:
            return equal_weights(window.columns.tolist())


class RiskParity(Strategy):
    min_rebalance_frequency = "monthly"
    suitable_for = {
        "min_horizon_years": 10,
        "risk_tolerance": ["conservative", "moderate"],
        "asset_types": ["ETF"],
        "max_drawdown_tolerance": -0.30,
        "notes": "Bridgewater All-Weather style. High Sharpe ratio, lower absolute returns.",
    }

    def __init__(self, tickers: list[str], lookback_months: int = 3, **kwargs):
        super().__init__(tickers, **kwargs)
        self.lookback_months = lookback_months
        self.name = f"RiskParity({lookback_months}m vol)"

    def get_weights(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
        hist = self._available_prices(prices, as_of)
        start = as_of - pd.DateOffset(months=self.lookback_months)
        inv_vols = {}
        for ticker in self.tickers:
            if ticker not in hist.columns:
                continue
            window = hist[ticker].loc[start:as_of].dropna()
            if len(window) < 10:
                continue
            vol = window.pct_change().dropna().std()
            if vol > 0:
                inv_vols[ticker] = 1.0 / vol
        total = sum(inv_vols.values())
        return {ticker: value / total for ticker, value in inv_vols.items()} if total else {}


class AdaptiveAssetAllocation(Strategy):
    min_rebalance_frequency = "monthly"
    suitable_for = {
        "min_horizon_years": 10,
        "risk_tolerance": ["moderate", "aggressive"],
        "asset_types": ["ETF"],
        "max_drawdown_tolerance": -0.45,
        "notes": "Combines momentum filter with risk parity sizing. Research-backed, high Sharpe.",
    }

    def __init__(self, tickers: list[str], top_n: int = MOMENTUM_TOP_N,
                 momentum_months: int = MOMENTUM_LOOKBACK_MONTHS, vol_months: int = 3, **kwargs):
        super().__init__(tickers, **kwargs)
        self.top_n = top_n
        self.momentum_months = momentum_months
        self.vol_months = vol_months
        self.name = f"AdaptiveAA(top{top_n}, {momentum_months}m mom, {vol_months}m vol)"

    def get_weights(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
        hist = self._available_prices(prices, as_of)
        scores = {}
        for ticker in self.tickers:
            if ticker not in hist.columns:
                continue
            window = hist[ticker].loc[as_of - pd.DateOffset(months=self.momentum_months):as_of].dropna()
            if len(window) >= 20:
                scores[ticker] = (window.iloc[-1] / window.iloc[0]) - 1
        selected = sorted(scores, key=scores.get, reverse=True)[: self.top_n]
        inv_vols = {}
        for ticker in selected:
            window = hist[ticker].loc[as_of - pd.DateOffset(months=self.vol_months):as_of].dropna()
            vol = window.pct_change().dropna().std() if len(window) >= 10 else 0
            inv_vols[ticker] = 1.0 / vol if vol > 0 else 1.0
        total = sum(inv_vols.values())
        return {ticker: value / total for ticker, value in inv_vols.items()} if total else {}


@dataclass
class RebalanceRule:
    name: str
    description: str


class CalendarRebalance(RebalanceRule):
    FREQ_MAP = {"monthly": "MS", "quarterly": "QS", "annual": "YS"}

    def __init__(self, frequency: str = "monthly"):
        self.frequency = frequency
        super().__init__(name=f"Calendar({frequency})", description=f"Rebalance on every {frequency} boundary.")

    def rebalance_dates(self, start: str, end: str) -> pd.DatetimeIndex:
        return pd.date_range(start=start, end=end, freq=self.FREQ_MAP[self.frequency])


class ThresholdRebalance(RebalanceRule):
    def __init__(self, threshold: float = THRESHOLD_TIGHT, min_interval_days: int = MIN_REBALANCE_INTERVAL_DAYS):
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
        return any(abs(current_weights.get(ticker, 0.0) - target) > self.threshold
                   for ticker, target in target_weights.items())


class HybridRebalance(RebalanceRule):
    def __init__(self, frequency: str = "monthly", threshold: float = THRESHOLD_LOOSE):
        self.calendar = CalendarRebalance(frequency)
        self.threshold = threshold
        super().__init__(
            name=f"Hybrid({frequency}, {threshold:.0%})",
            description=f"Check {frequency}; rebalance only if any asset drifts >{threshold:.0%}.",
        )

    def rebalance_dates(self, start: str, end: str) -> pd.DatetimeIndex:
        return self.calendar.rebalance_dates(start, end)

    def needs_rebalance(self, current_weights: dict, target_weights: dict) -> bool:
        return any(abs(current_weights.get(ticker, 0.0) - target) > self.threshold
                   for ticker, target in target_weights.items())


RULES = {
    "monthly": CalendarRebalance("monthly"),
    "quarterly": CalendarRebalance("quarterly"),
    "annual": CalendarRebalance("annual"),
    "hybrid_monthly": HybridRebalance("monthly", THRESHOLD_LOOSE),
}


def fixed_weight_suitability(weights: dict[str, float]) -> dict:
    leveraged = {"TQQQ", "TMF", "UPRO", "SSO", "SOXL", "SPXL"}
    equity = {"QQQ", "VOO", "VTI", "SPY", "SPMO", "VGT", "TQQQ", "UPRO", "VXUS", "VEA", "VWO"}
    has_leveraged = any(ticker in leveraged for ticker in weights)
    equity_weight = sum(weight for ticker, weight in weights.items() if ticker in equity)
    if has_leveraged:
        return {
            "min_horizon_years": 20, "risk_tolerance": ["aggressive"],
            "asset_types": ["ETF"], "max_drawdown_tolerance": -0.70,
            "notes": "Leveraged. Only suitable for investors with 20+ year horizon.",
        }
    if equity_weight >= 0.80:
        return {
            "min_horizon_years": 15, "risk_tolerance": ["aggressive"],
            "asset_types": ["ETF"], "max_drawdown_tolerance": -0.50,
            "notes": "Equity-heavy. High growth potential with significant drawdown risk.",
        }
    if equity_weight >= 0.50:
        return {
            "min_horizon_years": 10, "risk_tolerance": ["moderate", "aggressive"],
            "asset_types": ["ETF"], "max_drawdown_tolerance": -0.40,
            "notes": "Balanced equity/bond blend. Suitable for 10+ year horizon.",
        }
    return {
        "min_horizon_years": 5, "risk_tolerance": ["conservative", "moderate"],
        "asset_types": ["ETF"], "max_drawdown_tolerance": -0.25,
        "notes": "Conservative allocation. Prioritizes capital preservation.",
    }


def equal_weights(tickers: list[str]) -> dict[str, float]:
    weight = 1.0 / len(tickers) if tickers else 0.0
    return {ticker: weight for ticker in tickers}


def build_strategies(tickers: list[str]) -> list[tuple[Strategy, RebalanceRule]]:
    risky = get_tickers(["Broad ETF", "Factor ETF", "Sector ETF"])
    return [
        (FixedWeight(tickers, {"QQQ": 0.60, "SPMO": 0.40}), RULES["annual"]),
        (FixedWeight(tickers, {"QQQ": 0.40, "SPMO": 0.25, "VTI": 0.25, "VXUS": 0.10}), RULES["annual"]),
        (FixedWeight(tickers, {"TQQQ": 0.55, "TMF": 0.45}), RULES["monthly"]),
        (FixedWeight(tickers, {"QQQ": 1.0}), RULES["annual"]),
        (FixedWeight(tickers, {"VOO": 1.0}), RULES["annual"]),
        (FixedWeight(tickers, {"VTI": 0.60, "BND": 0.40}), RULES["annual"]),
        (FixedWeight(tickers, {"VTI": 0.60, "VXUS": 0.30, "BND": 0.10}), RULES["annual"]),
        (EqualWeight(tickers), RULES["monthly"]),
        (MomentumRotation(tickers, top_n=3), RULES["monthly"]),
        (MomentumRotation(tickers, top_n=5), RULES["monthly"]),
        (DualMomentum(tickers, risky_tickers=["QQQ", "VXUS"], safe_ticker="BND", tbill_ticker="SHY"), RULES["monthly"]),
        (TrendFollowing(tickers, risky_tickers=risky, safe_ticker="BND"), RULES["monthly"]),
        (MaxSharpe(tickers), RULES["quarterly"]),
        (MinVariance(tickers), RULES["quarterly"]),
        (RiskParity(tickers), RULES["monthly"]),
        (AdaptiveAssetAllocation(tickers, top_n=3), RULES["monthly"]),
        (AdaptiveAssetAllocation(tickers, top_n=5), RULES["monthly"]),
    ]


def fetch_prices(tickers: list[str], start: str, end: str, use_cache: bool = True) -> pd.DataFrame:
    DATA_CACHE.parent.mkdir(parents=True, exist_ok=True)
    cache_key = _cache_key(tickers, start, end)
    if use_cache and DATA_CACHE.exists():
        with open(DATA_CACHE, "rb") as f:
            cache = pickle.load(f)
        if isinstance(cache, dict) and cache_key in cache:
            prices = _clean_prices(cache[cache_key])
            if not prices.empty:
                print(f"  [cache] Loaded {len(tickers)} tickers from cache")
                return prices
    print(f"  [download] Fetching {len(tickers)} tickers from {start} to {end}...")
    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    prices = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
    prices = _clean_prices(prices)
    if not prices.empty:
        _save_cache(cache_key, prices)
    print(f"  [download] Done - {prices.shape[0]} trading days, {prices.shape[1]} tickers")
    return prices


def run_backtest(strategy: Strategy, rebalance_rule: RebalanceRule, prices: pd.DataFrame,
                 start: str, end: str, initial_capital: float = INITIAL_CAPITAL) -> dict:
    prices = prices[start:end].copy()
    if prices.empty:
        raise ValueError(f"No price data in range {start}-{end}")

    rebalance_dates = _get_rebalance_dates(rebalance_rule, start, end, prices.index)
    equity = pd.Series(index=prices.index, dtype=float)
    holdings: dict[str, float] = {}
    cash = initial_capital
    current_weights: dict[str, float] = {}
    last_rebalance = prices.index[0] - pd.Timedelta(days=999)
    rebalance_count = 0

    for date_value in prices.index:
        row = prices.loc[date_value]
        portfolio_value = cash + sum(
            holdings.get(ticker, 0) * row.get(ticker, np.nan)
            for ticker in holdings
            if not pd.isna(row.get(ticker, np.nan))
        )
        equity[date_value] = portfolio_value

        should_rebalance = _should_rebalance(
            rebalance_rule, rebalance_dates, date_value, current_weights, None, last_rebalance
        )
        if should_rebalance or not holdings:
            target = strategy.get_weights(prices, date_value)
            if not target:
                continue
            if isinstance(rebalance_rule, ThresholdRebalance):
                if not rebalance_rule.needs_rebalance(current_weights, target, last_rebalance, date_value):
                    continue
            elif isinstance(rebalance_rule, HybridRebalance):
                if date_value != prices.index[0] and not rebalance_rule.needs_rebalance(current_weights, target):
                    continue
            valid_target = {
                ticker: weight for ticker, weight in target.items()
                if not pd.isna(row.get(ticker, np.nan)) and row.get(ticker, np.nan) > 0
            }
            valid_weight = sum(valid_target.values())
            if valid_weight <= 0:
                continue
            valid_target = {ticker: weight / valid_weight for ticker, weight in valid_target.items()}

            for ticker, shares in holdings.items():
                price = row.get(ticker, np.nan)
                if not pd.isna(price) and shares > 0:
                    cash += shares * price
            holdings = {}
            for ticker, weight in valid_target.items():
                allocation = portfolio_value * weight
                holdings[ticker] = allocation / row[ticker]
                cash -= allocation
            current_weights = valid_target.copy()
            last_rebalance = date_value
            rebalance_count += 1

    equity = equity.dropna()
    metrics = compute_metrics(equity)
    metrics["rebalance_count"] = rebalance_count
    return {
        "strategy": strategy.name,
        "rebalance_rule": rebalance_rule.name,
        "label": f"{strategy.name} | {rebalance_rule.name}",
        "equity": equity,
        "metrics": metrics,
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
        metrics["annual_returns"] = {str(key): value for key, value in metrics["annual_returns"].items()}
    payload = {
        "label": label,
        "strategy": result["strategy"],
        "rebalance_rule": result["rebalance_rule"],
        "metrics": metrics,
        "equity_dates": [date_value.isoformat() for date_value in equity.index],
        "equity_values": [round(float(value), 2) for value in equity.values],
    }
    out_path = out_dir / f"{hashlib.md5(label.encode()).hexdigest()[:8]}.json"
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)
    return out_path


def _cache_key(tickers: list[str], start: str, end: str):
    return (tuple(sorted(tickers)), start, end)


def _clean_prices(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.sort_index().dropna(how="all").ffill().dropna(how="all")


def _save_cache(key, prices: pd.DataFrame):
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


def _should_rebalance(rule, rebalance_dates, date_value, _current_weights, _target_weights, _last_rebalance) -> bool:
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
    returns = {}
    for i in range(1, len(yearly)):
        returns[yearly.index[i].year] = (yearly.iloc[i] / yearly.iloc[i - 1]) - 1
    return returns


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
