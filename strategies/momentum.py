"""
Dynamic momentum strategies:
  - MomentumRotation: hold top-N assets by recent return
  - DualMomentum: Antonacci's relative + absolute momentum
  - TrendFollowing: hold if price > N-day moving average
"""

import pandas as pd
import numpy as np
from strategies.base import Strategy
from config import (
    MOMENTUM_LOOKBACK_MONTHS,
    MOMENTUM_SKIP_MONTHS,
    MOMENTUM_TOP_N,
    TREND_MA_DAYS,
)


class MomentumRotation(Strategy):
    """
    Monthly: rank all assets by past `lookback` months return.
    Hold the top `top_n` equally weighted.
    Skip the most recent month to avoid short-term reversal noise.
    """
    min_rebalance_frequency = "monthly"

    def __init__(self, tickers: list[str], top_n: int = MOMENTUM_TOP_N,
                 lookback_months: int = MOMENTUM_LOOKBACK_MONTHS,
                 skip_months: int = MOMENTUM_SKIP_MONTHS, **kwargs):
        super().__init__(tickers, **kwargs)
        self.top_n = top_n
        self.lookback_months = lookback_months
        self.skip_months = skip_months
        self.name = f"MomentumRotation(top{top_n}, {lookback_months}m)"
        self.description = (
            f"Hold top {top_n} assets by {lookback_months}-month return, "
            f"skip last {skip_months} month(s). Rebalance monthly."
        )

    def get_weights(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
        hist = self._available_prices(prices, as_of)

        end = as_of - pd.DateOffset(months=self.skip_months)
        start = end - pd.DateOffset(months=self.lookback_months)

        scores = {}
        for t in self.tickers:
            if t not in hist.columns:
                continue
            window = hist[t].loc[start:end].dropna()
            if len(window) < 20:
                continue
            scores[t] = (window.iloc[-1] / window.iloc[0]) - 1

        if not scores:
            return {}

        ranked = sorted(scores, key=scores.get, reverse=True)
        top = ranked[: self.top_n]
        w = 1.0 / len(top)
        return {t: w for t in top}


class DualMomentum(Strategy):
    """
    Gary Antonacci's Global Equities Momentum (GEM) — generalized.

    Each month:
      1. Relative momentum: compare each risky asset vs the others.
         Pick the one with highest return over lookback period.
      2. Absolute momentum: if the winner's return < T-bill proxy, go to safe haven.

    risky_tickers : assets to rank (e.g. QQQ, VXUS)
    safe_ticker   : fallback when absolute momentum is negative (e.g. BND, SHY)
    tbill_ticker  : T-bill proxy for absolute momentum test (e.g. SHY or BIL)
    """
    min_rebalance_frequency = "monthly"

    def __init__(self, tickers: list[str],
                 risky_tickers: list[str] | None = None,
                 safe_ticker: str = "BND",
                 tbill_ticker: str = "SHY",
                 lookback_months: int = MOMENTUM_LOOKBACK_MONTHS,
                 skip_months: int = MOMENTUM_SKIP_MONTHS, **kwargs):
        super().__init__(tickers, **kwargs)
        self.risky = risky_tickers or [t for t in tickers if t not in (safe_ticker, tbill_ticker)]
        self.safe = safe_ticker
        self.tbill = tbill_ticker
        self.lookback_months = lookback_months
        self.skip_months = skip_months
        self.name = f"DualMomentum({lookback_months}m)"
        self.description = (
            f"Antonacci Dual Momentum: pick best risky asset by {lookback_months}m return, "
            f"fallback to {safe_ticker} if absolute momentum is negative."
        )

    def get_weights(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
        hist = self._available_prices(prices, as_of)
        end = as_of - pd.DateOffset(months=self.skip_months)
        start = end - pd.DateOffset(months=self.lookback_months)

        scores = {}
        for t in self.risky:
            if t not in hist.columns:
                continue
            w = hist[t].loc[start:end].dropna()
            if len(w) < 20:
                continue
            scores[t] = (w.iloc[-1] / w.iloc[0]) - 1

        if not scores:
            return {self.safe: 1.0} if self.safe in hist.columns else {}

        winner = max(scores, key=scores.get)
        winner_return = scores[winner]

        # Absolute momentum: compare winner vs T-bill proxy return
        tbill_return = 0.0
        if self.tbill in hist.columns:
            tb = hist[self.tbill].loc[start:end].dropna()
            if len(tb) >= 20:
                tbill_return = (tb.iloc[-1] / tb.iloc[0]) - 1

        if winner_return > tbill_return:
            return {winner: 1.0}
        else:
            return {self.safe: 1.0} if self.safe in hist.columns else {winner: 1.0}


class TrendFollowing(Strategy):
    """
    For each asset: hold if price > N-day simple moving average, else hold safe haven.
    Multiple assets are equally weighted among those above their MA.
    """
    min_rebalance_frequency = "monthly"

    def __init__(self, tickers: list[str],
                 risky_tickers: list[str] | None = None,
                 safe_ticker: str = "BND",
                 ma_days: int = TREND_MA_DAYS, **kwargs):
        super().__init__(tickers, **kwargs)
        self.risky = risky_tickers or [t for t in tickers if t != safe_ticker]
        self.safe = safe_ticker
        self.ma_days = ma_days
        self.name = f"TrendFollowing({ma_days}d MA)"
        self.description = (
            f"Hold each asset if price > {ma_days}-day MA, else hold {safe_ticker}. "
            "Equal weight among assets passing the filter."
        )

    def get_weights(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
        hist = self._available_prices(prices, as_of)
        above_ma = []

        for t in self.risky:
            if t not in hist.columns:
                continue
            series = hist[t].dropna()
            if len(series) < self.ma_days:
                continue
            ma = series.rolling(self.ma_days).mean().iloc[-1]
            current = series.iloc[-1]
            if current > ma:
                above_ma.append(t)

        if above_ma:
            w = 1.0 / len(above_ma)
            return {t: w for t in above_ma}
        else:
            return {self.safe: 1.0} if self.safe in hist.columns else {}
