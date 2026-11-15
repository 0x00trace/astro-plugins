---
id: AP-17
type: task
title: Let /instructions:init take its answers as arguments, so an eval case can rerun the review
status: todo
priority: medium
owner: claude
created: 2026-11-15
---
A claude plugin eval run doesn't offer AskUserQuestion (AP-13), so /instructions:init stops at its first question and an eval case can't reach the review. If the skill took its answers from its arguments, such as "project, review and improve, no skills or hooks, nothing changed", and skipped the questions those answer, one eval case per fixture could rerun the AP-12 scoring after each Claude Code update.

## Subtasks
- [ ] Decide whether this is worth it: the try-plugin runs work, but cost about 30 minutes of driving
- [ ] Phase 1 and Phase 3 skip questions the arguments answer
- [ ] An eval case per fixture, with a grader per case D1-D12 and K1-K3

## Log
- 2026-11-15 13:47 claude: created
