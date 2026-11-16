---
id: AP-23
type: task
title: Build the plain-english eval suite
status: in-progress
priority: high
owner: claude
created: 2026-11-16
parent: AP-21
labels: [plain-english]
---
Six cases whose prompts tend to draw hedging, so `claude plugin eval` can score the style against its built-in no-plugin baseline arm.

Done when `claude plugin eval plugins/plain-english --scaffold` runs all six cases with a baseline arm, and every grader returns a verdict.

## Subtasks
- [x] Check that an eval run gets the output style (ask it to quote the style's first sentence, as the README's check does)
- [x] Write a small Python fixture: one failing test and a diff to review
- [x] Write the cases: explain the failing test, review the diff, pick one of two options, answer a question the files can't settle (Windows support), write a commit message, give a status update
- [x] Write graders: one per case for the right answer, and one shared grader for the style rules (hedges, filler, openers, closers, em dashes)

## Log
- 2026-11-16 17:35 claude: created
- 2026-11-16 17:36 claude: moved to in-progress
- 2026-11-16 17:38 claude: done subtask: Check that an eval run gets the output style (ask it to quote the style's first sentence, as the README's check does)
- 2026-11-16 17:38 claude: An eval run gets the output style: style-loads scored 1.00 with the plugin and 0.00 without (the without-arm replied none), 1 run each, $0.10.
- 2026-11-16 17:38 claude: done subtask: Write a small Python fixture: one failing test and a diff to review
- 2026-11-16 17:40 claude: done subtask: Write the cases: explain the failing test, review the diff, pick one of two options, answer a question the files can't settle (Windows support), write a commit message, give a status update
- 2026-11-16 17:40 claude: done subtask: Write graders: one per case for the right answer, and one shared grader for the style rules (hedges, filler, openers, closers, em dashes)
- 2026-11-16 17:40 claude: Shared style graders live in evals/style-graders/ and are symlinked into each case's graders/; the loader follows the links. Replies aren't in the results JSON, so runs use --keep-temp to keep trace.jsonl. The full AP-24 run doubles as this item's done check.
- 2026-11-16 17:44 claude: Added evals/stats.py: the eval's regex graders are pass/fail and hit the ceiling with the plugin, so the script counts hedges, filler, words and bold per reply from the kept traces.
