---
id: AP-32
type: task
title: Cut the vague references the Name things rule leaves
status: cancelled
priority: medium
owner: claude
created: 2026-11-16
labels: [plain-english]
---
After AP-30's rewrite, replies still use general phrases and ambiguous nouns that the style's list doesn't name: "PR #33 holds up everything left", "Everything else for 1.4 waits on PR #33", "The other option is ...", and "the change" or "the fix" when the reply discusses two. AP-30 rewrote the vague-reference grader to catch these; the 0.2.0 numbers came from the old rubric, so a fresh baseline comes first.

Done when the suite, run with the new rubric on 0.2.0 and on a change that covers these phrases, shows fewer replies failing no-vague-references on Opus 5.5 and Fable 5.2, with the other counts no worse.

## Subtasks
- [x] Run the suite on 0.2.0 with the new rubric
- [x] Add the phrases to the style's Name things list, or a rule for them
- [x] Run the suite again and compare

## Log
- 2026-11-16 18:45 claude: created
- 2026-11-16 18:55 claude: moved to in-progress
- 2026-11-16 19:09 claude: 0.2.0 baseline with the new vague-reference rubric, 3 runs per arm (Opus $10.84, Fable $18.99). With/without, of 27: Opus no-vague-references 18/11, Fable 21/20. With the plugin, release-status and next-step failed 3 of 3 on both models, merge-today 3 of 3 on Opus. Same style text as AP-30's rewrite run, and Opus no-metaphor-verbs scored 17 this time against 22, so that grader moves about 5 of 27 between identical runs: AP-30's 17 -> 22 on Opus isn't past noise. Fable: 15 (0.1.0) vs 21 and 23 (0.2.0). Measuring AP-32 with 6 runs of the three release cases.
- 2026-11-16 19:09 claude: done subtask: Run the suite on 0.2.0 with the new rubric
- 2026-11-16 19:12 claude: done subtask: Add the phrases to the style's Name things list, or a rule for them
- 2026-11-16 19:32 claude: done subtask: Run the suite again and compare
- 2026-11-16 19:32 claude: Added lines vs 0.2.0, release cases, 6 runs each with the plugin: Opus no-vague-references 2/18 both; Fable 6/18 -> 9/18. Phrase counts per release reply, Opus: 'everything else/left' 2 in 18 -> 7 in 27, 'the other option/way' 1 -> 5; Fable: 'everything else/left' 10 in 18 -> 4 in 27, 'hold up' 4 -> 0. Whole suite with the plugin: vague references Opus 18 -> 18, Fable 21 -> 25. Reverted: the done check needed both models.
- 2026-11-16 19:32 claude: moved to cancelled: Not done: the added lines cut vague phrases on Fable 5.2 but not on Opus 5.5, so they came back out. See the 2026-11-16 note on listing vague phrases
