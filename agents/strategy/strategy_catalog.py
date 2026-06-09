"""Self-contained strategy catalog for the strategy agent."""

TICKERS = [
    "QQQ", "VOO", "VTI", "VXUS", "SPMO", "SCHG", "VBR", "VGT", "SOXX",
    "TQQQ", "UPRO", "TMF", "GLD", "VNQ", "BTC-USD", "BND", "TLT", "SHY",
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL",
]


def load_all_strategies() -> list[dict]:
    entries = [
        ("FixedWeight(QQQ:60%, SPMO:40%)", "Calendar(annual)", fixed_weight_suitability({"QQQ": 0.60, "SPMO": 0.40})),
        ("FixedWeight(QQQ:40%, SPMO:25%, VTI:25%, VXUS:10%)", "Calendar(annual)", fixed_weight_suitability({"QQQ": 0.40, "SPMO": 0.25, "VTI": 0.25, "VXUS": 0.10})),
        ("FixedWeight(TQQQ:55%, TMF:45%)", "Calendar(monthly)", fixed_weight_suitability({"TQQQ": 0.55, "TMF": 0.45})),
        ("FixedWeight(QQQ:100%)", "Calendar(annual)", fixed_weight_suitability({"QQQ": 1.0})),
        ("FixedWeight(VOO:100%)", "Calendar(annual)", fixed_weight_suitability({"VOO": 1.0})),
        ("FixedWeight(VTI:60%, BND:40%)", "Calendar(annual)", fixed_weight_suitability({"VTI": 0.60, "BND": 0.40})),
        ("FixedWeight(VTI:60%, VXUS:30%, BND:10%)", "Calendar(annual)", fixed_weight_suitability({"VTI": 0.60, "VXUS": 0.30, "BND": 0.10})),
        ("EqualWeight(23 assets)", "Calendar(monthly)", {
            "min_horizon_years": 10,
            "risk_tolerance": ["moderate", "aggressive"],
            "asset_types": ["ETF"],
            "max_drawdown_tolerance": -0.45,
            "notes": "1/N diversification across all assets. No market view required.",
        }),
        ("MomentumRotation(top3, 12m)", "Calendar(monthly)", momentum_suitability()),
        ("MomentumRotation(top5, 12m)", "Calendar(monthly)", momentum_suitability()),
        ("DualMomentum(12m)", "Calendar(monthly)", {
            "min_horizon_years": 10,
            "risk_tolerance": ["moderate", "aggressive"],
            "asset_types": ["ETF"],
            "max_drawdown_tolerance": -0.40,
            "notes": "Defensive: switches to bonds in downtrends. Lower drawdown than pure equity.",
        }),
        ("TrendFollowing(200d MA)", "Calendar(monthly)", {
            "min_horizon_years": 10,
            "risk_tolerance": ["moderate"],
            "asset_types": ["ETF"],
            "max_drawdown_tolerance": -0.35,
            "notes": "Moving average filter reduces crash exposure. May lag in fast recoveries.",
        }),
        ("MaxSharpe(36m lookback)", "Calendar(quarterly)", {
            "min_horizon_years": 15,
            "risk_tolerance": ["moderate", "aggressive"],
            "asset_types": ["ETF"],
            "max_drawdown_tolerance": -0.50,
            "notes": "Model-dependent. Works best with 8+ uncorrelated assets in the universe.",
        }),
        ("MinVariance(36m lookback)", "Calendar(quarterly)", {
            "min_horizon_years": 5,
            "risk_tolerance": ["conservative", "moderate"],
            "asset_types": ["ETF"],
            "max_drawdown_tolerance": -0.25,
            "notes": "Capital preservation first. Lower returns but very low drawdowns.",
        }),
        ("RiskParity(3m vol)", "Calendar(monthly)", {
            "min_horizon_years": 10,
            "risk_tolerance": ["conservative", "moderate"],
            "asset_types": ["ETF"],
            "max_drawdown_tolerance": -0.30,
            "notes": "Bridgewater All-Weather style. High Sharpe ratio, lower absolute returns.",
        }),
        ("AdaptiveAA(top3, 12m mom, 3m vol)", "Calendar(monthly)", adaptive_suitability()),
        ("AdaptiveAA(top5, 12m mom, 3m vol)", "Calendar(monthly)", adaptive_suitability()),
    ]
    return [
        {
            "index": index,
            "label": f"{strategy_name} | {rule_name}",
            "strategy_name": strategy_name,
            "rule_name": rule_name,
            "suitable_for": suitable_for,
        }
        for index, (strategy_name, rule_name, suitable_for) in enumerate(entries)
    ]


def fixed_weight_suitability(weights: dict[str, float]) -> dict:
    leveraged = {"TQQQ", "TMF", "UPRO", "SSO", "SOXL", "SPXL"}
    equity = {"QQQ", "VOO", "VTI", "SPY", "SPMO", "VGT", "TQQQ", "UPRO", "VXUS", "VEA", "VWO"}
    has_leveraged = any(ticker in leveraged for ticker in weights)
    equity_weight = sum(weight for ticker, weight in weights.items() if ticker in equity)
    if has_leveraged:
        return {
            "min_horizon_years": 20, "risk_tolerance": ["aggressive"],
            "asset_types": ["ETF"], "max_drawdown_tolerance": -0.70,
            "notes": "Leveraged. Only suitable for investors with 20+ year horizon.",
        }
    if equity_weight >= 0.80:
        return {
            "min_horizon_years": 15, "risk_tolerance": ["aggressive"],
            "asset_types": ["ETF"], "max_drawdown_tolerance": -0.50,
            "notes": "Equity-heavy. High growth potential with significant drawdown risk.",
        }
    if equity_weight >= 0.50:
        return {
            "min_horizon_years": 10, "risk_tolerance": ["moderate", "aggressive"],
            "asset_types": ["ETF"], "max_drawdown_tolerance": -0.40,
            "notes": "Balanced equity/bond blend. Suitable for 10+ year horizon.",
        }
    return {
        "min_horizon_years": 5, "risk_tolerance": ["conservative", "moderate"],
        "asset_types": ["ETF"], "max_drawdown_tolerance": -0.25,
        "notes": "Conservative allocation. Prioritizes capital preservation.",
    }


def momentum_suitability() -> dict:
    return {
        "min_horizon_years": 10,
        "risk_tolerance": ["moderate", "aggressive"],
        "asset_types": ["ETF"],
        "max_drawdown_tolerance": -0.55,
        "notes": "Signal-driven rotation. Can underperform in choppy sideways markets.",
    }


def adaptive_suitability() -> dict:
    return {
        "min_horizon_years": 10,
        "risk_tolerance": ["moderate", "aggressive"],
        "asset_types": ["ETF"],
        "max_drawdown_tolerance": -0.45,
        "notes": "Combines momentum filter with risk parity sizing. Research-backed, high Sharpe.",
    }
