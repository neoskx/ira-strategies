"""Performance metrics calculated from an equity curve (daily portfolio values)."""

import numpy as np
import pandas as pd
from config import RISK_FREE_RATE, TRADING_DAYS_PER_YEAR


def compute_metrics(equity: pd.Series) -> dict:
    """
    Given a daily equity curve (pd.Series, index=date, values=portfolio value),
    return a dict of performance metrics.
    """
    returns = equity.pct_change().dropna()

    total_return = (equity.iloc[-1] / equity.iloc[0]) - 1
    n_years = len(equity) / TRADING_DAYS_PER_YEAR
    cagr = (1 + total_return) ** (1 / n_years) - 1 if n_years > 0 else 0

    vol = returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)

    rf_daily = (1 + RISK_FREE_RATE) ** (1 / TRADING_DAYS_PER_YEAR) - 1
    excess = returns - rf_daily
    sharpe = (excess.mean() / returns.std()) * np.sqrt(TRADING_DAYS_PER_YEAR) if returns.std() > 0 else 0

    downside = returns[returns < rf_daily]
    sortino_denom = downside.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    sortino = (returns.mean() - rf_daily) * TRADING_DAYS_PER_YEAR / sortino_denom if sortino_denom > 0 else 0

    max_dd = _max_drawdown(equity)
    calmar = cagr / abs(max_dd) if max_dd != 0 else 0

    recovery = _recovery_months(equity)

    year_returns = _annual_returns(equity)
    worst_year = min(year_returns.values()) if year_returns else None
    best_year = max(year_returns.values()) if year_returns else None

    stress = _stress_returns(equity)

    return {
        "cagr": cagr,
        "total_return": total_return,
        "volatility": vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": max_dd,
        "calmar": calmar,
        "recovery_months": recovery,
        "best_year": best_year,
        "worst_year": worst_year,
        "annual_returns": year_returns,
        **stress,
    }


def _max_drawdown(equity: pd.Series) -> float:
    rolling_max = equity.cummax()
    drawdown = (equity - rolling_max) / rolling_max
    return drawdown.min()


def _recovery_months(equity: pd.Series) -> int | None:
    rolling_max = equity.cummax()
    drawdown = (equity - rolling_max) / rolling_max
    trough_idx = drawdown.idxmin()
    post = equity[trough_idx:]
    peak_val = rolling_max[trough_idx]
    recovered = post[post >= peak_val]
    if recovered.empty:
        return None
    delta = recovered.index[0] - trough_idx
    return int(delta.days / 30)


def _annual_returns(equity: pd.Series) -> dict:
    yearly = equity.resample("YE").last()
    returns = {}
    for i in range(1, len(yearly)):
        year = yearly.index[i].year
        r = (yearly.iloc[i] / yearly.iloc[i - 1]) - 1
        returns[year] = r
    return returns


def _stress_returns(equity: pd.Series) -> dict:
    result = {}

    # 2022 bear market
    y2022 = equity["2022-01-01":"2022-12-31"]
    if len(y2022) > 5:
        result["return_2022"] = (y2022.iloc[-1] / y2022.iloc[0]) - 1

    # COVID crash: Feb 19 – Mar 23, 2020
    covid = equity["2020-02-19":"2020-03-23"]
    if len(covid) > 3:
        result["covid_crash"] = (covid.iloc[-1] / covid.iloc[0]) - 1

    # 2018 Q4 selloff
    q4_2018 = equity["2018-10-01":"2018-12-31"]
    if len(q4_2018) > 3:
        result["return_2018q4"] = (q4_2018.iloc[-1] / q4_2018.iloc[0]) - 1

    return result
