---
name: review
description: Review the repo's PROJECT.md, a committed file that describes the project's purpose, goals, non-goals and constraints. Compares the file with the changes made since it was last committed, and asks the user about work outside the goals, lines that are out of date, and open questions. If the argument names a section, reviews only that section. If the argument describes an idea, checks whether the idea fits the project's scope. Use when the user asks to review, refine or update PROJECT.md or the project's scope or goals, or asks whether an idea fits the project. If the repo has no PROJECT.md yet, use /project-md:init instead.
argument-hint: "[a section to review, or an idea to check against the scope]"
allowed-tools: Bash(git rev-parse *), Bash(git status *), Bash(git log *), Bash(git diff *)
---

# Review PROJECT.md

PROJECT.md is a file at the root of the repo that describes the project: the problem it solves, who it is for, what it will and will not do, and how to tell whether it succeeds. CLAUDE.md contains instructions for working in the repo, and PROJECT.md describes the project itself.

This skill was invoked with: `$ARGUMENTS`

The user may run this skill often. Each run must change PROJECT.md only with the user's approval. If nothing has changed since the previous run, the review must report no findings. Follow these rules to make this work:

- The file has no review date or "last updated" line. The last commit that changed PROJECT.md marks the last review.
- Every finding that the user answers is recorded in the file (step 3), even when the answer is to leave something as it is. Do not raise a finding that the file already answers.
- The file has one copy of each section, in this order: What it is, The problem, Who it's for, Goals, Non-goals, Success looks like, Failure looks like, Priorities, Constraints, Decisions, Open questions, Glossary, Status. Keep any extra sections the file has, and keep the user's wording unless the user approves a change.

## 1. Look at the repo

Run these commands in a single turn:

```
git rev-parse --show-toplevel
git status --short
git log -1 --format='%h %cs' -- :/PROJECT.md
```

If the folder is not a git repo, use the current folder as the repo root, skip the history in step 2, and tell the user that the review cannot see what has changed. If the repo has no commits yet, or PROJECT.md has never been committed, there is no earlier version to compare against. Step 2 explains what to do in that case.

At the repo root, read PROJECT.md, and also read the README, CLAUDE.md, .claude/CLAUDE.md and AGENTS.md if they exist. If there is no PROJECT.md, there is nothing to review and no scope to check an idea against. Tell the user, offer to create the file with `/project-md:init`, and stop.

Then decide what to do:

- **If the argument names a section** of PROJECT.md, such as `non-goals`, review only that section (step 2).
- **If the argument is anything else**, treat it as an idea to check (step 4).
- **If there is no argument**, review the whole file (step 2).

## 2. Review PROJECT.md

Find what has changed since PROJECT.md was last committed, using the commit hash from step 1:

```
git log --oneline HASH..HEAD
git diff --stat HASH..HEAD
```

If a commit's subject does not explain enough, read its changes with `git log -p -1 COMMIT`. If PROJECT.md has uncommitted changes, read them with `git diff -- :/PROJECT.md`. The user may have edited the file by hand, and those edits are the user's own. If PROJECT.md has never been committed, or the repo has no commits, review the file against `git log --oneline -30` and the repo's files, and tell the user that there is no committed version to compare against yet.

Look for the following:

- **In the changes since the last commit:**
  - Work that serves none of the goals, or that a non-goal or constraint rules out. Name the commit.
  - A success criterion that is now met, or a sign of failure that is now showing.
  - A decision in the commits that is not recorded under Decisions, such as a new dependency, a dropped feature or a chosen approach.
  - An open question that the commits answer.
  - A Status section that no longer describes the project's current state.
- **In the file itself:**
  - A success or failure line that is too vague to check. Propose one that can be checked.
  - Lines that contradict each other, such as a goal that a non-goal rules out.
  - A section from the list above that is missing, or a `Not decided yet.` that the repo now answers.
  - A Status section that reads as a log of past changes rather than the current state, or that contains something that changes with every commit, such as a commit count.
  - A file longer than 150 lines. Propose condensing old decisions into fewer lines and reducing Status to the current state.

Leave out any finding that the file already answers through a decision, non-goal or open question. Review the project's scope, not its code: don't run, test or change the code.

First, report in one line whether the work since the last review serves the goals. Then list the findings, numbered, each with its evidence (a commit or a line of the file) and the edit you propose. Then ask the questions that only the user can answer, in plain text, not with AskUserQuestion. If there are no findings, tell the user that PROJECT.md is up to date, and stop without changing anything.

## 3. Record the answers

Draft an edit for each finding that the user answers:

- A change of scope goes under Goals, Non-goals or Constraints, in the user's words.
- Work that the user keeps, although it is outside the goals, goes under Decisions with the user's reason. Otherwise, the next review will raise it again.
- A success criterion that is met, or a question that is answered, updates its section. An answered open question moves to Decisions.
- When the project's status changes, rewrite the Status section to describe the project's current state: what works, what comes next and what is on hold. Keep a past change only while it is still useful context. Remove finished work and anything that Decisions, What it is or a README already records. Don't add a line per change. Status stays a few lines long, however long the project runs.

A Decisions line has the format `- YYYY-MM-DD: what was decided. Why: the reason.`, with today's date. For example: `- 2026-11-05: Kept the level editor, though it's not a goal. Why: it makes testing levels faster.`

## 4. Check an idea

Compare the idea with the Goals, Non-goals, Priorities, Constraints and Decisions sections. Say whether the idea fits the project, conflicts with it (quote the line it conflicts with), or is not covered. Recommend whether to do it, not do it, or change the scope first, and explain why. When the user decides, record the decision as described in step 3: as a new goal or non-goal, or as a line under Decisions, such as `- 2026-11-05: Won't add multiplayer. Why: it would double the testing for a game made by one person.`

## 5. Write

1. Write nothing until the user approves the edits. Then change PROJECT.md with the Edit tool, keeping its wording and its own sections.
2. Show what changed with `git diff -- :/PROJECT.md`.
3. Offer to commit PROJECT.md, following the repo's git rules. The next review uses this commit as its starting point. Don't add an import of PROJECT.md to CLAUDE.md, because this plugin loads the file into every session.
