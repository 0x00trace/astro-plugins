---
id: AP-7
type: task
title: Find every instruction file that loads
status: todo
priority: medium
owner: claude
created: 2026-11-15
parent: AP-2
---
Phase 0 reads only `./CLAUDE.md`, but a project file can also live at `./.claude/CLAUDE.md`. In a repo that uses it, the skill reports "None yet" and drafts a second file, and both load. The review also needs the other files that load with the one it reviews, to catch conflicts.

Done when `dot-claude/` shows "Exists, N lines" in the first question and no second file gets drafted.

## Subtasks
- [ ] Phase 0 checks `./.claude/CLAUDE.md` too
- [ ] Phase 1 option descriptions name the file found
- [ ] Phase 2 surveys list nested CLAUDE.md files, `.claude/rules/`, `~/.claude/rules/` and AGENTS.md
- [ ] Wording test

## Log
- 2026-11-15 12:51 claude: created
