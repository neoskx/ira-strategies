# Runtime deps injected: Strategy, RULES, pd, np
METADATA = {
    "name": "EqualWeight(all assets)",
    "label": "EqualWeight(all assets) | Calendar(monthly)",
    "rebalance_rule": "monthly",
    "suitable_for": {
        "min_horizon_years": 10, "risk_tolerance": ["moderate", "aggressive"],
        "asset_types": ["ETF"], "max_drawdown_tolerance": -0.45,
        "notes": "1/N diversification across all assets. No market view required.",
    },
}

class _EqualWeight(Strategy):
    def __init__(self, tickers):
        super().__init__(tickers)
        self.name = "EqualWeight(all assets)"

    def get_weights(self, prices, as_of):
        hist = self._available_prices(prices, as_of)
        valid = [t for t in self.tickers if t in hist.columns and hist[t].notna().any()]
        w = 1.0 / len(valid) if valid else 0.0
        return {t: w for t in valid}

STRATEGY_CLASS = lambda tickers: _EqualWeight(tickers)
RULE = RULES["monthly"]
