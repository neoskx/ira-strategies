#!/usr/bin/env python3
"""
Orchestration agent — runs the full 401k strategy optimization workflow.

Can be used standalone (no AI) or invoked step-by-step by the orchestration AI agent.

Usage:
  python orchestrate.py profile                    # show saved user profile
  python orchestrate.py check-data                 # check price cache
  python orchestrate.py strategies                 # list filtered strategies
  python orchestrate.py run [--workers N]          # run full workflow
  python orchestrate.py run --dry-run              # show plan without running
"""
import sys
import os
import json
import argparse
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
AGENTS_DIR = PROJECT_ROOT / "agents"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
REPORT_OUTPUT = PROJECT_ROOT / "data" / "reports" / "index.html"


def _py(agent: str, script: str, *args) -> subprocess.CompletedProcess:
    """Run a Python agent script."""
    return subprocess.run(
        [sys.executable, str(AGENTS_DIR / agent / script), *args],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )


def _node(agent: str, script: str, *args) -> subprocess.CompletedProcess:
    """Run a Node.js agent script."""
    return subprocess.run(
        ["node", str(AGENTS_DIR / agent / script), *args],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )


def cmd_profile(_args):
    r = _py("personal-config", "personal_config.py", "read")
    print(r.stdout or r.stderr)


def cmd_check_data(_args):
    r = _py("data-retriever", "fetch_data.py", "check")
    print(r.stdout or r.stderr)


def cmd_strategies(_args):
    profile_path = str(DATA_DIR / "user_profile.yaml")
    r = _py("strategy", "select_strategies.py", "filter", "--profile", profile_path)
    print(r.stdout or r.stderr)


def cmd_run(args):
    print("=" * 60)
    print("  401k Strategy Optimization")
    print("=" * 60)

    # ── Step 1: profile ──────────────────────────────────────────
    print("\n[1/5] Loading user profile...")
    r = _py("personal-config", "personal_config.py", "read", "--json")
    if r.returncode != 0:
        print(f"  Error: {r.stderr}", file=sys.stderr)
        sys.exit(1)
    profile = json.loads(r.stdout)
    p = profile.get("personal", {})
    print(f"  age={p.get('age')}  risk={p.get('risk_tolerance')}  "
          f"horizon={p.get('years_to_retirement')}yr  account={p.get('account_type')}")

    # ── Step 2: data ─────────────────────────────────────────────
    print("\n[2/5] Checking price data...")
    r = _py("data-retriever", "fetch_data.py", "check", "--json")
    status = json.loads(r.stdout) if r.returncode == 0 else {"status": "unknown"}
    if status["status"] in ("miss", "stale", "partial"):
        print(f"  Status: {status['status']} — refreshing...")
        r2 = _py("data-retriever", "fetch_data.py", "refresh")
        print(f"  {r2.stdout.strip()}")
        if r2.returncode != 0:
            print(f"  Error: {r2.stderr}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"  Cache OK — {len(status.get('tickers', []))} tickers, "
              f"{status.get('start')} → {status.get('end')}")

    # ── Step 3: strategies ────────────────────────────────────────
    print("\n[3/5] Selecting strategies...")
    profile_path = str(DATA_DIR / "user_profile.yaml")
    r = _py("strategy", "select_strategies.py", "filter", "--profile", profile_path, "--json")
    if r.returncode != 0 or not r.stdout.strip():
        r = _py("strategy", "select_strategies.py", "list", "--json")
    strategies = json.loads(r.stdout)
    total = len(strategies)
    print(f"  {total} strategies selected")
    for s in strategies:
        print(f"    [{s['index']:2d}] {s['label']}")

    if args.dry_run:
        print("\n  [dry-run] Stopping before backtests.")
        return

    # ── Step 4: backtests (parallel) ─────────────────────────────
    sys_workers = profile.get("system", {}).get("max_parallel_backtests")
    workers = args.workers or sys_workers or max(1, (os.cpu_count() or 4) - 1)
    workers = min(int(workers), 8, total)
    print(f"\n[4/5] Running {total} backtests ({workers} parallel workers)...")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for result_file in RESULTS_DIR.glob("*.json"):
        result_file.unlink()

    # Skeleton report
    _node("report-generator", "generate_report.js",
          "--results-dir", str(RESULTS_DIR),
          "--total", str(total),
          "--output", str(REPORT_OUTPUT))

    def backtest_one(s):
        r = _py("backtest", "run_backtest.py",
                "--index", str(s["index"]),
                "--total", str(total),
                "--results-dir", str(RESULTS_DIR),
                "--json")
        success = r.returncode == 0 and "CAGR=" in r.stdout
        # update live report after each result
        _node("report-generator", "generate_report.js",
              "--results-dir", str(RESULTS_DIR),
              "--total", str(total),
              "--output", str(REPORT_OUTPUT))
        return s["index"], success, r.stdout, r.stderr

    completed = 0
    failed = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(backtest_one, s): s for s in strategies}
        for future in as_completed(futures):
            idx, success, out, err = future.result()
            completed += 1
            for line in out.splitlines():
                if "CAGR=" in line:
                    print(f"  [{completed}/{total}] {line.strip()}")
            if not success:
                failed.append(idx)
                if err:
                    print(f"  [error] index={idx}: {err.strip()}", file=sys.stderr)

    # ── Step 5: final report ──────────────────────────────────────
    print("\n[5/5] Generating final report...")
    r = _node("report-generator", "generate_report.js",
              "--results-dir", str(RESULTS_DIR),
              "--total", str(total),
              "--final",
              "--output", str(REPORT_OUTPUT))
    print(f"  {r.stdout.strip()}")

    print(f"\n{'=' * 60}")
    print(f"  Done: {total - len(failed)}/{total} strategies succeeded")
    print(f"  Report: {REPORT_OUTPUT}")
    if failed:
        print(f"  Failed indices: {failed}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="401k strategy orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("profile", help="Show current user profile")
    sub.add_parser("check-data", help="Check price data cache")
    sub.add_parser("strategies", help="List filtered strategies")
    run_p = sub.add_parser("run", help="Run full optimization workflow")
    run_p.add_argument("--workers", type=int, help="Max parallel backtest workers")
    run_p.add_argument("--dry-run", action="store_true", help="Show plan only, no backtests")
    args = parser.parse_args()

    dispatch = {
        "profile": cmd_profile,
        "check-data": cmd_check_data,
        "strategies": cmd_strategies,
        "run": cmd_run,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
