# IRA Strategies — Claude Code

Read `AGENTS.md` for full architecture and conventions. This file covers Claude Code-specific setup and quick-start.

## Prerequisites

```bash
# Python 3.10+
pip install -r requirements.txt

# Node.js 18+ (for the report generator — no npm install needed)
node --version
```

## Quick start

Just ask:
```
Find the best strategies for my 401k.
```
or use the slash command:
```
/find-best
```

The orchestration agent handles everything: profile, strategy selection, optional custom strategy build, backtests, and report.

## Key rules

- **Vibe-coded** — all changes go through agents, never hand-edited files.
- **Strategies** live in `data/strategies/<name>/` — two files each: `strategy.md` (spec) and `strategy.py` (implementation). Add new ones with `/build-strategy`.
- **`backtest_core.py`** contains only the abstract base class and infrastructure — no strategy implementations.
- **`data/reports/index.html`** is auto-generated — never edit it directly.
- **No personal data in source** — this repo is public. User profile stays in gitignored `data/user_profile.yaml`.

## Slash commands

| Command | What it does |
|---|---|
| `/find-best` | Full interactive workflow — profile → strategies → optional build → backtests → report |
| `/build-strategy` | Build and test a single new custom strategy |

## Validation

```bash
python agents/strategy/select_strategies.py list --json
python agents/backtest/run_backtest.py --index 5 --total 1 --json
python agents/orchestration/orchestrate.py run --dry-run
```
