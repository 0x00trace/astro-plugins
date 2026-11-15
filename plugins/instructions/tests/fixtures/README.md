# Review fixtures

Two small repos with known defects in their CLAUDE.md, to score what `/instructions:init`'s review catches (AP-4). This list sits outside both repos, so the review under test never reads it.

| Fixture | What it is | Its CLAUDE.md |
| --- | --- | --- |
| `review-me/` | A TypeScript API on Fastify and Postgres, run with pnpm | `CLAUDE.md` at the root, 11 defects and 3 lines to keep |
| `dot-claude/` | A Go command-line notebook | `.claude/CLAUDE.md`, a short file with nothing wrong |

## Build a scratch repo

The fixtures store their instruction files under names that don't load, so a session in this repo never picks up the flawed CLAUDE.md as a nested file. `fixture_repo.py` copies a fixture, gives those files their real names (`CLAUDE.fixture.md` becomes `CLAUDE.md`, `claude-dir` becomes `.claude`) and commits it in a new git repo:

```
python3 plugins/instructions/tests/fixture_repo.py review-me /path/to/scratch/review-me
python3 plugins/instructions/tests/fixture_repo.py dot-claude /path/to/scratch/dot-claude
```

Run `/instructions:init` in the copy, pick "Project CLAUDE.md", then "Review and improve it", and "Neither, just CLAUDE.md". Score the reply that shows the edits.

## Cases

A case is **caught** when the review proposes an edit that fixes it, **named** when it points the problem out without a fix, and **missed** otherwise.

| ID | Case | Where in review-me | What a good review proposes |
| --- | --- | --- | --- |
| D1 | Over 200 lines | the whole file (about 230 lines) | Cut what Claude can read from the code (D9, Architecture, Database schema, Error codes, Dependencies, API endpoints) and the generic lines, to get under 200 |
| D2 | A dense paragraph of rules | "Working rules" | Split it into bullets under a heading, each rule with its reason |
| D3 | Pressure language | "IMPORTANT: you MUST ALWAYS run `pnpm test`…NEVER skip this!!" | Say it plainly ("Run `pnpm test` before you commit"), or a Stop hook if it must always happen |
| D4 | A command that doesn't exist | `pnpm run lint:all`; `package.json` has only `lint` | `pnpm lint` |
| D5 | A path that doesn't exist | "Route handlers live in `src/routes/`" | `src/api/handlers.ts`, or remove the line |
| D6 | A contradiction with a rule file | "Put each test next to the file it tests" against `.claude/rules/testing.md`'s "Put tests in `tests/`" | Remove the CLAUDE.md line, since the rule file and the repo agree |
| D7 | An import that doesn't load | `@Design Docs/api.md`, which stops at the space and imports `Design` | `@Design\ Docs/api.md`, or drop it, since API docs belong in an import or nowhere |
| D8 | A rule that must always hold | "Never read or print `.env`" | A deny rule such as `Read(./.env)` in `.claude/settings.json` |
| D9 | Content Claude can read from the code | "Directory structure", a tree of the repo | Remove it |
| D10 | A procedure with several steps | "Releasing", 10 numbered steps | Move it to a skill, such as `.claude/skills/release/SKILL.md` |
| D11 | History | "We moved from npm to pnpm in PR #12, so use pnpm now" | State the current rule: "Use pnpm, never npm" |
| D12 | The project file lives at `.claude/CLAUDE.md` | dot-claude | Find it, report "Exists, N lines", review it, and don't draft a second `./CLAUDE.md` |

## Lines to keep

A good review keeps these, because Claude can't learn them from the code. Cutting one counts against the run.

| ID | Line in review-me |
| --- | --- |
| K1 | "Integration tests need `DATABASE_URL` pointed at a scratch database, never the dev one" |
| K2 | "Use the error helpers in `src/lib/errors.ts`, never throw raw strings or plain `Error`, because the error handler only maps an `AppError`…" |
| K3 | "Run one test file with `pnpm vitest run tests/handlers.spec.ts`" |

Everything else the review proposes for review-me is fine to propose, or not. dot-claude's file is meant to pass: an edit proposed there is a false alarm, and counts against the run.

`test_fixtures.py` checks that each case and line to keep is still in the fixtures, and that the paths and commands the CLAUDE.md files name exist, except the seeded ones.
