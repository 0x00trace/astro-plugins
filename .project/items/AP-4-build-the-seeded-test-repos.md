---
id: AP-4
type: task
title: Build the seeded test repos
status: done
priority: high
owner: claude
created: 2026-11-15
parent: AP-1
---
Two small repos with known defects, so every run of the review is scored against the same list.

Done when `review-me/` holds a CLAUDE.md with the 11 defects its README lists, and `dot-claude/` keeps its file at `.claude/CLAUDE.md`.

The defects: over 200 lines; a dense paragraph of rules; "IMPORTANT: you MUST ALWAYS"; a `pnpm run lint:all` that `package.json` doesn't define; a path that doesn't exist; a line that contradicts a `.claude/rules/` file; `@Design Docs/api.md` with the space unescaped; "Never read .env"; a directory tree; a multi-step release procedure; "we moved to pnpm in PR #12".

## Subtasks
- [x] Write the defect list in the fixtures' README
- [x] Build `review-me/` with a `package.json`, a rules file and `Design Docs/api.md`
- [x] Build `dot-claude/`
- [x] Store them under names that don't load (`CLAUDE.fixture.md`, `claude-dir/`), so the bad CLAUDE.md doesn't load into this repo's own sessions as a nested file, and copy them into a scratch git repo for each run

## Log
- 2026-11-15 12:51 claude: created
- 2026-11-15 12:58 claude: moved to in-progress
- 2026-11-15 13:03 claude: done subtask: Write the defect list in the fixtures' README
- 2026-11-15 13:03 claude: done subtask: Build `review-me/` with a `package.json`, a rules file and `Design Docs/api.md`
- 2026-11-15 13:03 claude: done subtask: Build `dot-claude/`
- 2026-11-15 13:03 claude: done subtask: Store them under names that don't load (`CLAUDE.fixture.md`, `claude-dir/`), so the bad CLAUDE.md doesn't load into this repo's own sessions as a nested file, and copy them into a scratch git repo for each run
- 2026-11-15 13:03 claude: Built tests/fixtures/review-me (229-line CLAUDE.md, D1-D11, keepers K1-K3) and dot-claude (D12, a sound .claude/CLAUDE.md, so any edit proposed there is a false alarm). tests/fixture_repo.py builds a scratch git repo from one; test_fixtures.py pins every case and fails on any path or command the files name that's missing by accident. The TS fixture's tests are *.spec.ts so a future claude plugin test never picks them up.
- 2026-11-15 13:03 claude: moved to done
- 2026-11-15 13:09 claude: Dropped review-me's gotcha that src/lib/db.ts opens its pool on import: pg's Pool creates clients lazily, so the line was false, a defect nobody seeded. The AP-5 spike's audit caught it. The file is now 227 lines.
