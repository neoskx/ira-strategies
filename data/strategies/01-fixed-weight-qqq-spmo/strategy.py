# Runtime deps injected: Strategy, RULES, pd, np
METADATA = {
    "name": "FixedWeight(QQQ:60%, SPMO:40%)",
    "label": "FixedWeight(QQQ:60%, SPMO:40%) | Calendar(annual)",
    "rebalance_rule": "annual",
    "suitable_for": {
        "min_horizon_years": 15, "risk_tolerance": ["aggressive"],
        "asset_types": ["ETF"], "max_drawdown_tolerance": -0.50,
        "notes": "Equity-heavy. High growth potential with significant drawdown risk.",
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


STRATEGY_CLASS = lambda tickers: _FixedWeight(tickers, {"QQQ": 0.60, "SPMO": 0.40})
RULE = RULES["annual"]
