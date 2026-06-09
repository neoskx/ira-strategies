# IRA Strategies — Claude Code Instructions

## Project Purpose
Backtesting and optimization tool for self-directed tax-advantaged retirement accounts
(Traditional IRA, Roth IRA, Solo 401k). Finds the best combination of allocation strategy
+ rebalancing rule based on historical data. Zero transaction cost assumption (appropriate
for these account types).

## Vibe Coding Policy
All code in this repository is AI-generated (vibe coded). Never manually write code.
All changes go through Claude Code. This means:
- Every file has a clear single responsibility
- No clever tricks — clarity over brevity
- Every new strategy must implement `Strategy` base class
- Every new rebalancing rule must follow the pattern in `rebalancing/rules.py`

## Architecture Overview

```
universe/assets.py          ← USER EDITS THIS: define asset universe
config.py                   ← USER EDITS THIS: dates, capital, parameters
main.py                     ← entry point; also defines which strategies to run
│
strategies/
  base.py                   ← abstract Strategy — implement get_weights()
  static.py                 ← FixedWeight, EqualWeight
  momentum.py               ← MomentumRotation, DualMomentum, TrendFollowing
  optimization.py           ← MaxSharpe, MinVariance, RiskParity, AdaptiveAA
│
rebalancing/rules.py        ← CalendarRebalance, ThresholdRebalance, HybridRebalance
│
engine/
  downloader.py             ← yfinance + local pickle cache
  runner.py                 ← portfolio simulation (no-cost rebalancing)
  metrics.py                ← Sharpe, Sortino, Calmar, Max Drawdown, stress tests
│
report/
  generator.py              ← HTML report builder (GitHub Pages)
  charts.py                 ← matplotlib → base64 PNG (embedded in HTML)
│
docs/index.html             ← OUTPUT: GitHub Pages report (auto-generated, do not edit)
data/prices.pkl             ← gitignored price cache
```

## How to Add a New Strategy

1. Create a class in the appropriate `strategies/*.py` file
2. Inherit from `Strategy` (strategies/base.py)
3. Implement `get_weights(prices, as_of) -> dict[str, float]`
4. Set `name`, `description`, `min_rebalance_frequency`
5. Add it to the `build_strategies()` list in `main.py`

```python
class MyStrategy(Strategy):
    name = "MyStrategy"
    description = "What it does"
    min_rebalance_frequency = "monthly"

    def get_weights(self, prices, as_of):
        hist = self._available_prices(prices, as_of)
        # ... logic ...
        return {"QQQ": 0.6, "BND": 0.4}
```

## How to Add Assets

Edit `universe/assets.py` — add a dict to `ASSETS`:
```python
{"ticker": "IBIT", "name": "iShares Bitcoin Trust ETF", "category": "Alternative"}
```

## Running Locally

```bash
pip install -r requirements.txt
python main.py              # full run
python main.py --quick      # fast subset, uses cache
python main.py --no-cache   # force fresh data download
```

## Key Design Decisions

- **No framework lock-in**: Engine is pure pandas/numpy. Abstract `Strategy` base makes
  it easy to swap in `bt`, `vectorbt`, or other engines later without changing strategy code.
- **No look-ahead bias**: `runner.py` only passes prices up to `as_of` date to strategies.
- **Zero cost assumption**: Appropriate for IRA/Roth IRA. Do not add transaction costs
  without making it a configuration option.
- **GitHub Pages**: Report is a single `docs/index.html` with base64-embedded charts.
  No external dependencies needed to view it.

## Future Features (v2)
- Robinhood API integration (robin-stocks) for automated signal execution
- Monte Carlo simulation for forward-looking return distributions
- Multi-objective optimization (Pareto frontier of return vs drawdown)
- Walk-forward validation to avoid overfitting
- Support for options strategies (covered calls on ETF positions)
