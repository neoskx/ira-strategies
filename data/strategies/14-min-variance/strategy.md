---
name: "MinVariance(36m lookback)"
label: "MinVariance(36m lookback) | Calendar(quarterly)"
status: builtin
---

## Description
Minimum variance optimization: find the portfolio weights that minimize total volatility regardless of return. Results in heavy allocation to bonds and gold. Capital preservation focus.

## Logic
1. Download 36 months of returns. 2. Run min-variance optimization. 3. Rebalance to computed weights. Repeat quarterly.

## Rebalance frequency
Quarterly.

## Suitable for
- Min horizon years: 5
- Risk tolerance: conservative
- Max drawdown tolerance: -25%
