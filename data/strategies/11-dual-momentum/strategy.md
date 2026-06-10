---
name: "DualMomentum(12m)"
label: "DualMomentum(12m) | Calendar(monthly)"
status: builtin
---

## Description
Gary Antonacci's Dual Momentum: compare QQQ vs VXUS over 12 months (relative momentum), then compare the winner vs SHY (absolute momentum). If the equity winner beats cash, hold it. Otherwise hold BND. Defensive and historically effective.

## Logic
1. Compare 12m return of QQQ vs VXUS. 2. Take the winner. 3. If the winner beats SHY → hold it 100%. If not → hold BND 100%. Repeat monthly.

## Rebalance frequency
Monthly.

## Suitable for
- Min horizon years: 10
- Risk tolerance: moderate
- Max drawdown tolerance: -40%
