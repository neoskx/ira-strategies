---
name: data-retriever
description: Checks whether price data for all tickers in the universe is cached in data/prices.pkl. Downloads missing or stale data. Returns cache status (hit/refreshed/partial/failed) before backtests run.
model: claude-haiku-4-5-20251001
tools:
  - Read
  - Bash
---

Read `agents/data-retriever/agents/data-retriever.md` and follow the steps exactly.
