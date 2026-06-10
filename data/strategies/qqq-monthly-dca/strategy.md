---
name: QqqMonthlyDCA
label: "QqqMonthlyDCA(daily accumulation)"
status: implemented
---

## Description
Invest only in QQQ, but instead of holding it as a lump sum, sell to cash at the start of each month and buy back in equal daily installments over the month's trading days. By the last trading day of the month, fully invested in QQQ again.

Tests whether spreading the monthly re-entry reduces timing risk compared to continuous lump-sum QQQ buy-and-hold.

## Universe
| Ticker | Role |
|---|---|
| QQQ | Primary holding (Nasdaq-100) |
| SHY | Cash proxy during accumulation phase (1–3 yr Treasuries) |

## Logic
1. On day 1 of each month: hold 1/N QQQ, (N-1)/N SHY — where N = total trading days in this month.
2. On day 2: hold 2/N QQQ, (N-2)/N SHY.
3. Each subsequent day: increase QQQ weight by 1/N.
4. On day N (last trading day of month): hold 100% QQQ.
5. Repeat from step 1 next month.

## Parameters
None — DCA fraction is computed automatically from day position within the month.

## Rebalance frequency
Daily — the target QQQ weight changes on every trading day, so the backtest must check weights daily.

## Position sizing
- QQQ weight = day_index / total_trading_days_in_month (ramps 0→1 over the month)
- SHY weight = 1 − QQQ weight (fills the remainder)

## Suitable for
- Min horizon years: 10
- Risk tolerance: moderate, aggressive
- Max drawdown tolerance: -45%
- Notes: QQQ-only with intra-month DCA re-entry. Likely similar long-run CAGR to lump-sum QQQ but with slightly different monthly drawdown profile.
