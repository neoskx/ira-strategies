---
name: strategy
description: Selects strategies from the library that match the user's 401k profile constraints (age, risk tolerance, drawdown tolerance, horizon). Generates new strategy code for any identified gaps. Returns the full indexed list of strategies to backtest.
model: claude-sonnet-4-6
tools:
  - Read
  - Write
  - Bash
---

Read `agents/strategy/agents/strategy.md` and follow the workflow exactly.
