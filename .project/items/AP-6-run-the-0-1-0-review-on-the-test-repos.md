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
- [ ] Review `review-me/` with Project, then "Review and improve it"
- [ ] Review `dot-claude/`
- [ ] Score both runs
- [ ] Save the captures and the table in this item's log

## Log
- 2026-11-15 12:51 claude: created
- 2026-11-15 13:18 claude: moved to in-progress
- 2026-11-15 13:18 claude: Rule for both runs (AP-6 and AP-12): approve reads and writes in the session's own scratchpad; decline installs, network fetches and edits to the repo before the edits are shown. A pilot on the pre-fix fixture is running; the scored baseline reruns on the fixed fixture.
