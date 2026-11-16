---
id: AP-26
type: task
title: Measure the style with the excerpts
status: done
priority: medium
owner: claude
created: 2026-11-16
parent: AP-22
labels: [plain-english]
blocked_by: [AP-24, AP-25]
---
Done when a dated note in `.project/docs/notes/` compares the scores with AP-24's, and PROJECT.md's Decisions says whether the excerpts stay or go, or whether the plugin is dropped.

## Subtasks
- [x] Run the suite on the branch with the excerpts
- [x] Write the note
- [x] Record the decision

## Log
- 2026-11-16 17:35 claude: created
- 2026-11-16 17:48 claude: moved to in-progress
- 2026-11-16 17:52 claude: done subtask: Run the suite on the branch with the excerpts
- 2026-11-16 17:52 claude: Excerpts run (1bebb39), 3 runs per arm, $5.58, 161s. With the plugin vs 0.1.0: mean 159 vs 143 words, bold 21 vs 12, hedge-like 5 vs 8, hedges 0 and filler 0 in both, right answers 18/18 in both. The two no-plugin arms differ by 4 words, 3 bold and 4 hedge-like, so the longer replies and extra bold are past the noise and the hedge-like drop isn't. Reverted the excerpts.
- 2026-11-16 17:52 claude: done subtask: Write the note
- 2026-11-16 17:52 claude: done subtask: Record the decision
- 2026-11-16 17:53 claude: Merged in PR #124.
- 2026-11-16 17:53 claude: moved to done
- 2026-11-16 17:53 claude: On main, the excerpts commit is 39836e6 and the revert is 83feaaa (1bebb39 and ee2b351 before the rebase merge).
