---
id: AP-7
type: task
title: Find every instruction file that loads
status: done
priority: medium
owner: claude
created: 2026-11-15
parent: AP-2
---
Phase 0 reads only `./CLAUDE.md`, but a project file can also live at `./.claude/CLAUDE.md`. In a repo that uses it, the skill reports "None yet" and drafts a second file, and both load. The review also needs the other files that load with the one it reviews, to catch conflicts.

Done when `dot-claude/` shows "Exists, N lines" in the first question and no second file gets drafted.

## Subtasks
- [x] Phase 0 checks `./.claude/CLAUDE.md` too
- [x] Phase 1 option descriptions name the file found
- [x] Phase 2 surveys list nested CLAUDE.md files, `.claude/rules/`, `~/.claude/rules/` and AGENTS.md
- [x] Wording test

## Log
- 2026-11-15 12:51 claude: created
- 2026-11-15 13:19 claude: moved to in-progress
- 2026-11-15 13:19 claude: Started while AP-6's baseline runs from a 0.1.0 copy in the scratchpad, so this edit can't touch it.
- 2026-11-15 13:22 claude: done subtask: Phase 0 checks `./.claude/CLAUDE.md` too
- 2026-11-15 13:22 claude: done subtask: Phase 1 option descriptions name the file found
- 2026-11-15 13:22 claude: done subtask: Phase 2 surveys list nested CLAUDE.md files, `.claude/rules/`, `~/.claude/rules/` and AGENTS.md
- 2026-11-15 13:22 claude: done subtask: Wording test
- 2026-11-15 13:22 claude: Checked live on a dot-claude copy: Q1 says 'Exists at .claude/CLAUDE.md, 19 lines.' and the next question is '.claude/CLAUDE.md already exists (19 lines). What should we do with it?'. No ./CLAUDE.md was created. The full review gets scored in AP-12.
- 2026-11-15 13:22 claude: moved to done
