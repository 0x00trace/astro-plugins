---
name: init
description: Sets up and reviews the files Claude Code loads as memory, by the rules in Anthropic's docs - a project's CLAUDE.md and .claude/rules/, a personal CLAUDE.local.md, the global ~/.claude/CLAUDE.md, and the memories Claude saves for itself (auto memory, and the global memory where that plugin is installed). Also proposes skills, hooks and permission rules. Shows every change and writes nothing until the user approves. Use when the user asks to set up, start, redo, clean up or review a CLAUDE.md, CLAUDE.local.md, rules file or their memories.
argument-hint: "[project] [personal] [global] [memory] [extras]"
allowed-tools: Read, Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/check.py), Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/check.py *), Bash(git log *), Bash(git worktree list)
---

# Set up CLAUDE.md and memory files

Claude Code loads these files into every session, or when Claude works in the folder they cover. Every line costs context in every session, and a long file is followed less closely. The goal is short, true files that hold only what Claude can't learn from the repo and would get wrong without them.

| Target | Files | For |
| --- | --- | --- |
| project | `CLAUDE.md` or `.claude/CLAUDE.md`, `.claude/rules/`, `CLAUDE.md` files in subfolders | everyone who clones the repo |
| personal | `CLAUDE.local.md`, gitignored | the user, in this repo |
| global | `~/.claude/CLAUDE.md`, `~/.claude/rules/` | the user, in every project |
| memory | this project's auto memory folder, and `~/.claude/memory/` if the global-memory plugin is installed | Claude itself |
| extras | skills, hooks and permission rules | the repo or the user |

## Rules for the whole run

- Write nothing until the user approves the proposal in Step 5. Reading files and running the check script is fine.
- Put the proposal in your reply and end your turn there. Don't ask for approval with AskUserQuestion: the user answers in their next message and can pick items by number.
- Use AskUserQuestion only for questions that stand on their own. Each one names what it's about and the evidence it rests on.
- Every line you propose comes from a file you read or from the user. Don't invent commands, facts or sections.
- Never write secrets, tokens or passwords into these files. Keep names and emails out of files that are shared.

## Step 1: Take stock

