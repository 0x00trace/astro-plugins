# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Build: `make build`, which writes `bin/notes`
- Test everything: `make test`
- Run one test: `go test ./internal/store -run TestAdd`
- Lint: `make lint`, which runs `go vet` and `staticcheck`

## Conventions

- Wrap every returned error with `fmt.Errorf("<what failed>: %w", err)`, because the CLI prints the whole chain as its only error message.
- A change to the `Note` struct changes the file format: bump `currentVersion` and add the upgrade step to `internal/store/migrate.go` in the same commit, or existing notes stop loading.

## Gotchas

- Tests set `NOTES_DIR` to `t.TempDir()`. Never point a test at `~/.notes`, which holds real notes.
