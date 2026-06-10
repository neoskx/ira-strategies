---
name: "FixedWeight(TQQQ:55%, TMF:45%)"
label: "FixedWeight(TQQQ:55%, TMF:45%) | Calendar(monthly)"
status: builtin
---

## Description
Leveraged risk-parity pairing: 55% 3x Nasdaq-100 (TQQQ) with 45% 3x long-term Treasuries (TMF). The two assets are historically negatively correlated, amplifying both upside and downside. Known as the 'HEDGEFUNDIE adventure'.

## Logic
Rebalance monthly — critical for leveraged strategies due to volatility decay. For aggressive investors with 20+ year horizon only.

## Rebalance frequency
Monthly.

## Suitable for
- Min horizon years: 20
- Risk tolerance: aggressive
- Max drawdown tolerance: -70%
