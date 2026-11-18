---
name: migrate
description: Find a repo's corkboard setup (a .project/ folder) and what older github-tracking boards left behind, show what migrating would change, and migrate once the user approves - corkboard's open items become issues on the repo's board, its releases milestones and its epics parent issues with sub-issues, item IDs in the repo's Markdown become links, .project/docs/ moves to docs/, and the board gets linked, its views, and closed items at Done. Use when the user asks to migrate a repo from corkboard, move .project/ items to GitHub, or clean up an old board setup, or a repo with a GitHub remote still has a .project/ folder.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/migrate.py scan), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/migrate.py scan *), Bash(git log *), Bash(git show *)
---

# Migrate a repo to GitHub tracking

corkboard kept a repo's work as Markdown files in `.project/`: releases, epics, tasks and bugs (items, with IDs such as `EX-12`), and docs in `.project/docs/`. github-tracking keeps it on GitHub instead, in issues, milestones and a Projects board linked to the repo. `migrate.py` moves one to the other and fixes what older github-tracking boards left behind. Done and cancelled items aren't moved: they stay in git history.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/migrate.py scan    # reads only: what it found and what run would do
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/migrate.py run     # does it
```

`run` changes GitHub and the repo's files, so it runs only after the user approves the plan `scan` printed. Pass `--project NUMBER` to both when the repo has several boards. If `gh` says it lacks the `project` scope, ask the user to run `! gh auth refresh -s project`.

What `run` does:

- **Board:** links a project that has the repo's name but isn't linked, or makes one, then adds the views the board lacks. It moves closed issues and PRs that aren't at Done to Done, and closes milestones whose issues are all closed.
- **Items:** each open item becomes an issue with its description, its subtasks as a checklist, its log in a folded section, and a last line saying which item it was. Its labels come along, and a bug gets `bug`. `in-progress` and `waiting` items go on the board as In Progress, `todo` and `backlog` ones as Todo.
- **Links between items:** a release with open items becomes a milestone, an epic's open tasks and bugs become its sub-issues, and `blocked_by` an open item becomes GitHub's blocked-by link.
- **IDs:** each item ID in the repo's Markdown and in the new issues becomes a link: an open item's to its issue, a done item's to the merged PR whose title names it. IDs in code stay as they are.
- **Files:** `.project/docs/` moves to `docs/` with `git mv`, with the links to and from it fixed. `.project/items`, `releases` and `config.yml` are removed, and so are `.project/` lines in ignore files such as `.prettierignore`.

Each issue it opens carries a hidden `<!-- corkboard: EX-12 -->` marker, so a second run finds it and opens nothing twice. `run` commits nothing.

## 1. Scan

Run `scan` in the repo. If the repo has no `.project/` but its Markdown names IDs such as `AP-12`, it may have used corkboard before: `git log -1 --format=%h -- .project/config.yml` prints the commit that removed it, and `git show HASH^:.project/config.yml` its `prefix`. Then scan with `--prefix PREFIX`, which links those IDs to the PRs that name them.

If it prints `Nothing to migrate.` and nothing for the user to look at, say so and stop.

## 2. Show the plan

The scan's `For you to look at` lists what it won't change itself: a line in a file that names corkboard, such as a CLAUDE.md rule or a `.claude/settings.json` entry, a board workflow that's off, an out-of-date status update. For each line that names corkboard, write the edit you'd make, so the user can approve it along with the rest.

Show the scan's plan and your edits as your reply, and end your turn there. Don't ask with a question dialog: the user needs to read the plan before answering.

## 3. Migrate

Once the user approves, run `run` with the same options. It prints each step as it does it, and each issue it opens. If it stops on an error, fix the cause and run it again: it picks up where it stopped.

Then make the edits the user approved. If `docs/` now has pages and the repo has no `mkdocs.yml`, and the docs-site plugin's `/docs-site:init` is available, run it so the docs have a site.

## 4. Report

Say what changed on GitHub, with the board's URL, and which files changed. `git status` shows the file changes, which are left for the user's own rules on branches and commits.
