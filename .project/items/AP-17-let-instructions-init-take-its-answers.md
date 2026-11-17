---
id: AP-17
type: task
title: Let /instructions:init take its answers as arguments, so an eval case can rerun the review
status: cancelled
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
- 2026-11-16 18:51 claude: moved to in-progress
- 2026-11-16 18:52 claude: moved to waiting: Build it? Arguments for /instructions:init plus two eval cases, about $15 per eval run, or cancel AP-17
- 2026-11-16 18:54 claude: The user chose to cancel: driving a try-plugin session stays the way to check the review.
- 2026-11-16 18:54 claude: moved to cancelled: Not worth it: the user cancelled after the cost and the plan were laid out (about $15 per eval run, and the project half may be dropped once /init shows its proposals)
