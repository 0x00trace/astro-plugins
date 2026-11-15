# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About this project

ledger-api is the HTTP API behind the Ledger mobile app. It stores accounts and their entries in
Postgres and serves monthly totals to the app. It is written in TypeScript and runs on Node with
Fastify. The mobile team depends on this API, so it is important that you are careful with it and
that you write high quality code that is easy to maintain and well tested.

API reference: @Design Docs/api.md

## Commands

- Install dependencies: `pnpm install`
- Start the dev server: `pnpm dev` (listens on port 3000)
- Build: `pnpm build`
- Run the unit tests: `pnpm test`
- Run the integration tests: `pnpm run test:integration`
- Typecheck: `pnpm typecheck`
- Format: `pnpm format`
- Run the migrations: `pnpm run db:migrate`
- Lint everything with `pnpm run lint:all` before you open a PR.

## Directory structure

```
ledger-api/
├── CHANGELOG.md
├── Design Docs/
│   └── api.md
├── migrations/
│   ├── 001_init.sql
│   └── 002_entries_account_index.sql
├── scripts/
│   └── migrate.mjs
├── src/
│   ├── api/
│   │   ├── handlers.ts
│   │   └── schemas.ts
│   ├── lib/
│   │   ├── db.ts
│   │   └── errors.ts
│   ├── index.ts
│   └── server.ts
├── tests/
│   ├── integration/
│   │   └── ledger.spec.ts
│   └── handlers.spec.ts
├── eslint.config.js
├── package.json
├── README.md
├── tsconfig.json
└── vitest.integration.config.ts
```

## Architecture

The service is a single Fastify app. A request flows through these layers:

1. `src/index.ts` reads `PORT` and starts the server.
2. `src/server.ts` builds the Fastify instance, turns on its logger and sets the error handler.
3. The error handler maps an `AppError` to its status code and turns anything else into a 500.
4. `src/server.ts` calls `registerHandlers`, which adds every route.
5. Each handler parses its body with a zod schema from `src/api/schemas.ts`.
6. Handlers talk to Postgres through `query` in `src/lib/db.ts`.
7. `src/lib/db.ts` keeps one connection pool for the whole process.
8. Handlers return plain objects, and Fastify serializes them to JSON.

Route handlers live in `src/routes/`, one file per resource.

The database has two tables. `accounts` holds an id and a name. `entries` holds an id, the account
it belongs to, an amount in cents and the date it was booked on. Monthly totals are computed with a
query at request time, not stored. There is no cache in front of the database.

Migrations are plain SQL files in `migrations/`, applied in file-name order by
`scripts/migrate.mjs`, which records each one in a `schema_migrations` table so it runs only once.

## Database schema

`accounts`:

| Column | Type | Notes |
| --- | --- | --- |
| id | serial | primary key |
| name | text | not null |

`entries`:

| Column | Type | Notes |
| --- | --- | --- |
| id | serial | primary key |
| account_id | integer | not null, references `accounts (id)` |
| amount_cents | integer | not null, negative for money out |
| booked_on | date | not null |

## Error codes

| Status | Code | When |
| --- | --- | --- |
| 400 | from `badRequest(code)` | a request the handler can't act on |
| 404 | `account_not_found` | the account in the path doesn't exist |
| 500 | `internal` | anything that isn't an `AppError` |

## Dependencies

Runtime:

- fastify 5: the HTTP server
- pg 8: the Postgres client
- pino 9: the logger Fastify uses
- zod 3: request validation

Development:

- typescript 5: the compiler
- tsx 4: runs TypeScript directly in development
- vitest 3: the test runner
- eslint 9 and typescript-eslint 8: the linter and its TypeScript rules
- prettier 3: the formatter
- `@types/node` and `@types/pg`: type definitions

## API endpoints

| Method | Path | What it does |
| --- | --- | --- |
| GET | /health | Returns `{"ok": true}` |
| POST | /accounts | Creates an account and returns its id |
| POST | /accounts/:id/entries | Books an entry on an account |
| GET | /accounts/:id/totals | Returns the account's total for each month |

