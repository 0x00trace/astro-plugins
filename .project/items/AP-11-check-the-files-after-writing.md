---
id: AP-11
type: task
title: Check the files after writing
status: done
priority: medium
owner: claude
created: 2026-11-15
parent: AP-2
---
Phase 5 re-reads each written file and confirms its line count, imports and named paths, then tells the user to run `/context all` and look under Memory files, the docs' own way to confirm a file loaded.

Done when, after writing, the reply gives each file's line count and the imports and paths it checked, then the `/context all` step.

## Subtasks
- [x] Phase 5 text
- [x] Phase 8 text
- [x] Wording test

## Log
- 2026-11-15 12:51 claude: created
- 2026-11-15 13:25 claude: moved to in-progress
- 2026-11-15 13:25 claude: done subtask: Phase 5 text
- 2026-11-15 13:25 claude: done subtask: Phase 8 text
- 2026-11-15 13:25 claude: done subtask: Wording test
- 2026-11-15 13:25 claude: Phase 5 reads each written file back and checks its line count, imports and named paths. Phase 8 reports them and tells the user to start a new session and run /context all. Live check: AP-12's review-me run replies 'write it' on the scratch copy.
- 2026-11-15 13:25 claude: moved to done
