---
name: orchestration
description: Main entry point for 401k strategy optimization. Coordinates the full multi-agent workflow — profile loading, strategy selection, data retrieval, parallel backtests, and report generation. Use when the user asks to find, build, run, or optimize 401k strategies.
model: claude-opus-4-7
tools:
  - Read
  - Bash
---

Read `agents/orchestration/agents/orchestration.md` and follow the workflow exactly.
