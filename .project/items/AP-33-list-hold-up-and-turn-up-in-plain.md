---
id: AP-33
type: task
title: List "hold up" and "turn up" in plain-english's style
status: in-progress
priority: medium
owner: claude
created: 2026-11-17
labels: [plain-english]
---
On 0.2.0, "hold up" is the most common dead metaphor left: 11 in 63 replies on Opus 5.5 and 7 in 63 on Fable 5.2. AP-32 listed it, and it fell to 3 in 45 and 0 in 45, but AP-32 was reverted because its vague-phrase lines didn't cut vague references on Opus. The author is fine with vague references (2026-11-17). With "hold up" listed, "turn up" rose on Opus from 1 in 63 to 5 in 45, so list it too.

Done when the three release cases, run 6 times on each model, show fewer "hold up" and "turn up" than the 0.2.0 runs, with no other metaphor phrase and no grader worse, and 0.2.1 is released.

## Subtasks
- [ ] Add "hold up" and "turn up" to the Name things list
- [ ] Remove the no-vague-references grader from the eval suite
- [ ] Run the release cases 6 times on Opus 5.5 and Fable 5.2 and count the phrases
- [ ] Write a note and a PROJECT.md decision
- [ ] Release 0.2.1

## Log
- 2026-11-17 16:09 claude: created
- 2026-11-17 16:09 claude: moved to in-progress
