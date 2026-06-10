# Runtime deps injected: Strategy, RULES, pd, np
METADATA = {
    "name": "QqqVooSpyAdaptive(12m mom, 3m vol)",
    "label": "QqqVooSpyAdaptive(12m mom, 3m vol) | Calendar(monthly)",
    "rebalance_rule": "monthly",
    "suitable_for": {
        "min_horizon_years": 10, "risk_tolerance": ["moderate", "aggressive"],
        "asset_types": ["ETF"], "max_drawdown_tolerance": -0.45,
        "notes": "Constrained to QQQ, VOO, SPY. Risk-adjusted momentum picks the strongest index ETF.",
    },
}

class _QqqVooSpyAdaptive(Strategy):
    def __init__(self, tickers, lookback=12, vol_months=3):
        super().__init__(tickers)
        self.allowed = ["QQQ", "VOO", "SPY"]
        self.lookback = lookback
        self.vol_months = vol_months
        self.name = f"QqqVooSpyAdaptive({lookback}m mom, {vol_months}m vol)"

    def get_weights(self, prices, as_of):
        hist = self._available_prices(prices, as_of)
        scores = {}
        for t in self.allowed:
            if t not in hist.columns:
                continue
            mw = hist[t].loc[as_of - pd.DateOffset(months=self.lookback):as_of].dropna()
            vw = hist[t].loc[as_of - pd.DateOffset(months=self.vol_months):as_of].dropna()
            if len(mw) < 60 or len(vw) < 20:
                continue
            mom = (mw.iloc[-1] / mw.iloc[0]) - 1
            vol = vw.pct_change().dropna().std()
            if vol > 0:
                scores[t] = mom / vol
        if not scores:
            return {}
        winner = max(scores, key=scores.get)
        return {"VOO": 0.50, "SPY": 0.50} if winner in ("VOO", "SPY") else {"QQQ": 1.0}

STRATEGY_CLASS = lambda tickers: _QqqVooSpyAdaptive(tickers)
RULE = RULES["monthly"]
