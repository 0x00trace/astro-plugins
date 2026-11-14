---
id: AP-19
type: task
title: "Merge bug-hunt's evals and its short-run fix (PR #114)"
status: done
priority: medium
owner: claude
created: 2026-11-15
labels: [bug-hunt]
---
PR #114 adds four `claude plugin eval` cases for bug-hunt, the fix they turned up (keep the run file on a short run so its repros survive) and release 0.1.2. It sat open since 2026-11-14; the user asked to merge it.

## Subtasks
- [x] Rebase onto main and resolve conflicts
- [x] Run the formatter, linter, tests and validate
- [x] Run one eval case on the rebased branch
- [x] Merge and update the installed copy

## Log
- 2026-11-15 16:17 claude: created
- 2026-11-15 16:17 claude: moved to in-progress
- 2026-11-15 16:17 claude: done subtask: Rebase onto main and resolve conflicts
- 2026-11-15 16:17 claude: done subtask: Run the formatter, linter, tests and validate
- 2026-11-15 16:19 claude: Rebased onto main with no conflicts. confirm-findings eval, 1 run: score 1.00, all 8 graders incl. run-file, 74s, $0.45
- 2026-11-15 16:19 claude: done subtask: Run one eval case on the rebased branch
- 2026-11-15 16:19 claude: done subtask: Merge and update the installed copy
- 2026-11-15 16:19 claude: moved to done
