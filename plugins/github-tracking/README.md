# github-tracking

Keeps a repo's GitHub issues, milestones and Projects board true while Claude works, so you can see on GitHub where a project stands instead of asking. Two skills: `/github-tracking:init` sets up a repo's board, and `track` says how the board works. Claude loads track whenever it opens, starts, files or finishes an issue or PR in a repo with a GitHub remote, or you ask where a project stands. You can also run it as `/github-tracking:track`.

```
/plugin install github-tracking --marketplace astrosteveo/astro-plugins
```

## Set up a repo

```
/github-tracking:init
```

Run it in a repo with a GitHub remote, or ask Claude to set up a board. It makes a Projects board and links it to the repo, gives it its views, checks the board's workflows and puts the open issues on the board. On a repo that already has a board, it adds only what's missing, so running it on an older board gives the board its views. It makes no labels or milestones.

## What the skills cover

The track skill tells Claude how the board works and how to change it:

- `board.py` moves an issue or PR to a status, adding it to the board first, because the API can't turn on a board's auto-add workflow.
- A PR whose body says `Closes #N` closes the issue when it merges, and the board's workflows move both to Done.
- A milestone stays open after its last issue closes, until something closes it.
- `board.py show` says where the board stands and marks what's out of step: a closed item that isn't Done, an open one that is, workflows that are off and views the board lacks.
- When a repo has no board, Claude offers to set one up with `/github-tracking:init`, and remembers if you say no.

The skills don't say how to work. Which work gets an issue, how issues are labelled and put in milestones, when to post a status update, and how to branch and commit are yours to set in your own CLAUDE.md and the repo's rules. For example:

```markdown
# Tracking work
In a repo on GitHub, track the work in its issues and the Projects board linked to it:
- Every change I commit gets an issue. Move it to In Progress on the board when you start it.
- A PR's body says `Closes #N` for each issue it finishes.
```

## The script

`scripts/board.py` makes the board's API calls through the `gh` CLI, for both skills. It finds the board linked to the repo and that board's Status field, so no CLAUDE.md keeps a project's ids.

```
board.py show                       # open milestones, items not done, workflows off, the latest status update
board.py move 12 "In Progress"      # an issue or PR by number or URL, added to the board if it isn't there
board.py sub 10 11 12               # 11 and 12 become sub-issues of 10
board.py update on-track FILE       # a status update: on-track, at-risk, off-track, complete or inactive
board.py views                      # the board's views of its open work, milestones and recently done issues
```

`--repo OWNER/NAME` works on another repo's board, and `--project NUMBER` picks one when a repo has several. It needs `gh` signed in with the `project` scope (`gh auth refresh -s project`) and Python 3.11 or later. Stdlib only.

## Views

A new board has one view, "View 1": a table of every issue and PR, done or not. `views` gives the board three views of its issues instead, each showing an issue's PRs in its row:

| View | Shows |
| --- | --- |
| Open work | Open issues on a board, a column per status, with labels, milestone, PRs and sub-issue progress |
| Milestones | Open issues grouped by milestone, with status, labels, PRs and sub-issue progress |
| Recently done | Issues closed in the last two weeks, with labels, milestone and the PRs that closed them |

It adds only the ones the board lacks, by name, and removes View 1 if no one has changed it, so the board opens on Open work. `show` lists the ones a board is missing, and `/github-tracking:init` adds them. GitHub's API can't show or sort by the Created, Updated or Closed dates, so Recently done keeps to two weeks rather than putting the newest first.

## Workflows

The board's own workflows do part of the job: Item closed and Pull request merged move items to Done, and Auto-add sub-issues puts a step's sub-issues on the board. A new board has them on. `show` lists any that are off, and the API can't turn one on, so you switch them on in the board's Workflows settings.

## Tests

```
python3 -m unittest discover -s plugins/github-tracking/tests
claude plugin validate plugins/github-tracking
```
