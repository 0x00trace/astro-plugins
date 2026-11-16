---
id: AP-20
type: task
title: Drop github-tracking, and make telling Claude how to work a non-goal
status: done
priority: high
owner: claude
created: 2026-11-16
labels: [marketplace]
---
github-tracking is going away: drop it from the marketplace and reword everything in this repo that names it, as if it never existed. Record in PROJECT.md that plugins say how their own tools work and what they need, not how Claude should work. The rules that came out of corkboard's skills now live in the global ~/.claude/CLAUDE.md (backup at ~/.claude/CLAUDE.md.bak).

Done when: plugins/github-tracking and its marketplace entry are gone, PROJECT.md names it only in the Decisions line that drops it, the new non-goal is in, and `claude plugin validate .` passes.

## Subtasks
- [x] Move the opinion rules to ~/.claude/CLAUDE.md (Tracking work, Docs, branch default)
- [x] Delete plugins/github-tracking and its marketplace entry
- [x] Reword PROJECT.md: list, problem, Decisions, Status
- [x] Add the non-goal and its Decisions line
- [x] Validate the marketplace and run every plugin's tests

## Log
- 2026-11-16 15:40 claude: created
- 2026-11-16 15:40 claude: moved to in-progress
- 2026-11-16 15:40 claude: done subtask: Move the opinion rules to ~/.claude/CLAUDE.md (Tracking work, Docs, branch default)
- 2026-11-16 15:40 claude: done subtask: Delete plugins/github-tracking and its marketplace entry
- 2026-11-16 15:40 claude: done subtask: Reword PROJECT.md: list, problem, Decisions, Status
- 2026-11-16 15:40 claude: done subtask: Add the non-goal and its Decisions line
- 2026-11-16 15:41 claude: done subtask: Validate the marketplace and run every plugin's tests
- 2026-11-16 16:03 claude: moved to done
