---
id: AP-25
type: task
title: Add the Go and crates.io excerpts to the style
status: todo
priority: medium
owner: claude
created: 2026-11-16
parent: AP-22
labels: [plain-english]
---
A "What it reads like" section at the end of `output-styles/plain-english.md`, with each excerpt's source and license. Excerpts: three from "Fixing For Loops in Go 1.22" (David Chase and Russ Cox, go.dev/blog/loopvar-preview, CC BY 4.0) and four from "crates.io Postmortem: Broken Crate Downloads" (Tobias Bieniek, blog.rust-lang.org, MIT/Apache-2.0).

Done when the section is in the style, `test_style.py` checks it, and the unit tests, `claude plugin test` and `claude plugin validate` pass.

## Subtasks
- [ ] Write the section with attribution (CC BY 4.0, MIT/Apache-2.0)
- [ ] Credit both sources in the README
- [ ] Update `test_style.py`
- [ ] Check in a try-plugin session that a subagent gets the section

## Log
- 2026-11-16 17:35 claude: created
