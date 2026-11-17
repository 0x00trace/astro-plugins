---
id: AP-30
type: task
title: Rewrite the style's rule on naming things
status: done
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
- [x] Rewrite the rule
- [x] Update test_style.py if it checks the old wording
- [x] Run the suite on both models
- [x] Write the note, and keep or revert the rewrite

## Log
- 2026-11-16 18:09 claude: created
- 2026-11-16 18:28 claude: moved to in-progress
- 2026-11-16 18:29 claude: done subtask: Rewrite the rule
- 2026-11-16 18:29 claude: done subtask: Update test_style.py if it checks the old wording
- 2026-11-16 18:29 claude: Rewrote the rule as a Name things section: a who-does-what check, ten stand-ins with plain words, and good examples only. Its examples use names that appear in neither eval fixture (AB-7, PR #52, test_parser.py), so Claude can't copy an answer from them. test_style.py checks no wording that changed.
- 2026-11-16 18:45 claude: done subtask: Run the suite on both models
- 2026-11-16 18:45 claude: Rewrite vs 0.1.0, Claude Code 2.1.326, 3 runs per arm, Sonnet judge, passing of 27 with the plugin. Opus 5.5 ($10.42): metaphor verbs 17->22 (no-plugin arm 13->14), stand-in words 26->27, cleft sentences 23->25, vague references 6->5, right answer 24->26. Fable 5.2 ($18.97): metaphor verbs 15->21 (no-plugin 13->16), stand-in words 22->27, cleft 24->23, vague references 8->7, right answer 26->27. stats.py stand-in words: Opus 1->0, Fable 5->0. Hedges, filler, words and bold no worse. Keeping the rewrite.
- 2026-11-16 18:45 claude: The vague-reference rubric failed ordinary pronouns ('Nobody has run it on Windows' answering 'Does this work on Windows?'), so it couldn't show a change. Rewrote it around general phrases ('everything left', 'the rest'), an ambiguous 'the change', and unclear pronouns. On three rewrite replies it fails the two with 'everything left' and 'everything else' and passes the Windows one. Also fixed commit-message's rubric to accept 'exactly BULK_QTY items' (AP-29 log).
- 2026-11-16 18:45 claude: done subtask: Write the note, and keep or revert the rewrite
- 2026-11-16 18:45 claude: moved to waiting: Merges with the 0.2.0 PR, after AP-31's release commit
- 2026-11-16 18:47 claude: moved to done
