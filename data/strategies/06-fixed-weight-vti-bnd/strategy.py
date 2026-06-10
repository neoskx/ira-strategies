# Runtime deps injected: Strategy, RULES, pd, np
METADATA = {
    "name": "FixedWeight(VTI:60%, BND:40%)",
    "label": "FixedWeight(VTI:60%, BND:40%) | Calendar(annual)",
    "rebalance_rule": "annual",
    "suitable_for": {
        "min_horizon_years": 10, "risk_tolerance": ["moderate", "aggressive"],
        "asset_types": ["ETF"], "max_drawdown_tolerance": -0.40,
        "notes": "Classic 60/40. Balanced equity/bond blend for 10+ year horizon.",
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


STRATEGY_CLASS = lambda tickers: _FixedWeight(tickers, {"VTI": 0.60, "BND": 0.40})
RULE = RULES["annual"]
