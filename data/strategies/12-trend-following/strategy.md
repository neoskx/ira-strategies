---
name: "TrendFollowing(200d MA)"
label: "TrendFollowing(200d MA) | Calendar(monthly)"
status: builtin
---

## Description
For each of the 15 risky ETFs, check if it is above its 200-day moving average. Hold the ones that are above (equal weight among them), replace the ones below with BND. Defensive approach that avoids holding ETFs in downtrends.

## Logic
1. Check each risky ETF vs its 200-day MA. 2. Hold those above in equal weight. 3. Hold BND for those below. Rebalance monthly.

## Rebalance frequency
Monthly.

## Suitable for
- Min horizon years: 10
- Risk tolerance: moderate
- Max drawdown tolerance: -35%
