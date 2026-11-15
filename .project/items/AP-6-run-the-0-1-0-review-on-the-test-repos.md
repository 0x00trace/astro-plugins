---
id: AP-6
type: task
title: Run the 0.1.0 review on the test repos
status: in-progress
priority: high
owner: claude
created: 2026-11-15
parent: AP-1
blocked_by: [AP-4]
---
Record what the current skill catches before anything changes, so the change can be scored against it.

Done when a table of the 12 cases (11 defects plus the `.claude/CLAUDE.md` location) shows which ones the 0.1.0 review proposes fixing, with screen captures.

## Subtasks
- [x] Review `review-me/` with Project, then "Review and improve it"
- [x] Review `dot-claude/`
- [ ] Score both runs
- [ ] Save the captures and the table in this item's log

## Log
- 2026-11-15 12:51 claude: created
- 2026-11-15 13:18 claude: moved to in-progress
- 2026-11-15 13:18 claude: Rule for both runs (AP-6 and AP-12): approve reads and writes in the session's own scratchpad; decline installs, network fetches and edits to the repo before the edits are shown. A pilot on the pre-fix fixture is running; the scored baseline reruns on the fixed fixture.
- 2026-11-15 13:29 claude: Declined the baseline's pnpm install in a clone and sent: Don't install packages or run the project's scripts. Go on from what you can read.
- 2026-11-15 13:31 claude: Baseline's Phase 3 answers, to reuse in AP-12: Changes = No, nothing's changed. Releasing section accurate = Accurate, keep it. How DATABASE_URL reaches the scripts = direnv or a shell hook. Commit pnpm-lock.yaml = Yes. Rule: anything in the fixture that isn't a seeded defect is accurate. (Fixture gap to fix after the runs: nothing loads .env.)
- 2026-11-15 13:38 claude: 0.1.0 on review-me: 9 of 11. Caught D1 (230 to ~110 lines), D2, D3, D4, D5, D6, D7, D9, D11. Missed D8 (the .env line stays, no permission rule) and D10 ('The Releasing section stays as it is'). Kept K1 and K2, cut K3 (the run-one-test-file line). 14 edits, $2.56. It also grepped the claude binary to confirm the import fix. Reply: scratchpad captures/ap6-base-review-me-reply.md.
- 2026-11-15 13:38 claude: 0.1.0 on dot-claude: Q1 said 'None at the root, but .claude/CLAUDE.md exists (19 lines) ... so this would review that one'. So D12 was caught in this run, though 0.1.0's Phase 0 says only the root file counts. Running its review of the sound file to count false alarms.
- 2026-11-15 13:38 claude: done subtask: Review `review-me/` with Project, then "Review and improve it"
- 2026-11-15 13:38 claude: done subtask: Review `dot-claude/`
