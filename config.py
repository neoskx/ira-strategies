from datetime import date

START_DATE = "2016-01-01"       # 10Y primary backtest start (SPMO available from Oct 2015)
START_DATE_15Y = "2011-01-01"   # 15Y extended backtest (no SPMO)
END_DATE = date.today().isoformat()

INITIAL_CAPITAL = 100_000       # USD

RISK_FREE_RATE = 0.045          # 10Y Treasury yield, annualized

TRADING_DAYS_PER_YEAR = 252

# Rebalancing thresholds
THRESHOLD_TIGHT = 0.05          # 5% drift triggers rebalance
THRESHOLD_LOOSE = 0.10          # 10% drift triggers rebalance

# Momentum lookback windows (in months)
MOMENTUM_LOOKBACK_MONTHS = 12   # Standard Antonacci dual momentum window
MOMENTUM_SKIP_MONTHS = 1        # Skip most recent month (avoids short-term reversal)

# Top-N assets to hold in rotation strategies
MOMENTUM_TOP_N = 3

# Trend following: moving average window
TREND_MA_DAYS = 200

# Minimum rebalance interval for threshold strategies (days)
MIN_REBALANCE_INTERVAL_DAYS = 21  # ~1 month — avoid excessive trading

# Output paths
OUTPUT_DIR = "docs"             # GitHub Pages serves from docs/
CHARTS_DIR = f"{OUTPUT_DIR}/charts"
REPORT_FILE = f"{OUTPUT_DIR}/index.html"
DATA_CACHE = "data/prices.pkl"
