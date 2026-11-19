# Reviewing memories

From Claude Code's docs (https://code.claude.com/docs/en/memory#auto-memory), the memory section of Claude's system prompt, and the global-memory plugin's README.

## The two memory stores

- **Auto memory**: notes Claude writes for itself in the folder its system prompt names, normally `~/.claude/projects/<project>/memory/`. A repo has one folder, which its worktrees share, and it stays on this machine. `MEMORY.md` is the index, one line per memory. Claude Code loads its first 200 lines or 25 KB, whichever comes first, at the start of every session. A memory file loads only when Claude opens it, so a file that the index doesn't list is never seen at startup.
- **Global memory**: the global-memory plugin's store, in `~/.claude/memory/` (or `$CLAUDE_CONFIG_DIR/memory/`), for facts that hold in every project. It has the same index and file format, with these differences: the types are `user`, `feedback` and `reference`, with no `project`; a file's `name` is its file name; a file is at most 4,096 bytes and 200 lines; and an index line is at most 150 characters. Change it only with the `global_memory_write` and `global_memory_delete` tools.

The format of a memory file and of its index line is in the memory section of Claude's system prompt. Check each file against that format, so the review follows the Claude Code version that runs it.

## Verdicts

Give each memory one verdict, with its evidence.

- **Keep**: true, needed and in the right place.
- **Update**: still needed, but part of it has changed. Give the new text.
- **Merge**: says what another memory says. Give the merged text and the file that stays.
- **Delete**, for one of these reasons:
  - Claude can find it in the repo: architecture, file paths, code structure, a past fix or git history.
  - A loaded CLAUDE.md file already says it. Give the `file:line`.
  - It is no longer true: a file, function, command, flag or setting it names is gone, or the work it describes is finished or dropped. Check `git log`.
  - It mattered only in the conversation that saved it.
- **Move**: it belongs in another file. Give the text for the target.
  - A convention, gotcha or decision that a teammate would need too goes to the project `CLAUDE.md`, or to a rule with `paths`. Leave out anything personal.
  - A fact that holds in every project goes to the global memory if the plugin is installed, or else to `~/.claude/CLAUDE.md`.
  - A global memory the user confirms has held up goes to `~/.claude/CLAUDE.md`, and the memory is deleted.
  - A rule that must hold every time goes to a hook or a permission rule (`skills-and-hooks.md`).

## Also check

- **Index**: every line links to a file that exists, every file has a line, and the index fits in 200 lines and 25 KB. The check script reports these.
- **Frontmatter**: the fields and types in the system prompt's format. The check script reports a missing field or an unknown type.
- **Body**: one fact per file. A feedback or project memory gives its reason and how to apply it. Dates are absolute, such as 2026-03-05, not "last week".
- **Privacy**: a memory may hold the user's name or other details. Don't carry them into a shared file.

## Don't

- Delete a memory only because it's old. Check it first.
- Rewrite a sound memory only to change its style.
- Change another project's memories without approval. When a preference moves to `~/.claude/CLAUDE.md`, list its copies in other projects as optional deletions.
