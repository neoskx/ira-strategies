# Runtime deps injected: Strategy, RULES, pd, np
METADATA = {
    "name": "DualMomentum(12m)",
    "label": "DualMomentum(12m) | Calendar(monthly)",
    "rebalance_rule": "monthly",
    "suitable_for": {
        "min_horizon_years": 10, "risk_tolerance": ["moderate", "aggressive"],
        "asset_types": ["ETF"], "max_drawdown_tolerance": -0.40,
        "notes": "Defensive: switches to bonds in downtrends.",
    },
}

class _DualMomentum(Strategy):
    def __init__(self, tickers, risky, safe="BND", tbill="SHY", lookback=12, skip=1):
        super().__init__(tickers)
        self.risky = risky
        self.safe = safe
        self.tbill = tbill
        self.lookback = lookback
        self.skip = skip
        self.name = f"DualMomentum({lookback}m)"

    def get_weights(self, prices, as_of):
        hist = self._available_prices(prices, as_of)
        end = as_of - pd.DateOffset(months=self.skip)
        start = end - pd.DateOffset(months=self.lookback)
        scores = {}
        for t in self.risky:
            if t not in hist.columns:
                continue
            w = hist[t].loc[start:end].dropna()
            if len(w) >= 20:
                scores[t] = (w.iloc[-1] / w.iloc[0]) - 1
        if not scores:
            return {self.safe: 1.0} if self.safe in hist.columns else {}
        winner = max(scores, key=scores.get)
        tbill_ret = 0.0
        if self.tbill in hist.columns:
            tb = hist[self.tbill].loc[start:end].dropna()
            if len(tb) >= 20:
                tbill_ret = (tb.iloc[-1] / tb.iloc[0]) - 1
        if scores[winner] > tbill_ret:
            return {winner: 1.0}
        return {self.safe: 1.0} if self.safe in hist.columns else {winner: 1.0}

STRATEGY_CLASS = lambda tickers: _DualMomentum(tickers, risky=["QQQ", "VXUS"])
RULE = RULES["monthly"]
