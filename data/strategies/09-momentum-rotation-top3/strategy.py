# Runtime deps injected: Strategy, RULES, pd, np
METADATA = {
    "name": "MomentumRotation(top3, 12m)",
    "label": "MomentumRotation(top3, 12m) | Calendar(monthly)",
    "rebalance_rule": "monthly",
    "suitable_for": {
        "min_horizon_years": 10, "risk_tolerance": ["moderate", "aggressive"],
        "asset_types": ["ETF"], "max_drawdown_tolerance": -0.55,
        "notes": "Signal-driven rotation into top 3 by 12m return.",
    },
}

class _MomentumRotation(Strategy):
    def __init__(self, tickers, top_n, lookback_months=12, skip_months=1):
        super().__init__(tickers)
        self.top_n = top_n
        self.lookback_months = lookback_months
        self.skip_months = skip_months
        self.name = f"MomentumRotation(top{top_n}, {lookback_months}m)"

    def get_weights(self, prices, as_of):
        hist = self._available_prices(prices, as_of)
        end = as_of - pd.DateOffset(months=self.skip_months)
        start = end - pd.DateOffset(months=self.lookback_months)
        scores = {}
        for t in self.tickers:
            if t not in hist.columns:
                continue
            w = hist[t].loc[start:end].dropna()
            if len(w) >= 20:
                scores[t] = (w.iloc[-1] / w.iloc[0]) - 1
        if not scores:
            return {}
        top = sorted(scores, key=scores.get, reverse=True)[:self.top_n]
        return {t: 1.0 / len(top) for t in top}


STRATEGY_CLASS = lambda tickers: _MomentumRotation(tickers, top_n=3)
RULE = RULES["monthly"]
