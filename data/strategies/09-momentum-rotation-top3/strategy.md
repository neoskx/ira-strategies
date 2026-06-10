---
name: "MomentumRotation(top3, 12m)"
label: "MomentumRotation(top3, 12m) | Calendar(monthly)"
status: builtin
---

## Description
Each month, rank all assets in the universe by 12-month total return. Hold the top 3 in equal weight (33.3% each). Rotates monthly. Performs well in trending markets, can lag in choppy sideways periods.

## Logic
1. Calculate 12-month return for all assets in the universe. 2. Identify the top 3. 3. Hold them equally. 4. Sell anything outside the top 3. Repeat monthly.

## Rebalance frequency
Monthly.

## Suitable for
- Min horizon years: 10
- Risk tolerance: moderate
- Max drawdown tolerance: -55%
