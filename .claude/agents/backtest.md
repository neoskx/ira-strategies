---
name: backtest
description: Runs one strategy backtest by index using the self-contained backtest agent. Saves the result JSON to data/results/. Spawned in parallel by the orchestrator — one instance per strategy.
model: claude-haiku-4-5-20251001
tools:
  - Bash
  - Read
---

Read `agents/backtest/agents/backtest.md` and follow the steps exactly.
