# Runtime deps injected: Strategy, RULES, pd, np
try:
    from pypfopt import EfficientFrontier, risk_models
    _OK = True
except ImportError:
    _OK = False

METADATA = {
    "name": "MinVariance(36m lookback)",
    "label": "MinVariance(36m lookback) | Calendar(quarterly)",
    "rebalance_rule": "quarterly",
    "suitable_for": {
        "min_horizon_years": 5, "risk_tolerance": ["conservative", "moderate"],
        "asset_types": ["ETF"], "max_drawdown_tolerance": -0.25,
        "notes": "Capital preservation first. Lower returns but very low drawdowns.",
    },
}

def _eq(cols):
    w = 1.0 / len(cols) if cols else 0.0
    return {c: w for c in cols}

class _MinVariance(Strategy):
    def __init__(self, tickers, lookback_months=36):
        super().__init__(tickers)
        self.lookback_months = lookback_months
        self.name = f"MinVariance({lookback_months}m lookback)"

    def get_weights(self, prices, as_of):
        if not _OK:
            raise ImportError("pip install PyPortfolioOpt")
        hist = self._available_prices(prices, as_of)
        window = hist.loc[as_of - pd.DateOffset(months=self.lookback_months):as_of,
                          self.tickers].dropna(axis=1, how="any")
        if window.shape[1] < 2 or window.shape[0] < 60:
            return _eq(window.columns.tolist())
        try:
            cov = risk_models.CovarianceShrinkage(window).ledoit_wolf()
            frontier = EfficientFrontier(None, cov)
            frontier.min_volatility()
            return {t: w for t, w in frontier.clean_weights().items() if w > 0.001}
        except Exception:
            return _eq(window.columns.tolist())

STRATEGY_CLASS = lambda tickers: _MinVariance(tickers)
RULE = RULES["quarterly"]
