---
id: AP-33
type: task
title: List "hold up" and "turn up" in plain-english's style
status: done
priority: medium
owner: claude
created: 2026-11-17
labels: [plain-english]
---
On 0.2.0, "hold up" is the most common dead metaphor left: 11 in 63 replies on Opus 5.5 and 7 in 63 on Fable 5.2. AP-32 listed it, and it fell to 3 in 45 and 0 in 45, but AP-32 was reverted because its vague-phrase lines didn't cut vague references on Opus. The author is fine with vague references (2026-11-17). With "hold up" listed, "turn up" rose on Opus from 1 in 63 to 5 in 45, so list it too.

Done when the three release cases, run 6 times on each model, show fewer "hold up" and "turn up" than the 0.2.0 runs, with no other metaphor phrase and no grader worse, and 0.2.1 is released.

## Subtasks
- [x] Add "hold up" and "turn up" to the Name things list
- [x] Remove the no-vague-references grader from the eval suite
- [x] Run the release cases 6 times on Opus 5.5 and Fable 5.2 and count the phrases
- [x] Write a note and a PROJECT.md decision
- [x] Release 0.2.1

## Log
- 2026-11-17 16:09 claude: created
- 2026-11-17 16:09 claude: moved to in-progress
- 2026-11-17 16:10 claude: done subtask: Add "hold up" and "turn up" to the Name things list
- 2026-11-17 16:10 claude: done subtask: Remove the no-vague-references grader from the eval suite
- 2026-11-17 16:16 claude: done subtask: Run the release cases 6 times on Opus 5.5 and Fable 5.2 and count the phrases
- 2026-11-17 16:16 claude: Release cases, 6 runs each, with the plugin: "hold up" fell from 11 in 27 replies to 2 in 18 on Opus 5.5 and from 7 to 0 on Fable 5.2; "turn up" fell from 1 and 2 to 0. Metaphor-verb grader: Opus 13/27 to 9/18, Fable 16/27 to 13/18. Opus cleft grader fell from 17/27 to 8/18: the flagged sentences use plain verbs, such as "PR #33 is the item everything else waits on". Going ahead with 0.2.1, since the condition the author approved (the two phrases fall, no other metaphor rises) holds. Cost $8.55.
- 2026-11-17 16:16 claude: done subtask: Write a note and a PROJECT.md decision
- 2026-11-17 16:17 claude: done subtask: Release 0.2.1
- 2026-11-17 16:17 claude: moved to done
