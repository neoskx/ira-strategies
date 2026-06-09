"""
Portfolio simulation engine.

Simulates daily portfolio value given a Strategy + RebalanceRule + price history.
No transaction costs (appropriate for IRA/Roth IRA — no capital gains tax on trades).
"""

import pandas as pd
import numpy as np
from strategies.base import Strategy
from rebalancing.rules import CalendarRebalance, ThresholdRebalance, HybridRebalance
from engine.metrics import compute_metrics


def run_backtest(
    strategy: Strategy,
    rebalance_rule,
    prices: pd.DataFrame,
    start: str,
    end: str,
    initial_capital: float = 100_000,
) -> dict:
    """
    Run a single backtest. Returns a result dict with equity curve + metrics.

    strategy       : any Strategy subclass
    rebalance_rule : a rule from rebalancing/rules.py
    prices         : full price DataFrame (daily, adjusted close)
    start / end    : backtest date range strings
    """
    prices = prices[start:end].copy()
    if prices.empty:
        raise ValueError(f"No price data in range {start}–{end}")

    # Build rebalance date set
    rebalance_dates = _get_rebalance_dates(rebalance_rule, start, end, prices.index)

    # Initialize
    equity = pd.Series(index=prices.index, dtype=float)
    holdings: dict[str, float] = {}    # ticker → number of shares
    cash = initial_capital
    current_weights: dict[str, float] = {}
    last_rebalance = prices.index[0] - pd.Timedelta(days=999)
    rebalance_count = 0

    for date in prices.index:
        row = prices.loc[date]

        # Update portfolio value
        portfolio_val = cash + sum(
            holdings.get(t, 0) * row.get(t, np.nan)
            for t in holdings
            if not pd.isna(row.get(t, np.nan))
        )
        equity[date] = portfolio_val

        # Check if we should rebalance today
        should_rebalance = _should_rebalance(
            rebalance_rule, rebalance_dates, date,
            current_weights, None, last_rebalance
        )

        if should_rebalance or date == prices.index[0]:
            target = strategy.get_weights(prices, date)
            if not target:
                continue

            # Compute target weights considering threshold rules
            if isinstance(rebalance_rule, ThresholdRebalance):
                if not rebalance_rule.needs_rebalance(current_weights, target, last_rebalance, date):
                    continue
            elif isinstance(rebalance_rule, HybridRebalance):
                if date != prices.index[0] and not rebalance_rule.needs_rebalance(current_weights, target):
                    continue

            # Rebalance: convert everything to cash, then buy targets
            for t, shares in holdings.items():
                price = row.get(t, np.nan)
                if not pd.isna(price) and shares > 0:
                    cash += shares * price
            holdings = {}

            for t, weight in target.items():
                price = row.get(t, np.nan)
                if pd.isna(price) or price <= 0:
                    continue
                alloc = portfolio_val * weight
                holdings[t] = alloc / price
                cash -= alloc

            current_weights = target.copy()
            last_rebalance = date
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


def _get_rebalance_dates(rule, start, end, index):
    if isinstance(rule, (CalendarRebalance, HybridRebalance)):
        cal_dates = rule.rebalance_dates(start, end)
        return set(index[index.searchsorted(cal_dates, side="left").clip(0, len(index) - 1)])
    return set()


def _should_rebalance(rule, rebalance_dates, date, current_weights, target_weights, last_rebalance):
    if isinstance(rule, ThresholdRebalance):
        return True  # threshold check happens later in the loop
    return date in rebalance_dates
