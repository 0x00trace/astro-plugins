---
id: AP-29
type: task
title: Add eval cases that draw status and plan text
status: done
priority: high
owner: claude
created: 2026-11-16
parent: AP-28
labels: [plain-english]
---
The six writing cases rarely ask for a status update or a plan, which is where stand-ins appear in the user's sessions ("Changes land in two plugins", "On the work side, nothing else is in flight"). Three new cases ask about a release in progress, described in files, since the eval sandbox has no git or gh.

Done when the three cases run in `claude plugin eval` with both arms, and the suite's 0.1.0 baseline is logged for Opus 5.5 and Fable 5.2.

## Subtasks
- [x] Write a fixture: a release task list, two open PRs described in a file, and a failing CI log
- [x] Write three cases: where the release stands, what to do next, whether PR #33 can merge today
- [x] Write graders: the right answer, an llm grader for stand-ins, a regex for the stand-in words, and the five style graders
- [x] Count stand-ins in evals/stats.py
- [x] Run 0.1.0 on Fable 5.2 (whole suite) and Opus 5.5 (new cases), and log the counts

## Log
- 2026-11-16 18:09 claude: created
- 2026-11-16 18:09 claude: moved to in-progress
- 2026-11-16 18:14 claude: done subtask: Write a fixture: a release task list, two open PRs described in a file, and a failing CI log
- 2026-11-16 18:14 claude: done subtask: Write three cases: where the release stands, what to do next, whether PR #33 can merge today
- 2026-11-16 18:14 claude: done subtask: Write graders: the right answer, an llm grader for stand-ins, a regex for the stand-in words, and the five style graders
- 2026-11-16 18:14 claude: done subtask: Count stand-ins in evals/stats.py
- 2026-11-16 18:14 claude: Probe of merge-today, Opus 5.5, 1 run per arm: one llm stand-in grader failed both replies, so it had no room to show a change. Split it into no-vague-references, no-metaphor-verbs and no-cleft-sentences. The eval's judge gives no reasons, so I asked Sonnet with the same rubric: with the plugin it flagged 'the fix is a one-line change' before any fix is named; without, 'it can probably go in today' and 'CI goes green ... and it merges'. Tightened merge-today's right-answer rubric, which judges split on.
- 2026-11-16 18:28 claude: 0.1.0 baseline, Claude Code 2.1.326, 3 runs per arm, Sonnet judge. Passing of 27 writing replies, with/without the plugin. Opus 5.5 ($10.28, 441s): vague references 6/3, metaphor verbs 17/13, cleft sentences 23/19, stand-in words 26/24, hedges 26/19, right answer 24/27. Fable 5.2 ($20.02, 402s): vague references 8/5, metaphor verbs 15/13, cleft sentences 24/17, stand-in words 22/20, hedges 27/14, right answer 26/27. stats.py with the plugin: Opus mean 189 words, 44 bold, 1 stand-in word; Fable 175 words, 45 bold, 5 stand-in words.
- 2026-11-16 18:28 claude: commit-message's right-answer rubric asks for '10 items', and Opus with the plugin wrote 'exactly BULK_QTY items' from the diff; the judge passed one of two identical messages. Fix the rubric after AP-30's run, so AP-30 compares against the same rubric.
- 2026-11-16 18:28 claude: done subtask: Run 0.1.0 on Fable 5.2 (whole suite) and Opus 5.5 (new cases), and log the counts
- 2026-11-16 18:28 claude: Merged in PR #126.
- 2026-11-16 18:28 claude: moved to done
