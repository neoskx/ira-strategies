"""
Asset universe — edit this file to define which assets the backtest uses.

Each asset is a dict with:
  ticker   : Yahoo Finance symbol
  name     : Human-readable name
  category : Grouping label (for report)
  note     : Optional context
"""

ASSETS = [
    # --- Broad Market ETFs ---
    {"ticker": "QQQ",  "name": "Invesco Nasdaq-100 ETF",          "category": "Broad ETF"},
    {"ticker": "VOO",  "name": "Vanguard S&P 500 ETF",            "category": "Broad ETF"},
    {"ticker": "VTI",  "name": "Vanguard Total US Market ETF",    "category": "Broad ETF"},
    {"ticker": "VXUS", "name": "Vanguard Total International ETF","category": "Broad ETF"},

    # --- Factor / Smart Beta ETFs ---
    {"ticker": "SPMO", "name": "Invesco S&P 500 Momentum ETF",    "category": "Factor ETF"},
    {"ticker": "SCHG", "name": "Schwab US Large-Cap Growth ETF",  "category": "Factor ETF"},
    {"ticker": "VBR",  "name": "Vanguard Small-Cap Value ETF",    "category": "Factor ETF"},

    # --- Sector ETFs ---
    {"ticker": "VGT",  "name": "Vanguard Information Technology", "category": "Sector ETF"},
    {"ticker": "SOXX", "name": "iShares Semiconductor ETF",       "category": "Sector ETF"},

    # --- Leveraged ETFs ---
    {"ticker": "TQQQ", "name": "ProShares UltraPro QQQ (3x)",    "category": "Leveraged ETF",
     "note": "Extreme volatility — -79% in 2022"},
    {"ticker": "UPRO", "name": "ProShares UltraPro S&P500 (3x)", "category": "Leveraged ETF"},
    {"ticker": "TMF",  "name": "Direxion 3x Long Treasury",       "category": "Leveraged ETF",
     "note": "Hedge for TQQQ/UPRO strategies"},

    # --- Alternatives ---
    {"ticker": "GLD",  "name": "SPDR Gold ETF",                   "category": "Alternative"},
    {"ticker": "VNQ",  "name": "Vanguard Real Estate ETF (REIT)", "category": "Alternative"},
    {"ticker": "BTC-USD", "name": "Bitcoin (spot price proxy)",   "category": "Alternative",
     "note": "Spot price — not directly tradeable in standard IRA; use IBIT/FBTC ETFs"},

    # --- Fixed Income ---
    {"ticker": "BND",  "name": "Vanguard Total Bond Market ETF",  "category": "Fixed Income"},
    {"ticker": "TLT",  "name": "iShares 20+ Year Treasury ETF",   "category": "Fixed Income"},
    {"ticker": "SHY",  "name": "iShares 1-3 Year Treasury ETF",   "category": "Fixed Income",
     "note": "Cash proxy for dual momentum / trend following"},

    # --- Individual Stocks ---
    {"ticker": "AAPL", "name": "Apple Inc.",                      "category": "Mega-Cap Stock"},
    {"ticker": "MSFT", "name": "Microsoft Corp.",                 "category": "Mega-Cap Stock"},
    {"ticker": "NVDA", "name": "NVIDIA Corp.",                    "category": "Mega-Cap Stock"},
    {"ticker": "AMZN", "name": "Amazon.com Inc.",                 "category": "Mega-Cap Stock"},
    {"ticker": "GOOGL","name": "Alphabet Inc. (Class A)",         "category": "Mega-Cap Stock"},
]

# Convenience: tickers only
TICKERS = [a["ticker"] for a in ASSETS]

# Lookup by ticker
ASSET_MAP = {a["ticker"]: a for a in ASSETS}


def get_tickers(categories: list[str] | None = None) -> list[str]:
    """Return tickers filtered by category. None = all."""
    if categories is None:
        return TICKERS
    return [a["ticker"] for a in ASSETS if a["category"] in categories]
