---
name: "EqualWeight(32 assets)"
label: "EqualWeight(32 assets) | Calendar(monthly)"
status: builtin
---

## Description
Divide the portfolio equally across all 32 instruments in the universe (~3.1% each). No market view required. Relies on diversification to smooth returns and benefit from rebalancing gains.

## Logic
Every month, restore each fund to equal weight by selling overweight positions and buying underweight ones.

## Rebalance frequency
Monthly.

## Suitable for
- Min horizon years: 10
- Risk tolerance: moderate
- Max drawdown tolerance: -45%
