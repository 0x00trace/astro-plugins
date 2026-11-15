# ledger-api

The HTTP API behind the Ledger mobile app: accounts, entries and monthly totals, stored in Postgres.

    pnpm install
    cp .env.example .env
    pnpm run db:migrate
    pnpm dev

The API listens on port 3000. See `Design Docs/api.md` for the endpoints.
