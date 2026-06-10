# Runtime deps injected: Strategy, RULES, pd, np
try:
    from pypfopt import EfficientFrontier, expected_returns, risk_models
    _OK = True
except ImportError:
    _OK = False

METADATA = {
    "name": "MaxSharpe(36m lookback)",
    "label": "MaxSharpe(36m lookback) | Calendar(quarterly)",
    "rebalance_rule": "quarterly",
    "suitable_for": {
        "min_horizon_years": 15, "risk_tolerance": ["moderate", "aggressive"],
        "asset_types": ["ETF"], "max_drawdown_tolerance": -0.50,
        "notes": "Mean-variance optimization. Model-dependent, works best with 8+ uncorrelated assets.",
    },
}

def _eq(cols):
    w = 1.0 / len(cols) if cols else 0.0
    return {c: w for c in cols}

class _MaxSharpe(Strategy):
    def __init__(self, tickers, lookback_months=36):
        super().__init__(tickers)
        self.lookback_months = lookback_months
        self.name = f"MaxSharpe({lookback_months}m lookback)"

    def get_weights(self, prices, as_of):
        if not _OK:
            raise ImportError("pip install PyPortfolioOpt")
        hist = self._available_prices(prices, as_of)
        window = hist.loc[as_of - pd.DateOffset(months=self.lookback_months):as_of,
                          self.tickers].dropna(axis=1, how="any")
        if window.shape[1] < 2 or window.shape[0] < 60:
            return _eq(window.columns.tolist())
        try:
            mu = expected_returns.mean_historical_return(window, returns_data=False)
            cov = risk_models.CovarianceShrinkage(window).ledoit_wolf()
            frontier = EfficientFrontier(mu, cov)
            frontier.max_sharpe(risk_free_rate=0.045)
            return {t: w for t, w in frontier.clean_weights().items() if w > 0.001}
        except Exception:
            return _eq(window.columns.tolist())

STRATEGY_CLASS = lambda tickers: _MaxSharpe(tickers)
RULE = RULES["quarterly"]
