# project-md

project-md adds a `PROJECT.md` file to your project. The file is committed with your code and describes the project's purpose, goals, and scope. Use `/project-md:init` to create the file and `/project-md:review` to update it as the project changes. You can run a review at any time. If nothing has changed since the last review, the review makes no changes. Claude also runs these skills when you ask it to create or review PROJECT.md.

```
/plugin install project-md --marketplace astrosteveo/astro-plugins
```

`CLAUDE.md` contains instructions for working in a repository. `PROJECT.md` describes the project itself. With it, Claude can judge whether a feature fits the project, make small tradeoffs the way you would, and avoid suggesting ideas you have already rejected.

## Use

```
/project-md:init                        # create a first PROJECT.md
/project-md:review                      # review PROJECT.md against recent changes
/project-md:review non-goals            # review one section
/project-md:review add multiplayer      # check whether an idea fits the project
```

| When | What Claude does |
| --- | --- |
| You run init | Fills in what it can learn from the repository, such as what the project is, its stack and its license. It then asks you about the rest, a few questions at a time, with a suggested answer for each, and shows you the complete draft. If PROJECT.md already exists, it offers to review the file instead. |
| You run review | Reads the changes made since PROJECT.md was last committed, and reports in one line whether that work serves the project's goals. It then lists numbered findings, such as work that a non-goal rules out, success criteria that are now met, decisions that the file does not record, open questions that the commits have answered, and lines that are vague or out of date. Finally, it asks you the questions that only you can answer. |
| You name an idea | Says whether the idea fits the project, conflicts with it (quoting the conflicting line), or is not covered. It recommends what to do and records your decision. |
| You answer | Drafts the edits. Changes to the scope use your wording. Work that you decide to keep, although it is outside the goals, is recorded under Decisions with your reason, so that a later review does not raise it again. |
| You approve | Writes the file and offers to commit it. A review also shows the diff. |

Neither skill writes anything until you approve. A review checks the project's scope, not its code. If you run a review and there is no PROJECT.md, Claude offers to run init.

## The file

PROJECT.md has these sections, in this order: What it is, The problem, Who it's for, Goals, Non-goals, Success looks like, Failure looks like, Priorities, Constraints, Decisions, Open questions, Glossary and Status. The template, with a note under each heading that explains what the section contains, is in [`skills/init/SKILL.md`](skills/init/SKILL.md) under "Draft PROJECT.md". The template is part of the skill rather than a separate file because Claude Code asks for permission before it reads a file outside the project, and an installed plugin is always outside the project. For the same reason, the review skill keeps its own list of the sections, so a change to the sections goes in both skills.

Repeated reviews do not raise the same findings, for these reasons:

- The file has no review date. The last commit that changed PROJECT.md marks the last review, so commit the file after each review.
- Every finding you answer is recorded in the file, even when your answer is to leave something as it is. A review does not raise a finding that the file already answers.
- The file has one copy of each heading. Your own sections and wording are kept unless you approve a change.

## Loading it in every session

The plugin loads PROJECT.md for you, so your CLAUDE.md does not need to import it. When a session starts, a hook looks for PROJECT.md at the root of the current git repository, or in the session's folder if the session is not in a repository. If the file exists, the hook adds it to the files that Claude Code sends with your first message, in the same way that Claude Code sends CLAUDE.md. The hook places this text above the file's contents:

```
PROJECT.md provides context for the project. It defines the project's purpose, goals, and any other information that helps Claude understand the project. If a request conflicts with the project's non-goals or constraints, point this out before starting work.
```

Claude Code sends the file again after a compaction or `/clear`. If there is no PROJECT.md, the hook does nothing. If a CLAUDE.md already imports PROJECT.md with `@PROJECT.md`, the hook does not add the file a second time, and you can delete that import line. Because the hook loads the file, PROJECT.md is loaded only where project-md is installed. Someone who clones the repository without the plugin does not get it.

Like CLAUDE.md, PROJECT.md uses context in every session. Claude Code's documentation recommends keeping CLAUDE.md under 200 lines, so the skills keep PROJECT.md under 150 lines, and a review proposes condensing old decisions when the file grows beyond that. A review rewrites the Status section to describe the project's current state instead of adding a line for each change, so Status stays a few lines long.

## Tests

```
python3 -m unittest discover -s plugins/project-md/tests
claude plugin validate plugins/project-md
claude plugin test plugins/project-md
```
