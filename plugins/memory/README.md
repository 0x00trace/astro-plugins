# memory

`/memory:init` sets up and reviews the files Claude Code loads as memory, by the rules in Anthropic's docs:

- a project's `CLAUDE.md` and `.claude/rules/`
- your `CLAUDE.local.md` for one project
- your global `~/.claude/CLAUDE.md` and `~/.claude/rules/`
- the memories Claude saves for itself: the project's auto memory, and your global memory if the [global-memory](../global-memory) plugin is installed

Like Claude Code's `/init`, it can also add skills, hooks and permission rules. It shows every change first and writes only what you approve.

```
/plugin install memory --marketplace astrosteveo/astro-plugins
```

## Use

```
/memory:init
/memory:init project memory
```

With no arguments, it asks what to work on. The arguments `project`, `personal`, `global`, `memory` and `extras` (skills, hooks and permission rules) skip that question. You can also ask Claude to set up or review a CLAUDE.md or your memories.

| Step | What Claude does |
| --- | --- |
| Take stock | Runs the check script, which lists every instruction and memory file that loads for the project, with its size and the problems it can find for certain |
| Ask | Asks which files to set up or review, and whether to look for skills, hooks and permission rules |
| Survey | Subagents read the repo, your Claude Code setup, or your memories, depending on what you picked. They only read |
| Ask again | Asks only what the files can't answer, with the evidence for each question |
| Propose | Shows each new file in full, each edit as a diff with the check it fixes, each memory change with its evidence, and each skill, hook and permission rule. Then it stops and waits |
| Write | Writes what you approve: reply "write it", or pick items by number. It copies `~/.claude/CLAUDE.md` to `~/.claude/CLAUDE.md.bak` before changing it, and changes the global memory only through its own tools |
| Check | Runs the check script on what it wrote, and says how to confirm the files load with `/context all` |

## What it checks

The checks come from Claude Code's [memory](https://code.claude.com/docs/en/memory) and [best practices](https://code.claude.com/docs/en/best-practices) docs:

- **CLAUDE.md files**: under 200 lines with imports; only what Claude can't learn from the repo; concrete lines at normal volume; true, consistent and current; each line in the right place, so a rule that must always hold becomes a hook or a deny rule, a procedure a skill, and a rule for one part of the code a rule file with `paths`.
- **Imports and rules**: `@` imports resolve within four hops, spaces are escaped, and rule frontmatter parses and has only `paths`.
- **Memories**: the `MEMORY.md` index matches the files and fits in the 200 lines or 25 KB that load; each memory is still true, isn't already in a CLAUDE.md file and isn't something Claude can read from the code; and memories that belong in a CLAUDE.md file, or in every project, move there.

Skills follow Anthropic's [skill guide](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).

## The check script

`skills/init/scripts/check.py` makes the checks that must be exact: line counts, import paths, rule frontmatter, the memory index and the paths a file names. It needs Python 3.11 or later and nothing outside the standard library, and it only reads files. To run it yourself in a project:

```
python3 plugins/memory/skills/init/scripts/check.py --memory-dir ~/.claude/projects/<project>/memory
```

## Tests

```
python3 -m unittest discover -s plugins/memory/tests
claude plugin validate plugins/memory
```

The tests cover the check script. The skill itself was checked in a live session.
