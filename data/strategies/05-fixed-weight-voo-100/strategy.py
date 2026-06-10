# Runtime deps injected: Strategy, RULES, pd, np
METADATA = {
    "name": "FixedWeight(VOO:100%)",
    "label": "FixedWeight(VOO:100%) | Calendar(annual)",
    "rebalance_rule": "annual",
    "suitable_for": {
        "min_horizon_years": 15, "risk_tolerance": ["aggressive"],
        "asset_types": ["ETF"], "max_drawdown_tolerance": -0.50,
        "notes": "100% S&P 500. The classic buy-and-hold benchmark.",
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


STRATEGY_CLASS = lambda tickers: _FixedWeight(tickers, {"VOO": 1.0})
RULE = RULES["annual"]
