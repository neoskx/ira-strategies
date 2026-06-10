---
name: "FixedWeight(QQQ:60%, SPMO:40%)"
label: "FixedWeight(QQQ:60%, SPMO:40%) | Calendar(annual)"
status: builtin
---

## Description
Hold 60% in Nasdaq-100 (QQQ) and 40% in S&P 500 Momentum (SPMO), rebalanced once a year. A pure equity portfolio tilting toward tech and price momentum.

## Universe
| Ticker | Weight | Role |
|---|---|---|
| QQQ | 60% | Nasdaq-100 — tech-heavy large cap |
| SPMO | 40% | S&P 500 momentum — strongest recent performers |

## Logic
1. Set allocations to QQQ 60%, SPMO 40%.
2. Once a year, rebalance back to target if drift exceeds 5%.
3. No other action needed.

## Rebalance frequency
Annual.

## Suitable for
- Min horizon years: 15
- Risk tolerance: aggressive
- Max drawdown tolerance: -50%
