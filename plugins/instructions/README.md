# instructions

`/instructions:init` sets up CLAUDE.md files: a project's `CLAUDE.md`, your private `CLAUDE.local.md` for it, and your global `~/.claude/CLAUDE.md`, which loads in every project. It can add skills and hooks too. It's a fork of Claude Code's new `/init` (`CLAUDE_CODE_NEW_INIT=1`, as of 2.1.325) with three changes: it shows every draft before it asks you to approve it, it covers the global file, and it checks every file against Claude Code's docs on writing CLAUDE.md, with Claude Code's own prompt audit on each file it reviews.

```
/plugin install instructions --marketplace astrosteveo/astro-plugins
```

## Use

```
/instructions:init
```

Or ask Claude to set up or redo a CLAUDE.md. For a one-line change to one of these files, ask for the change instead.

| Step | What Claude does |
| --- | --- |
| Start | Prints a short primer, checks which of the three files exist, and asks which to set up. Pick any of Project, Personal and Global, or "Let Claude decide" |
| Choose | For each picked file that exists, asks whether to review and improve it or start fresh, and whether to set up skills and hooks too |
| Explore | A subagent surveys the repo, and lists the other instruction files that load with yours. For the global file, another surveys your Claude Code settings, output style and memories, the projects your recent sessions ran in, your machine's tools and shell, and the corrections you gave in your last 40 sessions. That survey reads a lot: it took 13 minutes in testing. For each file you review, a third runs the prompt audit that `/doctor prompt-audit` runs |
| Fill gaps | Asks only what the files can't answer, each question with the evidence it rests on |
| Draft | Checks every draft and every file under review against the checks below. Shows each new file in full and each edit to an existing file as a diff headed with the line it changes and the check it fixes, then a "Checked" line with the numbers. Lists the skills, hooks and permission rules, then stops and waits for your reply |
| You reply | Answer "write it", pick edits by number ("1, 3"), or say what to change. Nothing is written before that |
| Write | Writes the files. Before changing `~/.claude/CLAUDE.md` it copies it to `~/.claude/CLAUDE.md.bak`. It reads each file back and checks its imports and the paths it names. Then it creates the skills, hooks and permission rules, offers the GitHub CLI and linting if they're missing, and ends with how to confirm the files load (`/context all` in a new session) and a short to-do list |

## What the review checks

Each check comes from Claude Code's [memory](https://code.claude.com/docs/en/memory#write-effective-instructions) and [best practices](https://code.claude.com/docs/en/best-practices#keep-claude-md-short) docs:

- **Size**: under 200 lines. Imports don't lower the cost.
- **Structure**: headings and bullets, not paragraphs, each rule with its reason.
- **Header**: the project file and the global file start with `# CLAUDE.md` and a line saying where the file applies, the way `/init` starts a project file. A review adds the header when it's missing.
- **Specific**: concrete enough to check, at normal volume, with no "IMPORTANT" or "try to".
- **Place**: a rule that must always hold goes in a permission rule or hook, a procedure in a skill, a rule for one part of the code in `.claude/rules/` with `paths`, and personal or every-project lines in their own files.
- **Not in the code**: no directory trees, dependency lists or architecture tours.
- **True, consistent and current**: every path and command exists, nothing contradicts a file that loads alongside, and no history.
- **Imports and rule files**: `@` paths resolve, spaces escaped, and rule frontmatter parses.
- **Git rules**: flags git rules that compete with Claude Code's own while `includeGitInstructions` is on.

It doesn't cut a line only to save space when Claude can't learn it from the code. On a file it reviews, the prompt audit adds Claude Code's check for instructions written for older models. If the bundled `claude-api` skill is turned off, the review says so in one line and uses the checks alone.

Where things go:

| You picked | CLAUDE.md file | Skills | Hooks |
| --- | --- | --- | --- |
| Project | `./CLAUDE.md` | `.claude/skills/` | `.claude/settings.json` |
| Personal | `./CLAUDE.local.md`, added to `.gitignore` | `.claude/skills/` | `.claude/settings.local.json` |
| Global | `~/.claude/CLAUDE.md` | `~/.claude/skills/` | `~/.claude/settings.json` |

## Why a fork

The new `/init` tells Claude to print its proposal as text and then ask "Does this look right?" with AskUserQuestion, in the same turn. By then the turn has already run tools, and in that spot Claude writes the proposal only in its thinking. Claude Code shows the thinking as one line ending in `· summary`, so you're asked to approve a proposal you never saw. Tested on 2.1.325 with a request to print a draft and then ask:

| Setup | Draft on screen |
| --- | --- |
| No tool call first | 3 of 3 runs |
| One tool call first | 0 of 3 |
| One tool call first, and the draft is the reply that ends the turn | 3 of 3 |

A full `/init` run left the proposal out with the plain-english output style on and with it off. `/init`'s primer, printed after its first read, was left out in 5 of 5 runs.

So this fork prints the primer before any tool call, and shows every draft and edit list as its reply and ends the turn there. It asks with AskUserQuestion only for choices that stand on their own. `/init` also writes only project files: its first question has no option for the global file.

This plugin goes once `/init` shows its proposals and covers the global file.

## How well it reviews

`tests/fixtures/` holds two small repos with known defects, listed in [its README](tests/fixtures/README.md). Scored on Claude Code 2.1.325, one run each, with the same answers to every question:

| | 0.1.0 | 0.2.0 |
| --- | --- | --- |
| review-me: 11 seeded defects caught | 9 | 11 |
| review-me: lines it must keep (3) | cut 1 | kept all 3 |
| review-me: what it missed | `.env` rule belongs in a deny rule, release steps belong in a skill | nothing |
| dot-claude: found the project file at `.claude/CLAUDE.md` | yes, though its instructions said only the root file counts | yes |
| dot-claude: edits to a file meant to be sound | 2 | 2, the same main one |
| review-me: session cost up to the edits | $2.56 | $3.86 |

The prompt audit is most of the extra cost: about 6 minutes in a subagent.

## Tests

```
python3 -m unittest discover -s plugins/instructions/tests
claude plugin validate plugins/instructions
```

To score the review yourself, build a fixture repo with `python3 plugins/instructions/tests/fixture_repo.py review-me <folder>`, run `/instructions:init` in it, and check the reply against `tests/fixtures/README.md`.
