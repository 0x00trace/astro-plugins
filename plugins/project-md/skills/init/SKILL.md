---
name: init
description: Create the repo's PROJECT.md, a committed file that describes the project's purpose, goals, non-goals and constraints. Drafts the file from the repo and a short interview with the user, and writes it after the user approves the draft. Use when the user asks to start, create, write or set up a PROJECT.md, or to write down a new project's scope or goals. If the repo already has a PROJECT.md, use /project-md:review instead.
allowed-tools: Bash(git rev-parse *), Bash(git log *)
---

# Create PROJECT.md

PROJECT.md is a file at the root of the repo that describes the project: the problem it solves, who it is for, what it will and will not do, and how to tell whether it succeeds. CLAUDE.md contains instructions for working in the repo, and PROJECT.md describes the project itself. After the file is written, `/project-md:review` keeps it up to date as the project changes.

## 1. Look at the repo

Run these commands in a single turn:

```
git rev-parse --show-toplevel
git log --oneline -20
```

If the folder is not a git repo, use the current folder as the repo root.

If PROJECT.md already exists at the repo root, don't draft another one. Tell the user that the file exists, offer to review it with `/project-md:review`, and stop.

Read the following files if they exist at the repo root: the README, CLAUDE.md, .claude/CLAUDE.md and AGENTS.md. Also read the project's manifest files, such as Cargo.toml, package.json, pyproject.toml or project.godot.

## 2. Draft PROJECT.md

Use the template below. Its headings, in the order shown, are the sections of PROJECT.md. The comment under each heading explains what the section contains. Do not include the comments in PROJECT.md.

````markdown
# Project name

One sentence that says what the project is and who it is for.

## What it is

<!-- What kind of project this is (for example a CLI, library, web app, game or service), what it does, and how people use it. One short paragraph. -->

## The problem

<!-- Who has the problem, how it affects them, and how they deal with it today. -->

## Who it's for

<!-- The people who use the project, and what they already know and have. If it is not obvious, also say who the project is not for. -->

## Goals

<!-- What the project will achieve, stated as outcomes, with the most important first. -->

## Non-goals

<!-- What the project will not do, even though someone could reasonably expect it to. Give the reason for each one. -->

## Success looks like

<!-- How to tell whether the project succeeded, stated as checks that someone can run or observe. For example, "a new player finishes level 1 in under 10 minutes", not "players enjoy it". -->

## Failure looks like

<!-- The outcomes that would make the project not worth doing, or the signs that it is heading toward them. -->

## Priorities

<!-- The order in which to make tradeoffs when two good things conflict, such as "1. Simple to use 2. Fast 3. More features". -->

## Constraints

<!-- What cannot change, such as platforms, stack, budget, time, licenses, and things that must never break. -->

## Decisions

<!-- One line per decision, with the newest last: "- YYYY-MM-DD: what was decided. Why: the reason." Include ideas that were rejected and findings that were kept on purpose, so that they are not raised again. -->

## Open questions

<!-- Questions that have not been decided yet, one per line. When a question is answered, move it to Decisions. -->

## Glossary

<!-- Terms that this project uses in a specific way, one line each. -->

## Status

<!-- The project's current state against its goals: what works and what comes next. Keep it to a few lines. It is not a task list or a log of changes, and it contains nothing that changes with every commit, such as a commit count. -->
````

Fill in what the repo shows: what the project is, and constraints such as the stack, platforms and license. Take these from the files you read and from the commits.

The problem, who it's for, goals, non-goals, success, failure and priorities are for the user to decide. If the user has already described any of these, in the skill's arguments or earlier in the conversation, use that answer and don't ask again. Ask about the rest in plain text, not with AskUserQuestion, so that the user can answer several questions in one reply. Ask at most four questions at a time. Suggest an answer to each question, based on what the repo shows, so that the user can accept it or reword it.

Then show the complete draft. It contains only what the user said or confirmed, and facts from the repo. If a section has no answer yet, write `Not decided yet.` in it and add its question under Open questions. Keep the file under 150 lines. It is loaded into every session, like CLAUDE.md, and Claude Code's documentation recommends keeping CLAUDE.md under 200 lines.

## 3. Write

1. Write nothing until the user approves the draft. Then write PROJECT.md at the repo root with the Write tool, including any changes the user asked for.
2. Offer to commit PROJECT.md, following the repo's git rules. The first `/project-md:review` uses this commit as its starting point. Don't add an import of PROJECT.md to CLAUDE.md, because this plugin loads the file into every session.
