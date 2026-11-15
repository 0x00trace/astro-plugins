---
id: AP-4
type: task
title: Build the seeded test repos
status: todo
priority: high
owner: claude
created: 2026-11-15
parent: AP-1
---
Two small repos with known defects, so every run of the review is scored against the same list.

Done when `review-me/` holds a CLAUDE.md with the 11 defects its README lists, and `dot-claude/` keeps its file at `.claude/CLAUDE.md`.

The defects: over 200 lines; a dense paragraph of rules; "IMPORTANT: you MUST ALWAYS"; a `pnpm run lint:all` that `package.json` doesn't define; a path that doesn't exist; a line that contradicts a `.claude/rules/` file; `@Design Docs/api.md` with the space unescaped; "Never read .env"; a directory tree; a multi-step release procedure; "we moved to pnpm in PR #12".

## Subtasks
- [ ] Write the defect list in the fixtures' README
- [ ] Build `review-me/` with a `package.json`, a rules file and `Design Docs/api.md`
- [ ] Build `dot-claude/`
- [ ] Store them under names that don't load (`CLAUDE.fixture.md`, `claude-dir/`), so the bad CLAUDE.md doesn't load into this repo's own sessions as a nested file, and copy them into a scratch git repo for each run

## Log
- 2026-11-15 12:51 claude: created
