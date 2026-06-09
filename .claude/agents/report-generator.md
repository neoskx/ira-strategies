---
name: report-generator
description: Generates data/reports/index.html. Call with action=skeleton before backtests begin (creates live progress page). Call with action=finalize after all backtests complete (produces final ranked HTML report with auto-refresh removed).
model: claude-sonnet-4-6
tools:
  - Read
  - Bash
  - Write
---

Read `agents/report-generator/agents/report-generator.md` and follow the instructions exactly.
