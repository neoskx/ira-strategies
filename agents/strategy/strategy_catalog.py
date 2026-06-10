"""Self-contained strategy catalog for the strategy agent.

Strategies are discovered from two directories:
  1. agents/backtest/strategies/  — built-in library (numbered for ordering)
  2. data/strategies/             — user-generated (sorted alphabetically)

METADATA is read via ast.literal_eval — no code is executed during discovery,
so catalog loading works without any runtime dependencies.
"""
import ast
from pathlib import Path

TICKERS = [
    "QQQ", "VOO", "SPY", "VTI", "VXUS", "EEM", "IWM",
    "SPMO", "SCHG", "VBR",
    "VGT", "SOXX", "XLE", "XLV", "XLF",
    "TQQQ", "UPRO", "TMF",
    "GLD", "VNQ", "DBC", "BTC-USD",
    "BND", "HYG", "TIP", "TLT", "SHY",
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL",
]

_STRATEGIES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "strategies"


def _read_metadata_from_dir(strategies_dir: Path) -> list[dict]:
    """Extract METADATA from strategy.py in each subdirectory using AST — no execution."""
    if not strategies_dir.exists():
        return []
    entries = []
    for subdir in sorted(d for d in strategies_dir.iterdir() if d.is_dir()):
        py_files = sorted(subdir.glob("*.py"))
        if not py_files:
            continue
        try:
            tree = ast.parse(py_files[0].read_text())
            for node in ast.walk(tree):
                if (isinstance(node, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == "METADATA"
                                for t in node.targets)):
                    entries.append(ast.literal_eval(node.value))
                    break
        except Exception:
            pass
    return entries


def load_all_strategies() -> list[dict]:
    return [
        {
            "index": i,
            "label": m["label"],
            "strategy_name": m["name"],
            "rule_name": f"Calendar({m['rebalance_rule']})",
            "suitable_for": m["suitable_for"],
        }
        for i, m in enumerate(_read_metadata_from_dir(_STRATEGIES_DIR))
    ]
