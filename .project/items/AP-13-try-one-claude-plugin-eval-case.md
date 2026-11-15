---
id: AP-13
type: task
title: Try one claude plugin eval case
status: todo
priority: medium
owner: claude
created: 2026-11-15
parent: AP-1
blocked_by: [AP-4]
---
Find out whether the test-repo check can rerun on its own after each Claude Code update.

Done when we know whether an eval run can answer the skill's AskUserQuestion prompts. If it can, one case passes.

## Subtasks
- [ ] Run `claude plugin eval init --bare`
- [ ] Write one case with a grader per defect
- [ ] Run it and log the result

## Log
- 2026-11-15 12:51 claude: created
