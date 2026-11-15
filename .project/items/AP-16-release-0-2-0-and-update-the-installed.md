---
id: AP-16
type: task
title: Release 0.2.0 and update the installed plugin
status: todo
priority: medium
owner: claude
created: 2026-11-15
parent: AP-3
blocked_by: [AP-14, AP-15]
---
Ship the change and bring the installed copy up to date with the `ship-release` skill.

Done when the PR is merged after CI passes and the installed plugin reports 0.2.0.

## Subtasks
- [ ] `chore(instructions): release 0.2.0 so …` commit
- [ ] PR titled as a Conventional Commit
- [ ] Merge, delete the branch, pull main
- [ ] Update the installed plugin and confirm it reports 0.2.0

## Log
- 2026-11-15 12:51 claude: created
