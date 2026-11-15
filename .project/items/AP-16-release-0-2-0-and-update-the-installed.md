---
id: AP-16
type: task
title: Release 0.2.0 and update the installed plugin
status: done
priority: medium
owner: claude
created: 2026-11-15
parent: AP-3
blocked_by: [AP-14, AP-15]
---
Ship the change and bring the installed copy up to date with the `ship-release` skill.

Done when the PR is merged after CI passes and the installed plugin reports 0.2.0.

## Subtasks
- [x] `chore(instructions): release 0.2.0 so …` commit
- [x] PR titled as a Conventional Commit
- [x] Merge, delete the branch, pull main
- [x] Update the installed plugin and confirm it reports 0.2.0

## Log
- 2026-11-15 12:51 claude: created
- 2026-11-15 13:51 claude: moved to in-progress
- 2026-11-15 13:51 claude: done subtask: `chore(instructions): release 0.2.0 so …` commit
- 2026-11-15 13:51 claude: done subtask: PR titled as a Conventional Commit
- 2026-11-15 13:51 claude: done subtask: Merge, delete the branch, pull main
- 2026-11-15 13:51 claude: done subtask: Update the installed plugin and confirm it reports 0.2.0
- 2026-11-15 13:51 claude: Release commit marks the release released and AP-16 and AP-3 done before the merge, so main gets no board-only commit. Installed plugin checked right after the merge.
- 2026-11-15 13:51 claude: moved to done
