---
id: AP-12
type: task
title: Run the changed review on the test repos
status: in-progress
priority: medium
owner: claude
created: 2026-11-15
parent: AP-1
blocked_by: [AP-6, AP-7, AP-8, AP-9, AP-10, AP-11]
---
Show that the changed review catches what 0.1.0 missed.

Done when each seeded defect gets a proposed fix, and the before-and-after table is shown with captures.

## Subtasks
- [ ] Rerun both repos
- [ ] Score the runs against the baseline table
- [ ] Fix what the review missed and rerun
- [ ] Reply 'write it' in the review-me run and capture Phase 5's check and Phase 8's /context all step (AP-11)
- [ ] Run review-me once with claude-api off in skillOverrides and capture the one-line notice (AP-8)

## Log
- 2026-11-15 12:51 claude: created
- 2026-11-15 13:25 claude: added subtask: Reply 'write it' in the review-me run and capture Phase 5's check and Phase 8's /context all step (AP-11)
- 2026-11-15 13:25 claude: added subtask: Run review-me once with claude-api off in skillOverrides and capture the one-line notice (AP-8)
- 2026-11-15 13:33 claude: Phase 3 answers in the after-run, matched to the baseline's: Changes = No. Releases push to main or go through a PR = push to main (keeps Releasing as written; this contradiction with the PR rule wasn't seeded). Where CI lives = In GitHub, not in this copy. How DATABASE_URL arrives = direnv or my shell.
- 2026-11-15 13:44 claude: From the review-me run: the drafted release skill had an unquoted description with ': ', which is invalid YAML. Only Phase 5's check caught it, so Phase 6 now says to quote such descriptions. Also fixed four unseeded fixture problems both runs flagged: nothing loaded .env (scripts now pass --env-file=.env), the PR rule now exempts releases, there's an index migration behind 'keep the query on an index', and the logger line names Fastify's logger. The scored runs used the earlier fixture, the same one for both.
- 2026-11-15 13:44 claude: moved to in-progress
