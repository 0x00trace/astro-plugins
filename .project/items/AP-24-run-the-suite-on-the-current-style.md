---
id: AP-24
type: task
title: Run the suite on the current style
status: in-progress
priority: medium
owner: claude
created: 2026-11-16
parent: AP-21
labels: [plain-english]
blocked_by: [AP-23]
---
Shows whether 0.1.0 changes anything.

Done when each case's score with and without the plugin is logged on the item, with one pair of replies quoted side by side.

## Subtasks
- [x] Run it with 3 runs per case
- [x] Read the replies where the graders split
- [x] Log the scores

## Log
- 2026-11-16 17:35 claude: created
- 2026-11-16 17:44 claude: moved to in-progress
- 2026-11-16 17:44 claude: done subtask: Run it with 3 runs per case
- 2026-11-16 17:44 claude: done subtask: Read the replies where the graders split
- 2026-11-16 17:44 claude: Claude Code 2.1.326, Opus 5.5, Sonnet judge, 3 runs per arm, $5.46, 163s. Case scores with/without: commit-message 1.00/1.00, failing-test 1.00/1.00, pick-one 1.00/0.94, review-diff 1.00/0.94, status 1.00/1.00, windows 1.00/0.78, style-loads 1.00/0.00. Every right-answer grader passed in both arms. Over the 18 writing replies (evals/stats.py), with vs without: mean 143 vs 195 words, hedges 0 vs 3, hedge-like words 8 vs 20, filler 0 vs 3, bold spans 12 vs 54. No reply in either arm used an em dash, buzzword, opener or closer.
- 2026-11-16 17:44 claude: Side by side, windows run 1. Without: 'Probably yes, but nobody has tested it there. I can't run Windows from this Linux machine, so everything below comes from reading the code' (291 words; the other two open 'I can't say for sure' and 'I don't know for sure', then 'I'd expect it to work'). With: 'Nobody has run it on Windows yet. The README says "It has been run on Linux only", and "Check it on Windows" is still unchecked in TODO.md. I can't run Windows here either, so this answer comes from reading the code, not from testing it.' (202 words).
- 2026-11-16 17:44 claude: The with-arm passes every pass/fail grader 18/18, so those graders can't show whether AP-25's excerpts help. AP-26 compares the counts from evals/stats.py instead. Of the 8 hedge-like words left with the plugin, 5 are 'should' meaning ought to; 1 is a real hedge ('That should make the test pass').
- 2026-11-16 17:44 claude: done subtask: Log the scores
