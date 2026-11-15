---
id: AP-12
type: task
title: Run the changed review on the test repos
status: done
priority: medium
owner: claude
created: 2026-11-15
parent: AP-1
blocked_by: [AP-6, AP-7, AP-8, AP-9, AP-10, AP-11]
---
Show that the changed review catches what 0.1.0 missed.

Done when each seeded defect gets a proposed fix, and the before-and-after table is shown with captures.

## Subtasks
- [x] Rerun both repos
- [x] Score the runs against the baseline table
- [x] Fix what the review missed and rerun
- [x] Reply 'write it' in the review-me run and capture Phase 5's check and Phase 8's /context all step (AP-11)
- [x] Run review-me once with claude-api off in skillOverrides and capture the one-line notice (AP-8)

## Log
- 2026-11-15 12:51 claude: created
- 2026-11-15 13:25 claude: added subtask: Reply 'write it' in the review-me run and capture Phase 5's check and Phase 8's /context all step (AP-11)
- 2026-11-15 13:25 claude: added subtask: Run review-me once with claude-api off in skillOverrides and capture the one-line notice (AP-8)
- 2026-11-15 13:33 claude: Phase 3 answers in the after-run, matched to the baseline's: Changes = No. Releases push to main or go through a PR = push to main (keeps Releasing as written; this contradiction with the PR rule wasn't seeded). Where CI lives = In GitHub, not in this copy. How DATABASE_URL arrives = direnv or my shell.
- 2026-11-15 13:44 claude: From the review-me run: the drafted release skill had an unquoted description with ': ', which is invalid YAML. Only Phase 5's check caught it, so Phase 6 now says to quote such descriptions. Also fixed four unseeded fixture problems both runs flagged: nothing loaded .env (scripts now pass --env-file=.env), the PR rule now exempts releases, there's an index migration behind 'keep the query on an index', and the logger line names Fastify's logger. The scored runs used the earlier fixture, the same one for both.
- 2026-11-15 13:44 claude: moved to in-progress
- 2026-11-15 13:48 claude: Changed skill on review-me: 11 of 11 (0.1.0: 9 of 11). It also caught D8 (proposed Read(./.env) in permissions.deny, and kept the CLAUDE.md line because a Bash cat isn't blocked) and D10 (drafted .claude/skills/release/SKILL.md with disable-model-invocation). Kept K1-K3 (0.1.0 cut K3). Every edit names path:line and its check, and the Checked line reads 230 -> 104 lines, 13 paths, 9 commands, 1 import, no conflicts, includeGitInstructions already false. Audit 5m45s, session $3.86 at the edits (0.1.0: $2.56).
- 2026-11-15 13:48 claude: Changed skill on dot-claude: D12 caught (Q1 'Exists at .claude/CLAUDE.md, 19 lines', reviewed that file, drafted no root file). 2 edits, the same count as 0.1.0, both grounded in code: the 'or existing notes stop loading' reason is wrong, since encoding/json skips unknown fields. The audit found nothing. The Checked line: 19 lines, 4 paths, 4 commands, no imports, no conflicts. Captures: scratchpad captures/ap12-*.
- 2026-11-15 13:48 claude: done subtask: Rerun both repos
- 2026-11-15 13:48 claude: done subtask: Score the runs against the baseline table
- 2026-11-15 13:48 claude: done subtask: Reply 'write it' in the review-me run and capture Phase 5's check and Phase 8's /context all step (AP-11)
- 2026-11-15 13:48 claude: done subtask: Fix what the review missed and rerun
- 2026-11-15 13:48 claude: Nothing seeded was missed. Fixed the two dot-claude flaws both runs flagged: the migration rule's wrong reason, and store.go returning migrate's error unwrapped. dot-claude still vets and passes go test.
- 2026-11-15 13:50 claude: done subtask: Run review-me once with claude-api off in skillOverrides and capture the one-line notice (AP-8)
- 2026-11-15 13:50 claude: moved to done
