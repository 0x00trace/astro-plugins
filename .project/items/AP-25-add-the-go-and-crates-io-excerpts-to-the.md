---
id: AP-25
type: task
title: Add the Go and crates.io excerpts to the style
status: cancelled
priority: medium
owner: claude
created: 2026-11-16
parent: AP-22
labels: [plain-english]
---
A "What it reads like" section at the end of `output-styles/plain-english.md`, with each excerpt's source and license. Excerpts: three from "Fixing For Loops in Go 1.22" (David Chase and Russ Cox, go.dev/blog/loopvar-preview, CC BY 4.0) and four from "crates.io Postmortem: Broken Crate Downloads" (Tobias Bieniek, blog.rust-lang.org, MIT/Apache-2.0).

Done when the section is in the style, `test_style.py` checks it, and the unit tests, `claude plugin test` and `claude plugin validate` pass.

## Subtasks
- [x] Write the section with attribution (CC BY 4.0, MIT/Apache-2.0)
- [x] Credit both sources in the README
- [x] Update `test_style.py`
- [x] Check in a try-plugin session that a subagent gets the section

## Log
- 2026-11-16 17:35 claude: created
- 2026-11-16 17:45 claude: moved to in-progress
- 2026-11-16 17:47 claude: done subtask: Write the section with attribution (CC BY 4.0, MIT/Apache-2.0)
- 2026-11-16 17:47 claude: done subtask: Credit both sources in the README
- 2026-11-16 17:47 claude: done subtask: Update `test_style.py`
- 2026-11-16 17:47 claude: done subtask: Check in a try-plugin session that a subagent gets the section
- 2026-11-16 17:47 claude: try-plugin, Claude Code 2.1.326, Fable 5.2: the main session and an Explore subagent both quoted 'These passages show the writing this style asks for.' The subagent's transcript has it in a hook_additional_context row. The new test fails when the CC BY credit is removed.
- 2026-11-16 17:48 claude: moved to waiting: Committed in 1bebb39; merges with the 0.2.0 PR after AP-26 measures it
- 2026-11-16 17:52 claude: moved to cancelled: Reverted in ee2b351 after AP-26: the passages made replies longer and added bold, with no measurable drop in hedging
