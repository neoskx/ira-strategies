#!/usr/bin/env python3
"""
Personal config agent — manages data/user_profile.yaml.

Usage:
  python personal_config.py read [--path PATH] [--json]
  python personal_config.py write --updates '{"age": 40, "risk_tolerance": "moderate"}' [--path PATH]
  python personal_config.py validate [--path PATH]
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import date

import yaml

DEFAULT_PATH = Path("data/user_profile.yaml")

TEMPLATE = {
    "version": 1,
    "personal": {
        "age": None,
        "years_to_retirement": None,
        "risk_tolerance": None,
        "preferred_assets": [],
        "account_type": "401k",
    },
    "constraints": {
        "max_drawdown_tolerance": None,
        "investment_horizon": None,
        "excluded_tickers": [],
        "min_backtest_years": 10,
    },
    "system": {
        "max_parallel_backtests": None,
        "last_updated": None,
    },
}


def _infer_horizon(years_to_retirement):
    if years_to_retirement is None:
        return None
    if years_to_retirement < 10:
        return "short"
    if years_to_retirement <= 20:
        return "medium"
    return "long"


def read_profile(path: Path = DEFAULT_PATH) -> dict:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.dump(TEMPLATE, default_flow_style=False, sort_keys=False))
    return yaml.safe_load(path.read_text())


def write_profile(updates: dict, path: Path = DEFAULT_PATH) -> dict:
    profile = read_profile(path)

    flat_personal_keys = {"age", "years_to_retirement", "risk_tolerance", "preferred_assets", "account_type"}
    flat_constraint_keys = {"max_drawdown_tolerance", "investment_horizon", "excluded_tickers", "min_backtest_years"}

    for top_key in ("personal", "constraints", "system"):
        if top_key in updates:
            profile.setdefault(top_key, {}).update(updates[top_key])

    flat_personal = {k: v for k, v in updates.items() if k in flat_personal_keys}
    flat_constraints = {k: v for k, v in updates.items() if k in flat_constraint_keys}
    if flat_personal:
        profile.setdefault("personal", {}).update(flat_personal)
    if flat_constraints:
        profile.setdefault("constraints", {}).update(flat_constraints)

    years = profile.get("personal", {}).get("years_to_retirement")
    if years and not profile.get("constraints", {}).get("investment_horizon"):
        profile.setdefault("constraints", {})["investment_horizon"] = _infer_horizon(years)

    profile.setdefault("system", {})["last_updated"] = date.today().isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(profile, default_flow_style=False, sort_keys=False, allow_unicode=True))
    return profile


def validate_profile(profile: dict) -> list:
    missing = []
    p = profile.get("personal", {})
    if not p.get("age") and not p.get("years_to_retirement"):
        missing.append("age or years_to_retirement")
    if not p.get("risk_tolerance"):
        missing.append("risk_tolerance")
    if not p.get("account_type"):
        missing.append("account_type")
    return missing


def main():
    parser = argparse.ArgumentParser(description="Personal config manager")
    parser.add_argument("command", choices=["read", "write", "validate"])
    parser.add_argument("--path", default=str(DEFAULT_PATH))
    parser.add_argument("--updates", help="JSON string of fields to update (write only)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    path = Path(args.path)

    if args.command == "read":
        profile = read_profile(path)
        print(json.dumps(profile, indent=2) if args.json else yaml.dump(profile, default_flow_style=False))

    elif args.command == "write":
        if not args.updates:
            print("Error: --updates required", file=sys.stderr)
            sys.exit(1)
        updates = json.loads(args.updates)
        profile = write_profile(updates, path)
        missing = validate_profile(profile)
        print(f"Saved to {path}" + (f" — still missing: {', '.join(missing)}" if missing else " — profile complete"))
        if args.json:
            print(json.dumps(profile, indent=2))

    elif args.command == "validate":
        profile = read_profile(path)
        missing = validate_profile(profile)
        if missing:
            print(f"Missing: {', '.join(missing)}", file=sys.stderr)
            sys.exit(1)
        print("Profile is complete.")


if __name__ == "__main__":
    main()
