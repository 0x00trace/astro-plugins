---
id: AP-8
type: task
title: Run the prompt audit during the review
status: todo
priority: medium
owner: claude
created: 2026-11-15
parent: AP-2
blocked_by: [AP-5]
---
In Phase 2, next to the surveys, a subagent runs the bundled prompt audit on each file under review and sends back its findings, which become numbered edits in Phase 4. See decision 0001.

Done when a review shows the audit's findings as numbered edits, and with `claude-api` turned off it says so in one line and goes on with the check list.

## Subtasks
- [ ] Phase 2 subagent text
- [ ] Merge the findings into Phase 4's edits
- [ ] Fallback line for when `claude-api` is off
- [ ] Wording test

## Log
- 2026-11-15 12:51 claude: created
