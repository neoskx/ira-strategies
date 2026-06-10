# Runtime deps injected: Strategy, RULES, pd, np
METADATA = {
    "name": "FixedWeight(QQQ:40%, SPMO:25%, VTI:25%, VXUS:10%)",
    "label": "FixedWeight(QQQ:40%, SPMO:25%, VTI:25%, VXUS:10%) | Calendar(annual)",
    "rebalance_rule": "annual",
    "suitable_for": {
        "min_horizon_years": 15, "risk_tolerance": ["aggressive"],
        "asset_types": ["ETF"], "max_drawdown_tolerance": -0.50,
        "notes": "Diversified equity blend with momentum and global exposure.",
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


STRATEGY_CLASS = lambda tickers: _FixedWeight(tickers, {"QQQ": 0.40, "SPMO": 0.25, "VTI": 0.25, "VXUS": 0.10})
RULE = RULES["annual"]
