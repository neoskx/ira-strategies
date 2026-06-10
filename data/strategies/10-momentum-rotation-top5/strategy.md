---
name: "MomentumRotation(top5, 12m)"
label: "MomentumRotation(top5, 12m) | Calendar(monthly)"
status: builtin
---

## Description
Same as top3 variant but holds the top 5 instruments (20% each). More diversified, slightly lower concentration risk.

## Logic
1. Calculate 12-month return for all assets in the universe. 2. Identify the top 5. 3. Hold them at 20% each. 4. Sell the rest. Repeat monthly.

## Rebalance frequency
Monthly.

## Suitable for
- Min horizon years: 10
- Risk tolerance: moderate
- Max drawdown tolerance: -55%
