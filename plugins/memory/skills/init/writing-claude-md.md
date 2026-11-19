# Writing CLAUDE.md files

From Claude Code's docs: https://code.claude.com/docs/en/memory and https://code.claude.com/docs/en/best-practices.

## How the files load

- At launch: the managed policy file, `~/.claude/CLAUDE.md` and `~/.claude/rules/`, then `CLAUDE.md`, `.claude/CLAUDE.md` and `CLAUDE.local.md` in the working folder and every folder above it, and the files in `.claude/rules/` that have no `paths`. They are joined in that order, from the broadest scope to the most specific. None overrides another: when two disagree, Claude may follow either.
- On demand: a `CLAUDE.md` in a subfolder loads when Claude reads or edits a file in that folder, and a rule with `paths` loads when Claude reads or edits a matching file. Claude gets only the first 40,000 characters of such a file.
- `AGENTS.md` loads only when there is no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` in the working folder or above it. To keep one source, a `CLAUDE.md` can import it with `@AGENTS.md`. A new `CLAUDE.local.md` in a repo that has only `AGENTS.md` stops `AGENTS.md` from loading, so propose a project `CLAUDE.md` with `@AGENTS.md` at the same time.
- Other tools' files (`.cursorrules`, `.cursor/rules/`, `.github/copilot-instructions.md`, `.windsurfrules`, `.windsurf/rules/`, `.clinerules`, `.devin/rules/`) don't load. Carry over what passes the test below.
- Claude treats all of these files as context, not as enforced configuration.

## The test for every line

Keep a line only if Claude can't find it by reading the repo, or would spend time finding it again in every session. Ask two questions: could Claude find this by reading the code, and would it actually go and look? If both answers are yes, cut the line.

Keep:

- How to confirm work here: build, test and lint commands Claude can't guess, and how to run one test.
- Conventions that differ from the language's or tool's defaults.
- Places where the code is misleading.
- Decisions that aren't in the repo, with their reasons.
- Anything the user has had to correct twice.
- Required setup, such as env vars, services and steps that must run in order, and repo etiquette, such as branch names, commit style and pull requests.

Cut:

- Directory layouts, file lists, dependency lists and architecture overviews: Claude reads the repo. Keep a decision behind the architecture if the code doesn't show it.
- Standard conventions and generic advice, such as "write clean code".
- Commands that are plain from the manifests, such as a standard `npm test`.
- History, such as "we moved to pnpm in March". Write the rule as it stands now.
- Long references and walk-throughs. Name the file and say when to read it, or make it a skill.

Don't cut a gotcha, a decision or the reason behind a rule only to save space.

## Where each line belongs

| The line | Goes in |
| --- | --- |
| must hold every time, with no exceptions | a hook or a deny rule: Claude may decide that a CLAUDE.md line doesn't apply. "Never read .env" is the deny rule `Read(./.env)`, and "format after every edit" is a `PostToolUse` hook |
| a procedure with several steps, such as a release | a skill, which loads only when it's used |
| matters for one part of the code | `.claude/rules/<topic>.md` with `paths` |
| matters for one package of a monorepo | that package's own `CLAUDE.md` |
| about the user, in this repo | `CLAUDE.local.md` |
| about the user, in every repo | `~/.claude/CLAUDE.md`, or `~/.claude/rules/<topic>.md` with `paths` for one language |
| already said by a loaded file, a setting, a hook or the output style | nowhere |
| what Claude does anyway | nowhere |

## How to write it

- Under 200 lines per file. An imported file loads with the file that imports it, so it counts toward that file's size.
- Related lines go under markdown headings, as bullets. A rule keeps its reason in the same bullet.
- Concrete enough to check: "Use 2-space indentation", not "Format code properly"; "Run `npm test` before committing", not "Test your changes".
- Normal volume: no "IMPORTANT", capitals or "!!". Emphasis makes Claude apply a rule where it doesn't fit. A line Claude keeps missing is lost in a long file, or belongs in a hook.
- One name for each thing.
- Block-level HTML comments (`<!-- ... -->`) are for notes to people: Claude Code removes them before Claude sees the file.

## Imports

- `@path` imports a file. A relative path resolves from the file that has the import, not from the working folder. Absolute and `~/` paths work too. Imports nest up to four hops.
- Put a backslash before each space: `@Design\ Docs/api.md`. A path in quotes isn't imported.
- An `@` in a code span or a code block isn't an import, so write a package name such as `@types/node` in backticks.
- In a project file, an import from outside the project shows an approval dialog the first time. If the user declines, it never loads.
- An import doesn't save context. For a long document Claude needs only for some tasks, name the file and say when to read it, without the `@`.

## Rule files

- `paths` is the only frontmatter field Claude Code reads. It takes a YAML list or a comma-separated string of glob patterns. Quote a pattern that starts with `*`, as in `- "**/*.ts"`.
- Patterns are relative to the folder that holds `.claude` for a project rule, and to the working folder for a rule in `~/.claude/rules/`.
- If the frontmatter doesn't parse, the rule loads in every session, as if it had no `paths`.
- A rule without `paths` loads at launch like `CLAUDE.md`, and counts toward what every session loads.

## What each file holds

- **Project `CLAUDE.md`**: what everyone who works in the repo needs, from "Keep" above. Nothing personal. If the repo has parts with different commands or conventions, propose a `CLAUDE.md` in each part, or rules with `paths`.
- **`CLAUDE.local.md`**: the user's role and how well they know this code, so Claude can pitch its explanations; their sandbox URLs, test accounts and local setup; and how they want to work in this repo. Keep it short.
- **`~/.claude/CLAUDE.md`**: what holds in every project: the environment (the OS, how to install packages, which toolchains and package managers to use), shell behavior that changes how commands work, workflow defaults (branches, commits, when to ask), what to check before calling work done, and how the user wants answers, unless the output style in your system prompt covers it. Nothing about one project.

## Checks

Make these checks on every draft and every file under review, and name the check in each edit you propose.

1. **Size**: under 200 lines with imports, and a file that loads on demand under 40,000 characters.
2. **Test**: each line passes "The test for every line".
3. **Place**: each line is where "Where each line belongs" puts it.
4. **Specific**: each line is concrete enough to check, at normal volume.
5. **Structure**: headings and bullets, with each rule's reason kept.
6. **True**: every path, command, script and flag the file names exists. Check the manifests and scripts; don't run them. The check script lists the paths that don't exist.
7. **Consistent**: no line contradicts another line, or any file in the Step 1 list.
8. **Current**: no history.
9. **Imports and frontmatter**: the check script reports no problem.
10. **Git**: Claude Code has its own commit and pull request instructions. If the file sets different ones, offer `"includeGitInstructions": false` in the settings, and the `attribution` setting for attribution lines.
