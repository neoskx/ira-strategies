---
name: "RiskParity(3m vol)"
label: "RiskParity(3m vol) | Calendar(monthly)"
status: builtin
---

## Description
Bridgewater All-Weather style: size each position so its risk contribution (volatility × weight) is equal across all assets. Low-volatility assets (bonds) receive larger weights than high-volatility assets (equities, crypto).

## Logic
1. Compute 3-month volatility for each fund. 2. Weight = 1 / volatility, normalized to 100%. 3. Rebalance monthly.

## Rebalance frequency
Monthly.

## Suitable for
- Min horizon years: 10
- Risk tolerance: conservative
- Max drawdown tolerance: -30%
