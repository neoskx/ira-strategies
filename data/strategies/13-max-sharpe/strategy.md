---
name: "MaxSharpe(36m lookback)"
label: "MaxSharpe(36m lookback) | Calendar(quarterly)"
status: builtin
---

## Description
Mean-variance optimization: find the portfolio weights that maximize the Sharpe ratio using 36 months of historical returns. Requires a solver. Output changes each quarter based on the rolling data.

## Logic
1. Download 36 months of returns for all funds. 2. Run mean-variance optimization to maximize Sharpe. 3. Rebalance to the computed weights. Repeat quarterly.

## Rebalance frequency
Quarterly.

## Suitable for
- Min horizon years: 15
- Risk tolerance: moderate
- Max drawdown tolerance: -50%
