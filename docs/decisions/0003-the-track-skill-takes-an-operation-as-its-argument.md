# The track skill takes an operation as its argument

Status: accepted 2026-11-18 · [#169](https://github.com/astrosteveo/astro-plugins/issues/169)

## Context

`/github-tracking:track` takes no arguments. Its frontmatter has no `argument-hint` and its body has no `$ARGUMENTS`, so when the user types words after it, Claude Code appends them to the end of the skill as `ARGUMENTS: ...`, and the skill doesn't say what to do with them. To see the board or file an issue, the user writes the request in words, and Claude works out from the skill which commands to run.

docs-site's `/docs-site:hub` already takes its command as its argument, such as `/docs-site:hub stop` ([0002](0002-the-hub-starts-and-stops-with-hub-py.md)).

## Decision

The track skill takes an operation as the first word of its argument. Its `argument-hint` lists them, so the slash menu shows them:

```
argument-hint: "[show | file DESCRIPTION | start ISSUE | move ITEM STATUS | sub PARENT ISSUE... | update STATUS [FILE]]"
```

| Argument | What Claude does |
| --- | --- |
| None | What it does now: loads the rules and does what the user asked. |
| `show` | Runs `board.py show` and says where the project stands: what's in progress, what's next, and anything `show` marks as out of step, with the command that fixes each. |
| `file DESCRIPTION` | Writes an issue from the description by the skill's rules: a lowercase title that starts with the scope, a type label, and Problem, Goal, Acceptance criteria and Open questions. Files it with `gh issue create`, puts it on the board at Todo with `board.py move`, and gives its URL. It asks first only when the description doesn't say what's wrong or what to change. |
| `start ISSUE` | Reads the issue, moves it to In Progress, and starts work on it by the user's own rules for branches and plans. If another issue is in progress, it asks whether to move that one back to Todo first. |
| `move`, `sub` or `update` | Runs that `board.py` command with the rest of the argument. `update STATUS` with no file writes the update's body from `show` and the PRs merged since the last update. |

- Typing the argument is the request, so `file`, `start`, `move`, `sub` and `update` change GitHub without asking again.
- The skill pre-approves no new commands. `gh issue create` and `gh label create` still ask for permission outside bypass mode, as they do now when Claude files an issue on its own.
- The body says what the skill was invoked with in one line, as project-md's review skill and bug-hunt's hunt skill do. An argument whose first word isn't an operation, such as `/github-tracking:track what's left before 0.7`, is a request in words, handled as with no argument.
- The description stays as it is. Claude loads the skill by its description, with no argument, before every change.
- `board.py` doesn't change.

## Turned down

- A skill per operation, such as `/github-tracking:show` and `/github-tracking:file`. Each would repeat or point to the track skill's rules, and the plugin would carry seven skills where three do.
- A `board.py file` command that creates the issue and adds it to the board in one call. `gh issue create` and `board.py move` already do it in two, and Claude writes the title and body either way.
- Pre-approving `gh issue create`. Claude loads track on its own before every change, so the approval would also cover issues it files without being asked.
- A `done ISSUE` operation. The board's Item closed and Pull request merged workflows already move an item to Done.
- Showing the issue as a draft before filing it. The user typed what to file, and an issue can be edited or closed after it's filed.

## Consequences

- github-tracking 0.7.0. The README lists the operations.
- `test_skill.py` checks that each operation in `argument-hint` has its row in the skill, and that each `board.py` command the skill names is one `board.py` has.
- A request in words that starts with an operation's name runs that operation: `/github-tracking:track show me what's left` runs `show`.
