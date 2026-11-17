---
id: AP-30
type: task
title: Rewrite the style's rule on naming things
status: todo
priority: medium
owner: claude
created: 2026-11-16
parent: AP-28
labels: [plain-english]
blocked_by: [AP-29]
---
Replace the abstract rule ("Don't stand in for it with an abstraction, a metaphor or project-speak") with a list of the stand-ins found in the user's transcripts, each with what to write instead, and a check for each sentence: does it say who does what to which thing? Drop the bad example, which reads like the sentences it warns against, and keep only good ones.

Done when the whole suite has run on the rewrite with Opus 5.5 and Fable 5.2, and the rewrite stays only if stand-ins drop while the hedge, filler, word and bold counts don't get worse. A dated note in .project/docs/notes/ gives the numbers.

## Subtasks
- [ ] Rewrite the rule
- [ ] Update test_style.py if it checks the old wording
- [ ] Run the suite on both models
- [ ] Write the note, and keep or revert the rewrite

## Log
- 2026-11-16 18:09 claude: created