All request bodies are JSON and are validated with zod. An unknown account returns a 404 with the
code `account_not_found`.

## Code style

- Use TypeScript for all new code.
- Use `const` instead of `let` where possible.
- Use camelCase for variables and functions, and PascalCase for classes and types.
- Use `type`, not `interface`, for object shapes.
- Use async/await instead of raw promises.
- Use double quotes for strings.
- Use 2-space indentation.
- Add a trailing comma in multi-line literals.
- Keep imports sorted: node built-ins first, then packages, then local files.
- Import local files with the `.js` extension, because the project is an ES module.
- Write clean, readable code.
- Handle errors properly.
- Write meaningful variable names.
- Avoid deeply nested code.
- Don't leave commented-out code behind.
- Delete unused imports.

## Working rules

When you change a handler, update its zod schema in the same commit and keep the response shape the same unless the ticket says otherwise, because the mobile app pins the shape. Don't add new dependencies without asking first. Keep functions under 40 lines where you can. Log with Fastify's logger (`request.log` in a handler), not console.log, since console output is dropped in production. Every new endpoint needs an entry in `Design Docs/api.md`. Prefer early returns over nested ifs. Don't touch a migration once it has shipped; add a new one instead.

## Testing

IMPORTANT: you MUST ALWAYS run `pnpm test` before you commit. NEVER skip this!!

- Put each test next to the file it tests, as `<name>.spec.ts`.
- Run one test file with `pnpm vitest run tests/handlers.spec.ts`.
- Integration tests need `DATABASE_URL` pointed at a scratch database, never the dev one. See
  `.env.example` for the format.
- Unit tests must not touch the database.
- Use `server.inject` to call a route in a test instead of starting the server.
- Write a test for every new endpoint.
- Make sure all the tests pass.

## Environment

- Copy `.env.example` to `.env` and fill it in before running the server.
- `DATABASE_URL` is the Postgres connection string.
- `PORT` sets the port the server listens on. It defaults to 3000.
- Never read or print `.env`. It holds the production database password.
- Node 22 or later is required.

## Gotchas

- Use the error helpers in `src/lib/errors.ts`, never throw raw strings or plain `Error`, because
  the error handler only maps an `AppError` to a status code. Anything else becomes a 500.

## Releasing

To release a new version:

1. Make sure you're on `main` and `git status` is clean.
2. Run `pnpm test` and `pnpm run test:integration`, and stop if either fails.
3. Bump `version` in `package.json`, following semver.
4. Add a section for the new version at the top of `CHANGELOG.md`, one line per user-facing change.
5. Commit both files with the message `chore: release vX.Y.Z`.
6. Tag the commit: `git tag vX.Y.Z`.
7. Push the commit and the tag: `git push origin main vX.Y.Z`.
8. CI deploys from the tag. Watch the deploy in the GitHub Actions tab.
9. Once it's live, check that `GET /health` on production returns `{"ok": true}`.
10. Post the changelog section in the team channel.

## Git

- Branch from `main`, and name the branch `feature/<ticket>-<slug>` or `fix/<ticket>-<slug>`.
- Write commit messages in the imperative mood.
- Keep commits small and focused.
- Open a pull request for every change except a release, and get one approval before merging.
- Squash-merge pull requests.
- We moved from npm to pnpm in PR #12, so use pnpm now and never commit a `package-lock.json`.

## Pull requests

- Give the pull request a clear title.
- Describe what changed and why.
- Link the ticket.
- Add screenshots of the app if the change affects what the mobile app shows.
- Make sure CI passes before asking for a review.
- Respond to review comments.
- Delete the branch after merging.

## Performance

- Monthly totals are computed per request. Keep the query on an index if you change it.
- Don't load a whole table into memory.
- Use a single query instead of a query per row.
- Avoid unnecessary work in hot paths.

## Security

- Validate every request body with zod.
- Use parameterized queries, never string concatenation, to build SQL.
- Don't log request bodies, because they can hold account names.
- Keep dependencies up to date.
