---
name: track
description: Use in a repo with a GitHub remote before you start a change, before you open, start, file or finish an issue or PR, and before you say where a project stands. Says which work gets an issue and how to write one, how the repo's issues, milestones and GitHub Projects board work, and how its script moves items, makes sub-issues and posts status updates, so the board stays true as you work. When the repo has no board, it offers /github-tracking:init.
argument-hint: "[show | file DESCRIPTION | start ISSUE | move ITEM STATUS | sub PARENT ISSUE... | update STATUS [FILE]]"
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/board.py *)
---

# Track work on GitHub

This skill was invoked with: `$ARGUMENTS`

A repo's work on GitHub is its issues, its milestones, and a Projects board linked to the repo. Each issue and PR on the board has a Status: Todo, In Progress or Done. The user reads the board to see where the project stands, so keep it true as you work. An issue still at In Progress a day after its PR merged misleads them.

`board.py` makes the board's API calls through `gh`. It finds the board linked to the repo you're in and that board's Status field, so no CLAUDE.md needs to keep a project's ids. Pass `--repo OWNER/NAME` to work on another repo's board, and `--project NUMBER` when a repo has more than one.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/board.py show                    # where the board stands
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/board.py move 12 "In Progress"   # an issue or PR, by number or URL
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/board.py sub 10 11 12 13         # 11, 12 and 13 become sub-issues of 10
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/board.py update on-track FILE    # a status update, its body from FILE or - for stdin
```

## Run it with an argument

When the first word of the skill's argument is one of these operations, do what its row says. The argument is the user's request, so don't ask before changing GitHub, except where a row says to.

| Argument | What to do |
| --- | --- |
| `show` | Run `board.py show`, and say where the project stands: what's in progress, what's next, and anything `show` marks as out of step, with the command that fixes each. Words after `show` say what to report on. |
| `file DESCRIPTION` | Write an issue from the description by the rules below, file it with `gh issue create`, put it on the board at Todo with `board.py move`, and give its URL. Ask first only when the description doesn't say what's wrong or what to change. |
| `start ISSUE` | Read the issue with `gh issue view`, move it to In Progress, and start work on it by the user's own rules for branches and plans. If another issue is in progress, ask whether to move that one back to Todo first. |
| `move ITEM STATUS`, `sub PARENT ISSUE...` or `update STATUS [FILE]` | Run that command of `board.py` with the rest of the argument. For `update` with no file, write the body from `show` and the PRs merged since the latest status update. |

With no argument, or one whose first word isn't an operation, do what the user asked by the rest of this skill.

## Which work gets an issue, and how to write one

These are the user's rules in every repo. Where a repo's own rules say otherwise, such as its CLAUDE.md or its issue forms, follow the repo.

- Every change you commit gets an issue, except a trivial fix such as a typo or a one-line change. Move it to In Progress on the board when you start it.
- Keep one issue in progress at a time: finish it, or move it back to Todo, before starting another.
- Work you find along the way gets its own issue instead of growing the current change, unless it's trivial.
- A PR's body says `Closes #N` for each issue it finishes.
- Write each issue so someone who wasn't in the conversation can start on it:
  - Title: the commit scope and what to change, in lowercase, such as `docs-site: add a switcher on each hub site`. The commit type goes in a label (`feat`, `fix`, `docs`, `test`, `chore` or `refactor`), not the title. Make the label with `gh label create` if the repo lacks it, and add the repo's other labels where they fit.
  - Body, under these headings in this order, the same ones the user's GitHub issue forms use:
    1. `### Problem`: what's wrong or missing, and the evidence: where it was found (link the issue or PR), the command and its output, or the numbers.
    2. `### Goal`: what to change, in a sentence or two, as the result the user gets. Leave how to build it to the plan unless the cause is already known.
    3. `### Acceptance criteria`: a checklist (`- [ ]`). Each item is one result that will be true when the issue is done, that someone can check as pass or fail, and that says how to check it: a named test, a command and the output it prints, or a screenshot. Give numbers for speed, size or counts. Include what must stay as it is when the change could break it. Describe the result, not how it's built.
  - When a repo's issue form has other sections, such as Steps to reproduce, keep them after Problem.
  - When the work changes what the issue delivers, update its Goal and criteria in the issue.
  - Tick each criterion in the issue once you've checked it, before the PR that closes the issue merges.
  - A trivial issue can cover Problem and Goal in one sentence each, with one criterion.

Branches, commits, merges and status updates follow the user's own rules and the repo's.

## What GitHub does on its own, and what it doesn't

- A new issue or PR isn't on the board until something adds it, and the API can't turn on a board's auto-add workflow. `move` adds an item that isn't on the board yet, at the status you give.
- A PR whose body says `Closes #N` closes issue N when it merges, and the board shows the PR in the issue's row.
- The board's Item closed and Pull request merged workflows move an item to Done when it closes or merges. A new board has them on, and `show` lists any that are off. The API can't turn one on: the user switches it on in the board's Workflows settings.
- The board's Auto-add sub-issues workflow puts the sub-issues `sub` makes on the board. Only an issue can be a parent or a sub-issue, not a PR.
- A milestone stays open after its last issue closes. Close it with `gh api -X PATCH repos/OWNER/NAME/milestones/M -f state=closed`.
- A status update is a short post on the board, with one of `on-track`, `at-risk`, `off-track`, `complete` or `inactive`. The newest one shows at the top of the board. Write its body to a file and pass the file, or `-` to read it from stdin.

## Saying where things stand

`board.py show` prints the board's URL, its open milestones with how many of their issues are closed, every item that isn't done grouped by status, and the latest status update. Answer from it, with `gh pr list` and git, rather than opening issues one by one.

`show` also marks what's out of step:

- `(closed)` or `(merged)` after an item that isn't at Done, and `(open)` after an open item at Done. Fix each with `move`.
- `Workflows off:` the board's workflows that are switched off.
- `Views missing:` the board's views of open work, milestones and recently done issues that it lacks. `/github-tracking:init` adds them, and only them.

## Errors

- If `gh` says it lacks the `project` scope, ask the user to run `! gh auth refresh -s project`.
- If `board.py` says the repo has several boards, ask the user which one and pass `--project NUMBER` from then on.

## A repo with no board

When `board.py` says no board is linked to the repo, offer to set one up. If the user says yes, set it up with the init skill (`/github-tracking:init`). If they say no, save that in the project's memory, and don't offer again in that repo.

## A repo with corkboard's .project/ folder

corkboard kept a repo's work as Markdown items in `.project/`. When a repo you're tracking on GitHub still has `.project/items`, offer to move them to issues with the migrate skill (`/github-tracking:migrate`), which shows what it would change before it changes anything.
