"""
Rebalancing rules — when to trigger a rebalance.

Each rule takes current weights and target weights and returns True if rebalance needed.
Combined with a calendar trigger in the runner.
"""

from dataclasses import dataclass
from config import THRESHOLD_TIGHT, THRESHOLD_LOOSE, MIN_REBALANCE_INTERVAL_DAYS
import pandas as pd


@dataclass
class RebalanceRule:
    name: str
    description: str


class CalendarRebalance(RebalanceRule):
    """Rebalance on a fixed calendar schedule."""

    FREQ_MAP = {
        "monthly": "MS",
        "quarterly": "QS",
        "annual": "YS",
    }

    def __init__(self, frequency: str = "monthly"):
        assert frequency in self.FREQ_MAP, f"frequency must be one of {list(self.FREQ_MAP)}"
        self.frequency = frequency
        super().__init__(
            name=f"Calendar({frequency})",
            description=f"Rebalance on every {frequency} boundary."
        )

    def rebalance_dates(self, start: str, end: str) -> pd.DatetimeIndex:
        return pd.date_range(start=start, end=end, freq=self.FREQ_MAP[self.frequency])


class ThresholdRebalance(RebalanceRule):
    """
    Rebalance when any asset drifts more than `threshold` from its target weight.
    Check daily; enforce minimum interval between trades.
    """

    def __init__(self, threshold: float = THRESHOLD_TIGHT,
                 min_interval_days: int = MIN_REBALANCE_INTERVAL_DAYS):
        self.threshold = threshold
        self.min_interval_days = min_interval_days
        super().__init__(
            name=f"Threshold({threshold:.0%})",
            description=(
                f"Rebalance when any asset drifts >{threshold:.0%} from target. "
                f"Min {min_interval_days} days between rebalances."
            )
        )

    def needs_rebalance(self, current_weights: dict, target_weights: dict,
                        last_rebalance: pd.Timestamp, today: pd.Timestamp) -> bool:
        if (today - last_rebalance).days < self.min_interval_days:
            return False
        for t, target in target_weights.items():
            current = current_weights.get(t, 0.0)
            if abs(current - target) > self.threshold:
                return True
        return False


class HybridRebalance(RebalanceRule):
    """
    Monthly calendar check PLUS threshold trigger.
    Rebalances if: (it's a calendar date) AND (drift exceeds threshold).
    Best of both: systematic discipline + avoids unnecessary small trades.
    """

    def __init__(self, frequency: str = "monthly",
                 threshold: float = THRESHOLD_LOOSE):
        self.calendar = CalendarRebalance(frequency)
        self.threshold = threshold
        super().__init__(
            name=f"Hybrid({frequency}, {threshold:.0%})",
            description=(
                f"Check {frequency}; rebalance only if any asset drifts >{threshold:.0%}. "
                "Reduces unnecessary trades while staying systematic."
            )
        )

    def rebalance_dates(self, start: str, end: str) -> pd.DatetimeIndex:
        return self.calendar.rebalance_dates(start, end)

    def needs_rebalance(self, current_weights: dict, target_weights: dict) -> bool:
        for t, target in target_weights.items():
            current = current_weights.get(t, 0.0)
            if abs(current - target) > self.threshold:
                return True
        return False


# Convenience presets
RULES = {
    "monthly": CalendarRebalance("monthly"),
    "quarterly": CalendarRebalance("quarterly"),
    "annual": CalendarRebalance("annual"),
    "threshold_5pct": ThresholdRebalance(THRESHOLD_TIGHT),
    "threshold_10pct": ThresholdRebalance(THRESHOLD_LOOSE),
    "hybrid_monthly": HybridRebalance("monthly", THRESHOLD_LOOSE),
    "hybrid_quarterly": HybridRebalance("quarterly", THRESHOLD_LOOSE),
}
