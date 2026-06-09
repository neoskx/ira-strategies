"""Abstract base class for all allocation strategies."""

from abc import ABC, abstractmethod
import pandas as pd


class Strategy(ABC):
    """
    A Strategy takes a price history and produces target weights on each rebalance date.

    To add a new strategy: subclass this, implement `get_weights()`.
    The runner calls `get_weights()` at each rebalance date.
    """

    name: str = "BaseStrategy"
    description: str = ""
    min_rebalance_frequency: str = "annual"  # hint for the runner

    def __init__(self, tickers: list[str], **kwargs):
        self.tickers = tickers

    @abstractmethod
    def get_weights(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> dict[str, float]:
        """
        Return target weights as of `as_of` date.
        weights: dict {ticker: float}, values must sum to ~1.0.
        Prices available: all history up to and including `as_of`.
        """
        ...

    def _available_prices(self, prices: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
        """Helper: slice prices up to as_of (no look-ahead)."""
        return prices[prices.index <= as_of]

    def __repr__(self):
        return f"<Strategy: {self.name}>"
