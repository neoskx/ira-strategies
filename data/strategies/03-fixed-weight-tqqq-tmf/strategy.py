# Runtime deps injected: Strategy, RULES, pd, np
METADATA = {
    "name": "FixedWeight(TQQQ:55%, TMF:45%)",
    "label": "FixedWeight(TQQQ:55%, TMF:45%) | Calendar(monthly)",
    "rebalance_rule": "monthly",
    "suitable_for": {
        "min_horizon_years": 20, "risk_tolerance": ["aggressive"],
        "asset_types": ["ETF"], "max_drawdown_tolerance": -0.70,
        "notes": "Leveraged. Only suitable for investors with 20+ year horizon.",
    },
}

class _FixedWeight(Strategy):
    def __init__(self, tickers, weights):
        super().__init__(tickers)
        total = sum(weights.values())
        self.weights = {t: w / total for t, w in weights.items()}
        self.name = "FixedWeight(" + ", ".join(
            f"{t}:{w:.0%}" for t, w in self.weights.items()
        ) + ")"

    def get_weights(self, prices, as_of):
        return self.weights.copy()


STRATEGY_CLASS = lambda tickers: _FixedWeight(tickers, {"TQQQ": 0.55, "TMF": 0.45})
RULE = RULES["monthly"]
