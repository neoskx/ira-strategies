---
name: "AdaptiveAA(top5, 12m mom, 3m vol)"
label: "AdaptiveAA(top5, 12m mom, 3m vol) | Calendar(monthly)"
status: builtin
---

## Description
Same as AdaptiveAA top3 but holds the top 5 funds. More diversified with slightly different concentration profile.

## Logic
1. Score all 32 funds by risk-adjusted momentum. 2. Keep top 5. 3. Weight by inverse vol. 4. Sell the rest. Repeat monthly.

## Rebalance frequency
Monthly.

## Suitable for
- Min horizon years: 10
- Risk tolerance: moderate
- Max drawdown tolerance: -45%
