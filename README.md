# IRA Strategies

Agent-driven 401k strategy optimization for self-directed retirement accounts.

This repo is intended to be run through Claude Code or Codex. Each agent is
self-contained: it owns the code it executes and communicates through `data/`
artifacts instead of importing shared repo modules.

## Run

In Claude Code:

```text
/find-best
```

Or ask:

```text
Build 401k strategies for my profile.
```

In Codex, address the orchestration agent:

```text
Have orchestration build 401k strategies for a 40-year-old with moderate risk.
```

CLI fallback:

```bash
python agents/orchestration/orchestrate.py run
```

The workflow writes:

- `data/user_profile.yaml` - retirement profile
- `data/prices.pkl` - yfinance cache
- `data/results/*.json` - one result per completed backtest
- `docs/index.html` - generated report

## Architecture

This project uses an agent-first architecture.

Agents are the microservices. Each agent owns its runtime, prompt, script,
dependencies, and local implementation details. An agent should be independently
runnable and replaceable.

Skills are the packages. When behavior needs to be reused across agents, package it
as a skill or versioned dependency and declare it in the agents that consume it.
Do not share behavior by importing files across agent directories or from the repo
root.

```mermaid
flowchart TD
    user[Claude Code / Codex] --> orchestration[orchestration agent]

    orchestration --> personal[personal-config agent]
    orchestration --> strategy[strategy agent]
    orchestration --> data[data-retriever agent]
    orchestration --> backtest[backtest agent]
    orchestration --> report[report-generator agent]

    personal --> profile[(data/user_profile.yaml)]
    strategy --> selected[(selected strategy list)]
    data --> prices[(data/prices.pkl)]
    backtest --> results[(data/results/*.json)]
    report --> docs[(docs/index.html)]

    skills{{Skills / Packages}} -. shared behavior .-> personal
    skills -. shared behavior .-> strategy
    skills -. shared behavior .-> data
    skills -. shared behavior .-> backtest
    skills -. shared behavior .-> report

    classDef agent fill:#eef6ff,stroke:#2563eb,stroke-width:1px,color:#111827;
    classDef artifact fill:#f8fafc,stroke:#64748b,stroke-width:1px,color:#111827;
    classDef skill fill:#ecfdf5,stroke:#059669,stroke-width:1px,color:#111827;

    class orchestration,personal,strategy,data,backtest,report agent;
    class profile,selected,prices,results,docs artifact;
    class skills skill;
```

The only cross-agent contract is explicit data:

- CLI arguments
- process stdout/stderr
- files under `data/`
- generated report output under `docs/`

## Agents

| Agent | Role |
|---|---|
| `orchestration` | Coordinates the full workflow |
| `personal-config` | Reads/writes `data/user_profile.yaml` |
| `strategy` | Selects strategy candidates from its local catalog |
| `data-retriever` | Ensures yfinance price cache is available |
| `backtest` | Runs one strategy using its local backtesting core |
| `report-generator` | Builds `docs/index.html` from result JSON |

## Self-Containment Rule

Agents must not import implementation modules from the repo root or from sibling
agents. If logic must be shared, promote it into a skill/package and consume that
package from each agent. Duplicating code inside an agent is acceptable when it
preserves independent execution.

## Validation

```bash
python agents/strategy/select_strategies.py filter --profile data/user_profile.yaml
python agents/data-retriever/fetch_data.py check
python agents/backtest/run_backtest.py --index 5 --total 1 --json
node agents/report-generator/generate_report.js --results-dir data/results --total 1
python agents/orchestration/orchestrate.py run --dry-run
python agents/orchestration/orchestrate.py run
```

## Disclaimer

Backtests are hypothetical and based on historical data. Past performance does not
guarantee future results. This is an educational research tool, not financial advice.
