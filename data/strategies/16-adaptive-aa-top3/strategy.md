---
name: "AdaptiveAA(top3, 12m mom, 3m vol)"
label: "AdaptiveAA(top3, 12m mom, 3m vol) | Calendar(monthly)"
status: builtin
---

## Description
Adaptive Asset Allocation: select the top 3 funds by risk-adjusted momentum (12m return / 3m volatility), then size them by inverse volatility. Combines momentum selection with risk-parity weighting. Research-backed and typically high Sharpe.

## Logic
1. Score all 32 funds: score = 12m return / 3m vol. 2. Keep top 3 with positive momentum. 3. Weight by inverse vol. 4. Sell the rest. Repeat monthly.

## Rebalance frequency
Monthly.

## Suitable for
- Min horizon years: 10
- Risk tolerance: moderate
- Max drawdown tolerance: -45%
