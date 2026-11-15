---
id: AP-13
type: task
title: Try one claude plugin eval case
status: done
priority: medium
owner: claude
created: 2026-11-15
parent: AP-1
blocked_by: [AP-4]
---
Find out whether the test-repo check can rerun on its own after each Claude Code update.

Done when we know whether an eval run can answer the skill's AskUserQuestion prompts. If it can, one case passes.

## Subtasks
- [x] Run `claude plugin eval init --bare`
- [x] Write one case with a grader per defect
- [x] Run it and log the result

## Log
- 2026-11-15 12:51 claude: created
- 2026-11-15 13:45 claude: moved to in-progress
- 2026-11-15 13:47 claude: No. A claude plugin eval run doesn't offer AskUserQuestion, even with it in allowed_tools: the init event listed Task, Glob, Grep, Read, Skill, TaskStop and ToolSearch. /instructions:init then printed the primer, read the 4 files and asked Q1 and Q2 as text, and the one-prompt case ended there (7 turns, $0.17). A case can resume a recorded session (context.history_file + execution.prompt), but the review needs several turns of answers. A rerunnable case needs the skill to take its answers as arguments: filed as its own item.
- 2026-11-15 13:47 claude: done subtask: Run `claude plugin eval init --bare`
- 2026-11-15 13:47 claude: done subtask: Write one case with a grader per defect
- 2026-11-15 13:47 claude: done subtask: Run it and log the result
- 2026-11-15 13:47 claude: moved to done
