"""Static allocation strategies: fixed weights and equal weight."""

import pandas as pd
from strategies.base import Strategy


class FixedWeight(Strategy):
    """
    Hold fixed weights, rebalance back to target on schedule.
    Example: QQQ 60%, SPMO 40%
    """
    min_rebalance_frequency = "annual"

    def __init__(self, tickers: list[str], weights: dict[str, float], **kwargs):
        super().__init__(tickers, **kwargs)
        total = sum(weights.values())
        self.weights = {t: w / total for t, w in weights.items()}  # normalize
        self.name = "FixedWeight(" + ", ".join(f"{t}:{w:.0%}" for t, w in self.weights.items()) + ")"
        self.description = "Fixed target weights, rebalance back to target on schedule."

    def get_weights(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
        return self.weights.copy()


class EqualWeight(Strategy):
    """
    Allocate equally across all tickers. Rebalance monthly.
    Surprisingly competitive — no opinions required.
    """
    min_rebalance_frequency = "monthly"

    def __init__(self, tickers: list[str], **kwargs):
        super().__init__(tickers, **kwargs)
        self.name = f"EqualWeight({len(tickers)} assets)"
        self.description = "1/N allocation across all assets. Monthly rebalance."

    def get_weights(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
        available = self._available_prices(prices, as_of)
        valid = [t for t in self.tickers if t in available.columns and available[t].notna().any()]
        w = 1.0 / len(valid) if valid else 0.0
        return {t: w for t in valid}
