Run the `orchestration` subagent to find the best 401k strategies.

The orchestration agent will:
1. Load your saved profile from data/user_profile.yaml
2. Ask about any missing fields (age, risk tolerance, account type)
3. Select and optionally generate strategies for your constraints
4. Run all backtests in parallel
5. Generate docs/index.html with ranked results

Pass any context upfront: "Find the best strategies for my 401k. I am 40, moderate risk."
