---
name: personal-config
description: Reads and writes the user's retirement profile in data/user_profile.yaml. Call with action=read to load the saved profile. Call with action=write and a dict of fields to update and persist. Never deletes existing fields.
model: claude-haiku-4-5-20251001
tools:
  - Read
  - Write
  - Bash
---

Read `agents/personal-config/agents/personal-config.md` and follow the instructions exactly.
