---
name: track
description: Use in a repo with a GitHub remote before you open, start, file or finish an issue or PR, and before you say where a project stands. Says how the repo's issues, milestones and GitHub Projects board work, and how its script moves items, makes sub-issues and posts status updates, so the board stays true as you work. When the repo has no board, it offers /github-tracking:init.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/board.py *)
---

# Track work on GitHub

A repo's work on GitHub is its issues, its milestones, and a Projects board linked to the repo. Each issue and PR on the board has a Status: Todo, In Progress or Done. The user reads the board to see where the project stands, so keep it true as you work. An issue still at In Progress a day after its PR merged misleads them.

`board.py` makes the board's API calls through `gh`. It finds the board linked to the repo you're in and that board's Status field, so no CLAUDE.md needs to keep a project's ids. Pass `--repo OWNER/NAME` to work on another repo's board, and `--project NUMBER` when a repo has more than one.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/board.py show                    # where the board stands
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/board.py move 12 "In Progress"   # an issue or PR, by number or URL
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/board.py sub 10 11 12 13         # 11, 12 and 13 become sub-issues of 10
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/board.py update on-track FILE    # a status update, its body from FILE or - for stdin
```

Which work gets an issue, how issues are labelled, titled and put in milestones, when to post a status update, and how to branch and commit follow the user's own rules and the repo's. This skill doesn't decide them.

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
