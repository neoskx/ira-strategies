"""
Optimization-based allocation strategies using PyPortfolioOpt.

  - MaxSharpe     : Maximize Sharpe ratio (efficient frontier tangency portfolio)
  - MinVariance   : Minimize portfolio volatility
  - RiskParity    : Equal risk contribution (inverse-volatility weighting)
  - AdaptiveAA    : Momentum selection + risk parity sizing (ReSolve AM style)
"""

import pandas as pd
import numpy as np
from strategies.base import Strategy
from config import MOMENTUM_LOOKBACK_MONTHS, MOMENTUM_TOP_N, RISK_FREE_RATE

try:
    from pypfopt import EfficientFrontier, risk_models, expected_returns
    PYPFOPT_AVAILABLE = True
except ImportError:
    PYPFOPT_AVAILABLE = False


class MaxSharpe(Strategy):
    """
    Quarterly: fit mean-variance model on trailing `lookback_months` of data.
    Return weights at the efficient frontier tangency point (max Sharpe).
    """
    min_rebalance_frequency = "quarterly"

    def __init__(self, tickers: list[str], lookback_months: int = 36, **kwargs):
        super().__init__(tickers, **kwargs)
        self.lookback_months = lookback_months
        self.name = f"MaxSharpe({lookback_months}m lookback)"
        self.description = (
            f"PyPortfolioOpt max-Sharpe portfolio using {lookback_months}m trailing data. "
            "Rebalance quarterly."
        )

    def get_weights(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
        if not PYPFOPT_AVAILABLE:
            raise ImportError("PyPortfolioOpt not installed. Run: pip install PyPortfolioOpt")

        hist = self._available_prices(prices, as_of)
        start = as_of - pd.DateOffset(months=self.lookback_months)
        window = hist.loc[start:as_of, self.tickers].dropna(axis=1, how="any")

        if window.shape[1] < 2 or window.shape[0] < 60:
            return self._fallback_equal(window.columns.tolist())

        try:
            mu = expected_returns.mean_historical_return(window, returns_data=False)
            S = risk_models.CovarianceShrinkage(window).ledoit_wolf()
            ef = EfficientFrontier(mu, S)
            ef.max_sharpe(risk_free_rate=RISK_FREE_RATE)
            weights = ef.clean_weights()
            return {t: w for t, w in weights.items() if w > 0.001}
        except Exception:
            return self._fallback_equal(window.columns.tolist())

    def _fallback_equal(self, tickers):
        w = 1.0 / len(tickers) if tickers else 0
        return {t: w for t in tickers}


class MinVariance(Strategy):
    """
    Quarterly: fit covariance model, return minimum-variance portfolio weights.
    Lowest risk option — prioritizes capital preservation.
    """
    min_rebalance_frequency = "quarterly"

    def __init__(self, tickers: list[str], lookback_months: int = 36, **kwargs):
        super().__init__(tickers, **kwargs)
        self.lookback_months = lookback_months
        self.name = f"MinVariance({lookback_months}m lookback)"
        self.description = (
            f"Minimum variance portfolio using {lookback_months}m trailing data. "
            "Lowest volatility possible given the asset set."
        )

    def get_weights(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
        if not PYPFOPT_AVAILABLE:
            raise ImportError("PyPortfolioOpt not installed.")

        hist = self._available_prices(prices, as_of)
        start = as_of - pd.DateOffset(months=self.lookback_months)
        window = hist.loc[start:as_of, self.tickers].dropna(axis=1, how="any")

        if window.shape[1] < 2 or window.shape[0] < 60:
            w = 1.0 / window.shape[1] if window.shape[1] > 0 else 0
            return {t: w for t in window.columns}

        try:
            S = risk_models.CovarianceShrinkage(window).ledoit_wolf()
            ef = EfficientFrontier(None, S)
            ef.min_volatility()
            weights = ef.clean_weights()
            return {t: w for t, w in weights.items() if w > 0.001}
        except Exception:
            w = 1.0 / window.shape[1]
            return {t: w for t in window.columns}


class RiskParity(Strategy):
    """
    Equal risk contribution: weight each asset by inverse of its trailing volatility.
    Used by Bridgewater's All Weather. Lower returns, very high Sharpe.
    """
    min_rebalance_frequency = "monthly"

    def __init__(self, tickers: list[str], lookback_months: int = 3, **kwargs):
        super().__init__(tickers, **kwargs)
        self.lookback_months = lookback_months
        self.name = f"RiskParity({lookback_months}m vol)"
        self.description = (
            f"Inverse-volatility weighting using {lookback_months}m trailing vol. "
            "Each asset contributes equal risk."
        )

    def get_weights(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
        hist = self._available_prices(prices, as_of)
        start = as_of - pd.DateOffset(months=self.lookback_months)

        inv_vols = {}
        for t in self.tickers:
            if t not in hist.columns:
                continue
            window = hist[t].loc[start:as_of].dropna()
            if len(window) < 10:
                continue
            vol = window.pct_change().dropna().std()
            if vol > 0:
                inv_vols[t] = 1.0 / vol

        if not inv_vols:
            return {}

        total = sum(inv_vols.values())
        return {t: v / total for t, v in inv_vols.items()}


class AdaptiveAssetAllocation(Strategy):
    """
    ReSolve Asset Management style: Adaptive Asset Allocation.

    Monthly:
      1. Momentum filter: keep top `top_n` assets by `momentum_months` return.
      2. Risk parity sizing: weight survivors by inverse volatility.

    Best risk-adjusted strategy in research — captures momentum while controlling risk.
    Min rebalance: monthly (~30 min/month in Robinhood).
    """
    min_rebalance_frequency = "monthly"

    def __init__(self, tickers: list[str],
                 top_n: int = MOMENTUM_TOP_N,
                 momentum_months: int = MOMENTUM_LOOKBACK_MONTHS,
                 vol_months: int = 3, **kwargs):
        super().__init__(tickers, **kwargs)
        self.top_n = top_n
        self.momentum_months = momentum_months
        self.vol_months = vol_months
        self.name = f"AdaptiveAA(top{top_n}, {momentum_months}m mom, {vol_months}m vol)"
        self.description = (
            f"Step 1: keep top {top_n} assets by {momentum_months}m momentum. "
            f"Step 2: risk-parity weight by {vol_months}m inverse-volatility. "
            "Monthly rebalance."
        )

    def get_weights(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
        hist = self._available_prices(prices, as_of)
        mom_start = as_of - pd.DateOffset(months=self.momentum_months)

        # Step 1: momentum ranking
        scores = {}
        for t in self.tickers:
            if t not in hist.columns:
                continue
            w = hist[t].loc[mom_start:as_of].dropna()
            if len(w) < 20:
                continue
            scores[t] = (w.iloc[-1] / w.iloc[0]) - 1

        ranked = sorted(scores, key=scores.get, reverse=True)
        selected = ranked[: self.top_n]

        if not selected:
            return {}

        # Step 2: risk parity on selected
        vol_start = as_of - pd.DateOffset(months=self.vol_months)
        inv_vols = {}
        for t in selected:
            w = hist[t].loc[vol_start:as_of].dropna()
            if len(w) < 10:
                inv_vols[t] = 1.0
                continue
            vol = w.pct_change().dropna().std()
            inv_vols[t] = 1.0 / vol if vol > 0 else 1.0

        total = sum(inv_vols.values())
        return {t: v / total for t, v in inv_vols.items()}