Run the check script before anything else, with the auto memory folder that your system prompt names:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/check.py --memory-dir <auto memory folder>
```

Leave out `--memory-dir` if your system prompt has no auto memory section. The script lists every instruction and memory file that loads for this project, with its size, and reports the problems a script can find for certain: imports that don't resolve, files over 200 lines, rule frontmatter that doesn't parse, index lines and memory files that don't match, and paths named in code spans that don't exist. Keep its output for the later steps.

If `python3` is missing or older than 3.11, find and read the files yourself and make these checks by hand.

## Step 2: Ask what to work on

Arguments given: $ARGUMENTS

If the arguments name targets from the table, work on those and skip this step. Otherwise call AskUserQuestion with these two questions:

1. "Which files should we set up or review?", with `multiSelect: true`:
   - "Project CLAUDE.md": "Shared with everyone who clones the repo: commands, conventions, gotchas. Includes .claude/rules/."
   - "Personal CLAUDE.local.md": "Yours only, in this repo, and gitignored: your setup, sandbox URLs, how you work here."
   - "Global ~/.claude/CLAUDE.md": "Yours in every project: environment, tools, workflow, how you want answers. Includes ~/.claude/rules/."
   - "Memories": "What Claude saved for itself, in this project and in your global memory. Finds stale, duplicate and misplaced memories."

   End each description with what Step 1 found, such as "Exists, 64 lines.", "None yet." or "12 memories, 2 problems." If the folder isn't a git repo, say so in the question: a CLAUDE.md here loads in every session started in this folder or below it.
2. "Also look for skills, hooks and permission rules?":
   - "Yes": "Turn repeated multi-step workflows into skills, and rules that must always hold into hooks or permission rules."
   - "No": "Only instruction and memory files, plus any hook or rule that a moved line needs."

A file that exists is reviewed and improved, not replaced. If the user wants one started over, they can say so when they reply to the proposal.

## Step 3: Survey

Read the reference for each target, in `${CLAUDE_SKILL_DIR}`:

- `writing-claude-md.md` for project, personal or global.
- `reviewing-memory.md` for memory.
- `skills-and-hooks.md` for extras, and whenever a line or a memory belongs in a skill, hook or permission rule.

Then start the surveys the targets need, in parallel, as general-purpose subagents. Give each one its brief, the Step 1 output and these rules: read only; edit and delete nothing; read files with the Read, Grep and Glob tools, not shell loops, which ask for permission each time; use Bash only for git; run nothing that installs, builds or runs the project's code; give the file and line behind each fact; end with what it couldn't find out.

**Repo survey**, for project, personal or extras:

> Survey the repo at `<path>` for its CLAUDE.md files. Read the manifests (package.json, pyproject.toml, Cargo.toml, go.mod and others), the README, the Makefile and other task runners, CI config, formatter and linter config, `.claude/settings.json`, `.claude/skills/`, and every instruction file in the list. Report: the build, test, lint and format commands, how to run one test, and which are non-standard; conventions that differ from the language's or tool's defaults; gotchas such as misleading names, generated files, required env vars or services, and steps that must run in order; branch, commit and pull request conventions, from `git log --oneline -30`; what other tools' instruction files say that is still true; procedures with several steps, such as a release or a deploy; actions that must happen every time, such as formatting after an edit, or files that must never be touched; and for each line of the existing CLAUDE.md files, whether what it names exists and whether the repo already makes it plain.

**Setup survey**, for global:

> Survey how this user works in every project, for their `~/.claude/CLAUDE.md`. Read `~/.claude/settings.json` (hooks, permissions, `outputStyle`, `includeGitInstructions`, `attribution`), `~/.claude/CLAUDE.md`, `~/.claude/rules/`, the names and descriptions of the skills in `~/.claude/skills/`, every project's memories in `~/.claude/projects/*/memory/`, and `~/.claude/memory/` if it exists. Check the machine: the OS and distribution, the shell, and the package managers and toolchains on the PATH. Report: preferences and corrections that appear in the memories of two or more projects, or in the global memory, with each memory's path; facts about the machine that change how commands must be written; and what settings, hooks and rules already cover. Leave out names, emails and secrets.

**Memory survey**, for memory:

> Review Claude's memories for the project at `<path>`. Read `${CLAUDE_SKILL_DIR}/reviewing-memory.md` and apply it to every memory file in `<auto memory folder>` and, if it exists, `<global memory folder>`. The instruction files that load are in the list. Give each memory one verdict from that file, with its evidence: the repo file, `git log` line or CLAUDE.md line that shows it. For update, merge and move, give the new text and where it goes. A memory file follows this format: `<memory format>`

A subagent's system prompt has no memory section, so replace `<memory format>` with the memory file format from yours.

## Step 4: Ask what the files can't answer

Ask with AskUserQuestion, at most four questions per call, and only about what the surveys couldn't find out. Base each question on what you found, such as "The last 30 commits use Conventional Commits, but CONTRIBUTING.md asks for plain sentences. Which is current?" Skip this step when nothing is open.

- Project: commands and gotchas the files don't show, branch and pull request rules, and what counts as done here.
- Personal: the user's role and how well they know this code, their sandbox URLs, test accounts and local setup. If `git worktree list` shows worktrees in sibling folders, ask whether the personal file should reach them.
- Global: when Claude should decide and when it should ask, the default git workflow, and what to check before calling work done.
- Memory: each memory the survey couldn't judge, such as whether a preference holds in every project.

## Step 5: Propose, and end your turn

Check every draft and every file under review against "Checks" in `writing-claude-md.md`, and every memory against `reviewing-memory.md`. Then reply with these parts, numbering the items of parts 3 to 5 in one sequence:

1. One line per target with what you found, such as "CLAUDE.md: 212 lines; 9 edits, 160 lines after them."
2. Each new file in full, in a fenced block under its path.
3. The edits to each existing file. Head each edit with `path:line`, the check it fixes and the evidence, then show it as a `diff` block.
4. The memory changes: each memory's path, its verdict and the evidence. For a move, show the line added to the target file.
5. The skills, hooks and permission rules: what each does, its target file, and its full content.
6. Under each file, a "Checked:" line with the numbers: its lines after the edits, the imports and paths found, and the loaded files it was compared with. Name any check that still fails and say why you left it.
7. A last line asking the user to reply "write it" for everything, to pick items by number ("1, 3, 5"), or to say what to change.

End your turn there. If the user asks for changes, show the changed items the same way and end your turn again.

## Step 6: Write

Write only what the user approved, with the changes they asked for. In a file that exists, make only the approved edits.

- **Project CLAUDE.md**: at its current path. A new one goes at the project root.
- **CLAUDE.local.md**: at the project root. Add `CLAUDE.local.md` to `.gitignore` unless Step 1 showed it's already ignored. If the user wants it in sibling worktrees, write the content to `~/.claude/<project>-instructions.md`, and make each worktree's `CLAUDE.local.md` the one line `@~/.claude/<project>-instructions.md`.
- **~/.claude/CLAUDE.md**: copy it to `~/.claude/CLAUDE.md.bak` before you change it, since it isn't under git, and say where the copy is.
- **Auto memory**: edit or delete the memory files, and update `MEMORY.md` in the same step, so each index line still links to a file and each file has a line. For a move, write the target first, then delete the memory.
- **Global memory**: change it only with the `global_memory_write` and `global_memory_delete` tools, never with file tools: they keep its index and lock in step. Read a memory before you replace it.
- **Skills, hooks and permission rules**: follow `skills-and-hooks.md`.

## Step 7: Check and finish

Run the check script again on each instruction file and memory folder you wrote:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/check.py <path> <path> ...
```

Fix any problem your changes caused. Then tell the user:

- what you wrote, with each file's line count and where any backup is
- what you left and why
- how to confirm the files load: start a new session, run `/context all` and look under "Memory files". A `CLAUDE.md` in a subfolder and a rule with `paths` load only when Claude works with matching files. `/memory` opens these files and the auto memory folder.
- that `/doctor prompt-audit` checks the files later for outdated or conflicting instructions, and that `/memory:init` can review them again

Add a to-do list only for gaps that hold back Claude's work, such as no test command or no linter: Claude uses them to check its own changes.
