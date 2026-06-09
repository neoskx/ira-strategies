# IRA Strategies — Agent Conventions

This is the canonical reference for all AI agents working on this project.
All agents (Claude Code, Codex CLI, Cursor, Windsurf, Copilot, etc.) must follow these rules.

## Multi-Agent System

This project uses a 6-agent system for 401k strategy optimization. The agents are defined in:
- `agents/*/agents/*.md` — canonical system prompts (agent-neutral, human-editable)
- `.claude/agents/*.md` — Claude Code subagent wrappers
- `.codex/agents/*.toml` — Codex CLI subagent wrappers

| Agent | File | Role |
|---|---|---|
| `orchestration` | `agents/orchestration/` | Entry point; coordinates all other agents |
| `personal-config` | `agents/personal-config/` | Reads/writes `data/user_profile.yaml` |
| `strategy` | `agents/strategy/` | Selects + generates strategies by user constraints |
| `data-retriever` | `agents/data-retriever/` | Ensures price cache is fresh |
| `backtest` | `agents/backtest/` | Runs one strategy; updates live HTML |
| `report-generator` | `agents/report-generator/` | Creates and finalizes `data/reports/index.html` |

**To run:** In Claude Code say "build 401k strategies for [my profile]" or use `/find-best`.
In Codex CLI, address the `orchestration` agent by name.

### Shared State

Most runtime state is gitignored under `data/`. The exception is
`data/reports/`, which contains the committed static report for GitHub Pages.

- `data/user_profile.yaml` — user's retirement profile
- `data/results/*.json` — one JSON file per completed backtest
- `data/prices.pkl` — yfinance price cache
- `data/reports/index.html` — generated final report, committed for publishing

### Agent self-containment principle

Each agent is a deployable unit with its own script, prompt, and dependency manifest.
Agents must not rely on importing Python modules from the project root through relative
filesystem paths such as `sys.path.insert(...)`, `from main import ...`,
`from engine...`, `from strategies...`, `from rebalancing...`, or `from report...`.

Agents communicate through explicit inputs/outputs and shared state in `data/`, not by
cross-importing implementation code from another agent or from repository-root modules.
This is an intentional trade-off: duplicated code inside an agent is acceptable when it keeps the
agent independently runnable and testable.

If code truly needs to be shared across agents, extract it into a real versioned package
with a declared dependency in each agent's `requirements.txt` or `package.json`. Do not
share code by reaching across the repository filesystem.

### Modifying agents
Edit the canonical file in `agents/*/agents/*.md`. The `.claude/` and `.codex/` wrappers reference these files — they do not need to be updated unless the tool list or model changes.

---

## Project Purpose

Backtesting and optimization tool for self-directed tax-advantaged retirement accounts
(Traditional IRA, Roth IRA, Solo 401k). Finds the best combination of allocation strategy
+ rebalancing rule based on historical data. Zero transaction cost assumption (appropriate
for these account types).

## Vibe Coding Policy

All code in this repository is AI-generated (vibe coded). Never manually write code.
All changes go through AI agents. This means:
- Every file has a clear single responsibility
- No clever tricks — clarity over brevity
- Every new executable strategy must live in the owning agent, currently
  `agents/backtest/backtest_core.py`
- Every new strategy metadata entry must be represented in
  `agents/strategy/strategy_catalog.py`

## Architecture Overview

```
agents/
  orchestration/            ← workflow coordinator
  personal-config/          ← profile reader/writer
  strategy/                 ← self-contained strategy catalog + filter logic
  data-retriever/           ← self-contained yfinance cache manager
  backtest/                 ← self-contained executable backtesting core
  report-generator/         <- self-contained HTML report generator
data/reports/index.html     <- generated final report, committed for Pages
data/                       <- runtime state; reports subdirectory is tracked
```

## Golden Rules

1. **Read before write** — always read the file before editing it.
2. **One responsibility per file** — don't collapse modules.
3. **No personal data** — this repo is intended to go public. Never hardcode names,
   account numbers, portfolio values, or any personal financial information.
4. **Tests are truth** — agent changes must pass the relevant `python agents/...` or
   `node agents/...` script, plus the orchestrator dry run when workflow behavior changes.
5. **Reports are generated** — never manually edit `data/reports/index.html`.
   They are overwritten by `agents/report-generator/generate_report.js`.

## How to Add a New Strategy

- Add strategy metadata to `agents/strategy/strategy_catalog.py`.
- Add executable strategy logic to `agents/backtest/backtest_core.py`.
- Add the executable strategy instance to `build_strategies()` in
  `agents/backtest/backtest_core.py`.
- Keep the catalog index order synchronized with `build_strategies()`.
- Validate with `python agents/strategy/select_strategies.py list --json` and a targeted
  `python agents/backtest/run_backtest.py --index N --total 1 --json`.

## How to Add Assets

Add the ticker to the local asset lists in the agents that need it:
- `agents/backtest/backtest_core.py`
- `agents/strategy/strategy_catalog.py`
- `agents/data-retriever/fetch_data.py`

## Rebalancing Rules

Defined inside `agents/backtest/backtest_core.py`. Keep them local to the backtest
agent unless they are extracted into a real package dependency.

## Running Locally

```bash
pip install -r agents/personal-config/requirements.txt
pip install -r agents/strategy/requirements.txt
pip install -r agents/data-retriever/requirements.txt
pip install -r agents/backtest/requirements.txt
pip install -r agents/orchestration/requirements.txt
python agents/orchestration/orchestrate.py run --dry-run
python agents/orchestration/orchestrate.py run
```

## Metrics

Metrics are computed in `agents/backtest/backtest_core.py::compute_metrics()`.
Add new metrics there and ensure `agents/report-generator/generate_report.js`
handles the new JSON field.

## Report

`agents/report-generator/generate_report.js` builds `data/reports/index.html` from
`data/results/*.json`.

## GitHub Actions

The workflow in `.github/workflows/pages.yml`:
- Runs on pushes to `main` that change `data/reports/**`
- Can be triggered manually
- Publishes `data/reports/` to GitHub Pages
- Does not run backtests

Backtests are local/agent-driven because they depend on user profile state,
network data freshness, and agent orchestration. Commit `data/reports/index.html`
after a trusted local run, then the Pages workflow publishes it.

## Key Design Decisions

- **Agent-only execution**: users run the project through Claude Code, Codex, or the
  orchestration script.
- **Self-contained agents**: agents may duplicate code to remain deployable units.
- **No filesystem coupling**: shared code must become a versioned package dependency.
- **No look-ahead bias**: backtest strategies only use prices up to `as_of`.
- **Zero cost assumption**: Appropriate for IRA/Roth IRA. Do not add transaction costs
  without making it a configuration option.
- **GitHub Pages**: Report is a single `data/reports/index.html`.

## Dependency Management

Add new Python packages to the owning agent's `requirements.txt`. Add JavaScript
packages to the owning agent's `package.json`. Use `>=` version pins for Python,
not `==`. Do not add packages without a clear reason — keep each agent dependency
list minimal.

## Future Features (v2)

- Robinhood API integration (robin-stocks) for automated signal execution
- Monte Carlo simulation for forward-looking return distributions
- Multi-objective optimization (Pareto frontier of return vs drawdown)
- Walk-forward validation to avoid overfitting
- Support for options strategies (covered calls on ETF positions)
