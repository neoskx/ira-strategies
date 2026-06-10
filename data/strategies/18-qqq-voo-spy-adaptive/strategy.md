---
name: "QqqVooSpyAdaptive(12m mom, 3m vol)"
label: "QqqVooSpyAdaptive(12m mom, 3m vol) | Calendar(monthly)"
status: builtin
---

## Description
Constrained momentum: only consider QQQ, VOO, and SPY. Score each by risk-adjusted momentum. If QQQ wins, hold 100% QQQ. If VOO or SPY wins, hold 50% VOO + 50% SPY (split to reduce fund-specific risk).

## Logic
1. Score QQQ, VOO, SPY by 12m return / 3m vol. 2. If QQQ wins → 100% QQQ. 3. If VOO or SPY wins → 50% VOO + 50% SPY. Rebalance monthly.

## Rebalance frequency
Monthly.

## Suitable for
- Min horizon years: 10
- Risk tolerance: moderate
- Max drawdown tolerance: -45%
