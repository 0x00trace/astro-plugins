---
id: AP-5
type: task
title: Test that a subagent can run the bundled prompt audit
status: todo
priority: high
owner: claude
created: 2026-11-15
parent: AP-2
---
The audit step depends on a subagent starting the bundled `claude-api` skill's `prompt-audit` (what `/doctor prompt-audit <path>` runs), and nobody has tried it. If it fails, decision 0001 changes before anything else gets built.

Done when a subagent started from a skill runs `claude-api` with `prompt-audit <path>` on `review-me/` and returns findings, shown in a capture.

## Subtasks
- [ ] Write a throwaway skill that starts the subagent
- [ ] Run it in a second session with `try-plugin`
- [ ] Run it again with `claude-api` turned off in `skillOverrides`, and note what happens
- [ ] Note the time and tokens it costs

## Log
- 2026-11-15 12:51 claude: created
