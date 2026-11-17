---
id: AP-31
type: task
title: Release plain-english 0.2.0 and update the installed plugin
status: done
priority: medium
owner: claude
created: 2026-11-16
parent: AP-28
labels: [plain-english]
blocked_by: [AP-30]
---
Skipped if AP-30 reverts the rewrite.

Done when the PR is merged, the installed copy reports 0.2.0, and a try-plugin capture shows the new rule working.

## Subtasks
- [x] Update the README and descriptions if they no longer fit
- [x] Release commit, then merge
- [x] Update the installed copy and confirm its version

## Log
- 2026-11-16 18:09 claude: created
- 2026-11-16 18:45 claude: moved to in-progress
- 2026-11-16 18:47 claude: try-plugin, Opus 5.5, on a copy of the release fixture: 'Can we merge #33 today?' got a reply naming test_write_receipt, tests/test_cart.py line 44 and the CI log, with 'T-14 can't start until #33 merges' and no stand-in words. An Explore subagent quoted the first sentence of Name things, and its transcript has the section in its SubagentStart context.
- 2026-11-16 18:47 claude: done subtask: Update the README and descriptions if they no longer fit
- 2026-11-16 18:47 claude: done subtask: Release commit, then merge
- 2026-11-16 18:47 claude: done subtask: Update the installed copy and confirm its version
- 2026-11-16 18:47 claude: The installed plain-english@astro-plugins reads from this checkout and reports 0.2.0 (0.1.0 before the release).
- 2026-11-16 18:47 claude: moved to done
