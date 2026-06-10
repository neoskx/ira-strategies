# Runtime deps injected: Strategy, RULES, pd, np
METADATA = {
    "name": "RiskParity(3m vol)",
    "label": "RiskParity(3m vol) | Calendar(monthly)",
    "rebalance_rule": "monthly",
    "suitable_for": {
        "min_horizon_years": 10, "risk_tolerance": ["conservative", "moderate"],
        "asset_types": ["ETF"], "max_drawdown_tolerance": -0.30,
        "notes": "Bridgewater All-Weather style. High Sharpe, lower absolute returns.",
    },
}

class _RiskParity(Strategy):
    def __init__(self, tickers, lookback_months=3):
        super().__init__(tickers)
        self.lookback_months = lookback_months
        self.name = f"RiskParity({lookback_months}m vol)"

    def get_weights(self, prices, as_of):
        hist = self._available_prices(prices, as_of)
        start = as_of - pd.DateOffset(months=self.lookback_months)
        inv_vols = {}
        for t in self.tickers:
            if t not in hist.columns:
                continue
            w = hist[t].loc[start:as_of].dropna()
            if len(w) < 10:
                continue
            vol = w.pct_change().dropna().std()
            if vol > 0:
                inv_vols[t] = 1.0 / vol
        total = sum(inv_vols.values())
        return {t: v / total for t, v in inv_vols.items()} if total else {}

STRATEGY_CLASS = lambda tickers: _RiskParity(tickers)
RULE = RULES["monthly"]
