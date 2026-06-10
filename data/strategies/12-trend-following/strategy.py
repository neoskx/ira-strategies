# Runtime deps injected: Strategy, RULES, pd, np
METADATA = {
    "name": "TrendFollowing(200d MA)",
    "label": "TrendFollowing(200d MA) | Calendar(monthly)",
    "rebalance_rule": "monthly",
    "suitable_for": {
        "min_horizon_years": 10, "risk_tolerance": ["moderate"],
        "asset_types": ["ETF"], "max_drawdown_tolerance": -0.35,
        "notes": "200-day MA filter. Reduces crash exposure, may lag recoveries.",
    },
}

_RISKY = ["QQQ","VOO","SPY","VTI","VXUS","EEM","IWM","SPMO","SCHG","VBR","VGT","SOXX","XLE","XLV","XLF"]

class _TrendFollowing(Strategy):
    def __init__(self, tickers, risky, safe="BND", ma_days=200):
        super().__init__(tickers)
        self.risky = risky
        self.safe = safe
        self.ma_days = ma_days
        self.name = f"TrendFollowing({ma_days}d MA)"

    def get_weights(self, prices, as_of):
        hist = self._available_prices(prices, as_of)
        above = []
        for t in self.risky:
            if t not in hist.columns:
                continue
            s = hist[t].dropna()
            if len(s) >= self.ma_days and s.iloc[-1] > s.rolling(self.ma_days).mean().iloc[-1]:
                above.append(t)
        if above:
            return {t: 1.0 / len(above) for t in above}
        return {self.safe: 1.0} if self.safe in hist.columns else {}

STRATEGY_CLASS = lambda tickers: _TrendFollowing(tickers, risky=_RISKY)
RULE = RULES["monthly"]
