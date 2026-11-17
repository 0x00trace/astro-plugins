---
id: AP-32
type: task
title: Cut the vague references the Name things rule leaves
status: todo
priority: medium
owner: claude
created: 2026-11-16
labels: [plain-english]
---
After AP-30's rewrite, replies still use general phrases and ambiguous nouns that the style's list doesn't name: "PR #33 holds up everything left", "Everything else for 1.4 waits on PR #33", "The other option is ...", and "the change" or "the fix" when the reply discusses two. AP-30 rewrote the vague-reference grader to catch these; the 0.2.0 numbers came from the old rubric, so a fresh baseline comes first.

Done when the suite, run with the new rubric on 0.2.0 and on a change that covers these phrases, shows fewer replies failing no-vague-references on Opus 5.5 and Fable 5.2, with the other counts no worse.

## Subtasks
- [ ] Run the suite on 0.2.0 with the new rubric
- [ ] Add the phrases to the style's Name things list, or a rule for them
- [ ] Run the suite again and compare

## Log
- 2026-11-16 18:45 claude: created
