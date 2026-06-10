# /build-strategy

Interview the user about a strategy they want to backtest, write the spec file, then invoke the `strategy-builder` agent to generate and validate the code.

## Workflow

### Step 1 — Gather the spec

Ask the user the following questions (skip any already answered in their message):

1. **Name** — What should we call this strategy? (becomes the Python class name)
2. **Universe** — Which tickers does it trade? Or does it pick from the full 32-instrument universe?
3. **Signal** — What drives buy/sell decisions? (price momentum, moving average, time-based DCA, fixed allocation, volatility, etc.)
4. **Position sizing** — Equal weight? Inverse volatility? Fixed percentages? Full allocation to winner?
5. **Defensive fallback** — Does it go to cash/bonds when the signal is off, or stays invested?
6. **Rebalance frequency** — Daily, monthly, quarterly, or annual?
7. **Horizon & risk** — Min investment horizon (years)? Risk tolerance (conservative/moderate/aggressive)?

Keep questions conversational — if the user already described the logic clearly, infer answers rather than asking again.

### Step 2 — Write the spec file

Write the spec to `data/strategies/<kebab-case-name>.md` using this template:

```markdown
---
name: ClassName
label: "Human readable label (params)"
status: draft
---

## Description
[plain English summary]

## Universe
[tickers and roles]

## Logic
[numbered pseudocode steps]

## Parameters
[configurable params with defaults, or "None"]

## Rebalance frequency
[daily / monthly / quarterly / annual — and why]

## Position sizing
[how weights are computed]

## Suitable for
- Min horizon years: N
- Risk tolerance: [list]
- Max drawdown tolerance: -X%
- Notes: [one sentence]
```

### Step 3 — Invoke the strategy-builder agent

Run the `strategy-builder` subagent with the spec file path. It will:
- Write the Python Strategy class in `agents/backtest/backtest_core.py`
- Add the catalog entry to `agents/strategy/strategy_catalog.py`
- Validate with a test backtest run

### Step 4 — Report results

Tell the user:
- Strategy name and index
- Backtest result if validation passed (CAGR, Sharpe, Max DD)
- Any issues or limitations found
- Next steps (run `/find-best` to compare against all strategies)
