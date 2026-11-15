# Testing

- Put tests in `tests/`, never next to the source file. Vitest's config and CI only look there.
- Integration tests go in `tests/integration/` and run with `pnpm run test:integration`.
