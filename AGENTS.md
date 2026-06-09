# Agent Conventions

This project is vibe-coded — all code changes are made by AI agents (Claude Code).
This file defines conventions every agent must follow.

## Golden Rules

1. **Read before write** — always read the file before editing it.
2. **One responsibility per file** — don't collapse modules.
3. **No personal data** — this repo is intended to go public. Never hardcode names,
   account numbers, portfolio values, or any personal financial information.
4. **Tests are truth** — if `python main.py --quick` fails, the change is broken.
5. **docs/ is generated** — never manually edit `docs/index.html` or chart files.
   They are overwritten by `main.py`.

## Adding a Strategy (step by step)

```
1. Choose the right file:
   - Fixed/passive allocation → strategies/static.py
   - Signal-driven (momentum, trend) → strategies/momentum.py
   - Model-driven (optimizer) → strategies/optimization.py

2. Inherit Strategy, implement get_weights(prices, as_of)
   - prices is the FULL price DataFrame — slice it with self._available_prices()
   - as_of is a pd.Timestamp — no look-ahead beyond this date
   - Return dict {ticker: float} summing to 1.0

3. Add (strategy_instance, rebalance_rule) to build_strategies() in main.py

4. Run python main.py --quick to verify no errors
```

## Rebalancing Rules

Defined in `rebalancing/rules.py`. Presets in `RULES` dict:
- `RULES["monthly"]` — CalendarRebalance monthly
- `RULES["quarterly"]` — CalendarRebalance quarterly
- `RULES["annual"]` — CalendarRebalance annual
- `RULES["hybrid_monthly"]` — HybridRebalance (monthly check + 10% threshold)

## Metrics

All metrics come from `engine/metrics.py::compute_metrics(equity_series)`.
Add new metrics there and they auto-appear in the report.

## Report

`report/generator.py` builds the HTML. `report/charts.py` generates charts.
Charts are embedded as base64 PNG — no separate file management needed.

## GitHub Actions

The workflow in `.github/workflows/backtest.yml`:
- Runs monthly (1st of each month)
- Runs on every push to main
- Downloads fresh data (no cache in CI)
- Commits updated docs/ back to main
- Deploys docs/ to GitHub Pages

To trigger manually: GitHub UI → Actions → Monthly Backtest & Deploy → Run workflow.

## Dependency Management

Add new packages to `requirements.txt`. Use `>=` version pins, not `==`.
Do not add packages without a clear reason — keep the dependency list minimal.
