---
id: AP-10
type: task
title: Show the evidence for each edit
status: done
priority: medium
owner: claude
created: 2026-11-15
parent: AP-2
blocked_by: [AP-9]
---
Each numbered edit quotes the line as `file:line` and names the check or audit finding it fixes. After the edits, one "Checked" line gives the numbers, so a clean result reads as checked, not skipped.

Done when each edit quotes `file:line` and names its check, and a clean file's review ends with a "Checked" line such as "38 lines, 6 paths and 3 commands found, no conflicts with `~/.claude/CLAUDE.md`".

## Subtasks
- [x] Phase 4 text
- [x] Wording test

## Log
- 2026-11-15 12:51 claude: created
- 2026-11-15 13:25 claude: moved to in-progress
- 2026-11-15 13:25 claude: done subtask: Phase 4 text
- 2026-11-15 13:25 claude: done subtask: Wording test
- 2026-11-15 13:25 claude: Phase 4: each edit is headed with path:line and the check or audit finding it fixes, and each file gets a 'Checked' line with numbers (lines, paths, commands, imports, files compared) that names any check left failing. Live check in AP-12.
- 2026-11-15 13:25 claude: moved to done
