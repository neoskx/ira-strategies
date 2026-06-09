# IRA Strategies

**Backtest and optimize investment strategies for self-directed tax-advantaged retirement accounts.**

> Built for accounts where rebalancing is free — Traditional IRA, Roth IRA, Solo 401k at
> brokerages like Robinhood, Fidelity, Schwab, etc.

**[📊 View Latest Backtest Report](https://neoskx.github.io/ira-strategies/)**

---

## What It Does

1. **You define the asset universe** — any stocks, ETFs in `universe/assets.py`
2. **It backtests 17+ strategies** across multiple allocation models and rebalancing rules
3. **Ranked by Sharpe ratio** — best risk-adjusted returns, not just raw returns
4. **Automatically refreshes** monthly via GitHub Actions → deployed to GitHub Pages

## Strategy Types

| Category | Strategies |
|---|---|
| **Static** | Fixed weight, Equal weight |
| **Momentum** | Momentum rotation (top-N), Dual Momentum (Antonacci), Trend following |
| **Optimization** | Max Sharpe, Min Variance, Risk Parity, Adaptive Asset Allocation |

## Rebalancing Rules

- **Calendar**: Monthly / Quarterly / Annual
- **Threshold**: Rebalance when any asset drifts >5% or >10%
- **Hybrid**: Calendar check + threshold filter (fewer unnecessary trades)

## Quickstart

```bash
git clone https://github.com/neoskx/ira-strategies.git
cd ira-strategies
pip install -r requirements.txt

# Run full backtest
python main.py

# Quick run (subset of strategies, uses cache)
python main.py --quick

# Force fresh data download
python main.py --no-cache
```

Open `docs/index.html` in a browser to view the report.

## Customizing Your Universe

Edit `universe/assets.py`:

```python
ASSETS = [
    {"ticker": "QQQ",  "name": "Invesco Nasdaq-100 ETF", "category": "Broad ETF"},
    {"ticker": "SPMO", "name": "S&P 500 Momentum ETF",   "category": "Factor ETF"},
    # ... add your own
]
```

## Key Design Principles

- **Zero cost rebalancing** — no transaction costs modeled (correct for IRA/Roth IRA)
- **No look-ahead bias** — strategies only see data available at each decision point
- **Transparent** — pure pandas/numpy engine, no black-box framework
- **Extensible** — abstract `Strategy` base class; swap engines without changing strategy logic

## Default Asset Universe

Broad ETFs (QQQ, VOO, VTI, VXUS), Factor ETFs (SPMO, SCHG, VBR),
Sector ETFs (VGT, SOXX), Leveraged ETFs (TQQQ, UPRO, TMF),
Alternatives (GLD, VNQ, BTC-USD), Fixed Income (BND, TLT, SHY),
Mega-Cap Stocks (AAPL, MSFT, NVDA, AMZN, GOOGL).

## Disclaimer

Backtests are hypothetical and based on historical data. Past performance does not
guarantee future results. This is an educational research tool — not financial advice.

---

*All code in this repository is AI-generated (vibe coded with [Claude Code](https://claude.ai/code)).*
