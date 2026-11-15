---
id: AP-5
type: task
title: Test that a subagent can run the bundled prompt audit
status: done
priority: high
owner: claude
created: 2026-11-15
parent: AP-2
---
The audit step depends on a subagent starting the bundled `claude-api` skill's `prompt-audit` (what `/doctor prompt-audit <path>` runs), and nobody has tried it. If it fails, decision 0001 changes before anything else gets built.

Done when a subagent started from a skill runs `claude-api` with `prompt-audit <path>` on `review-me/` and returns findings, shown in a capture.

## Subtasks
- [x] Write a throwaway skill that starts the subagent
- [x] Run it in a second session with `try-plugin`
- [x] Run it again with `claude-api` turned off in `skillOverrides`, and note what happens
- [x] Note the time and tokens it costs

## Log
- 2026-11-15 12:51 claude: created
- 2026-11-15 13:03 claude: moved to in-progress
- 2026-11-15 13:17 claude: done subtask: Write a throwaway skill that starts the subagent
- 2026-11-15 13:17 claude: done subtask: Run it in a second session with `try-plugin`
- 2026-11-15 13:17 claude: done subtask: Run it again with `claude-api` turned off in `skillOverrides`, and note what happens
- 2026-11-15 13:17 claude: done subtask: Note the time and tokens it costs
- 2026-11-15 13:17 claude: Works. A general-purpose subagent started from a skill called Skill(claude-api, 'prompt-audit ./CLAUDE.md'), read shared/prompt-audit.md from /tmp/claude-1000/bundled-skills/<version>/claude-api/, and returned the report and diff. In default permission mode the Skill call asks for approval first. Cost on review-me: 11m 1s, $2.58 for the session, subagent 6.9M cache-read tokens and 127k output tokens. Most of the time went to Step 7 probes: grepping the claude binary for the import parser, copying CLAUDE.md into scratch dirs, and trying to pnpm add pg (I declined).
- 2026-11-15 13:17 claude: Caught D3, D4, D5, D6, D7 and D11; missed D1 (size), D2 (dense paragraph), D8 (.env belongs in a deny rule), D9 (directory tree) and D10 (procedure belongs in a skill), and kept D8 and D10 on purpose. Those five are AP-9's check list, which backs decision 0001. It also found 3 unseeded fixture defects (a false 400 claim, monthly totals the code lacks, @types/node read as an import), fixed under AP-4.
- 2026-11-15 13:17 claude: With skillOverrides {"claude-api": "off"} the call fails at once with: Skill claude-api is disabled for model invocation in skillOverrides settings. For AP-8: tell the subagent to skip Step 7 and run no installs or binary greps, report only, and fall back to the check list on that error.
- 2026-11-15 13:17 claude: moved to done
