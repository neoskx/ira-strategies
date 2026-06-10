# Runtime deps injected: Strategy, RULES, pd, np
METADATA = {
    "name": "AdaptiveAA(top5, 12m mom, 3m vol)",
    "label": "AdaptiveAA(top5, 12m mom, 3m vol) | Calendar(monthly)",
    "rebalance_rule": "monthly",
    "suitable_for": {
        "min_horizon_years": 10, "risk_tolerance": ["moderate", "aggressive"],
        "asset_types": ["ETF"], "max_drawdown_tolerance": -0.45,
        "notes": "Momentum selection + risk parity sizing. More diversified than top3 variant.",
    },
}

class _AdaptiveAA(Strategy):
    def __init__(self, tickers, top_n, momentum_months=12, vol_months=3):
        super().__init__(tickers)
        self.top_n = top_n
        self.momentum_months = momentum_months
        self.vol_months = vol_months
        self.name = f"AdaptiveAA(top{top_n}, {momentum_months}m mom, {vol_months}m vol)"

    def get_weights(self, prices, as_of):
        hist = self._available_prices(prices, as_of)
        scores = {}
        for t in self.tickers:
            if t not in hist.columns:
                continue
            w = hist[t].loc[as_of - pd.DateOffset(months=self.momentum_months):as_of].dropna()
            if len(w) >= 20:
                scores[t] = (w.iloc[-1] / w.iloc[0]) - 1
        selected = sorted(scores, key=scores.get, reverse=True)[:self.top_n]
        inv_vols = {}
        for t in selected:
            w = hist[t].loc[as_of - pd.DateOffset(months=self.vol_months):as_of].dropna()
            vol = w.pct_change().dropna().std() if len(w) >= 10 else 0
            inv_vols[t] = 1.0 / vol if vol > 0 else 1.0
        total = sum(inv_vols.values())
        return {t: v / total for t, v in inv_vols.items()} if total else {}


STRATEGY_CLASS = lambda tickers: _AdaptiveAA(tickers, top_n=5)
RULE = RULES["monthly"]
