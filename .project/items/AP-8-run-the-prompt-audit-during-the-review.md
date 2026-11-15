---
id: AP-8
type: task
title: Run the prompt audit during the review
status: in-progress
priority: medium
owner: claude
created: 2026-11-15
parent: AP-2
blocked_by: [AP-5]
---
In Phase 2, next to the surveys, a subagent runs the bundled prompt audit on each file under review and sends back its findings, which become numbered edits in Phase 4. See decision 0001.

Done when a review shows the audit's findings as numbered edits, and with `claude-api` turned off it says so in one line and goes on with the check list.

## Subtasks
- [x] Phase 2 subagent text
- [x] Merge the findings into Phase 4's edits
- [x] Fallback line for when `claude-api` is off
- [x] Wording test

## Log
- 2026-11-15 12:51 claude: created
- 2026-11-15 13:22 claude: moved to in-progress
- 2026-11-15 13:23 claude: done subtask: Phase 2 subagent text
- 2026-11-15 13:23 claude: done subtask: Merge the findings into Phase 4's edits
- 2026-11-15 13:23 claude: done subtask: Fallback line for when `claude-api` is off
- 2026-11-15 13:23 claude: done subtask: Wording test
- 2026-11-15 13:23 claude: Phase 2 starts one audit subagent per file under review, with a brief that skips Step 7, rules out installs and running project code, and says not to look inside Claude Code's files (the spike spent most of its 11 minutes there). Added Skill(claude-api *) to allowed-tools: the docs give that syntax but don't say whether the grant reaches a subagent, and AP-12's run in default mode will show it. Stays open until a live run shows the findings as edits, and the off path's one-line notice.
- 2026-11-15 13:29 claude: Live: in the AP-12 run (default permission mode) the audit subagent called Skill(claude-api, 'prompt-audit <abs path>/CLAUDE.md') with no approval prompt, so the allowed-tools grant Skill(claude-api *) reaches a subagent the skill starts.
