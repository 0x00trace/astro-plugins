# astro-plugins

Personal Claude Code plugins that remove the frictions a solo developer runs into session after session.

## What it is

A public Claude Code plugin marketplace with ten plugins, each installed on its own: inline-thinking, gates, global-memory, github-tracking, screen-polish, project-md, bug-hunt, plain-english, docs-site and instructions. Install one with `/plugin install NAME --marketplace astrosteveo/astro-plugins`.

## The problem

Claude Code's defaults don't fit how the author works. It folds its thinking into "Thought for 4s", runs risky commands like `pkill`, forgets preferences between projects, doesn't keep GitHub in step with the work, drifts from a project's scope, and pads its writing with hedges and filler. Without the plugins, the author corrects the same things session after session.

## Who it's for

The author: a solo developer on Linux who uses Claude Code for hobby projects. The repo is public, so anyone can install the plugins, but they're built around the author's workflow. They're not meant for teams.

## Goals

1. Each plugin removes one friction that keeps coming up in Claude Code sessions, and installs on its own.
2. Plugins build on Claude Code's current docs and APIs, rather than copying its behavior.
3. A plugin ships only after it's tested and seen working in a real session.

## Non-goals

- Settings or features for needs other than the author's, such as team or org setups. Why: these are personal plugins for solo hobby projects.
- Doing what Claude Code already does itself. A plugin is dropped once Claude Code ships the same feature. Why: a plugin like that is upkeep with no gain.
- Carrying the author's own workflow habits, such as how to use git, which work gets an issue, or where docs go. Why: those live in the author's global CLAUDE.md, so installing a plugin doesn't bring the author's habits with it. A plugin can still say how to use its own tool well.

## Success looks like

- Every plugin in the marketplace is one the author keeps installed and enabled.
- Each plugin's tests and `claude plugin validate` pass on main.
- When a Claude Code release breaks a plugin, it's fixed or dropped within a week.

## Failure looks like

- The author turns off a plugin because it gets in the way more than it helps.
- Keeping the plugins working after Claude Code updates takes more time than they save.

## Priorities

1. Never breaks or slows down a session.
2. Follows Claude Code's current docs.
3. Simple, with the fewest moving parts.
4. More features.

## Constraints

- Every plugin is listed in `.claude-plugin/marketplace.json` and passes `claude plugin validate`.
- Hook plugins are written in TypeScript, and skill scripts use only Python 3.11+'s standard library, as their tests do.
- Plugins are all tested on Linux.
- MIT license, public on GitHub.

## Decisions

- 2026-11-10: Plugins aim to support both Linux, on any distro, and Windows, replacing the Linux-only constraint and the Windows non-goal. Why: the author works on WSL now and wants the plugins not to depend on one setup; Windows support may lag behind Linux.
- 2026-11-11: Plugins are tested on Linux only, replacing the aim to support Windows. They may work on Windows, but that isn't tested or guaranteed. Why: the author uses Linux again.
- 2026-11-12: project-md loads PROJECT.md with a hook instead of an @PROJECT.md line in CLAUDE.md. Why: no repo needs the line, and the hook adds PROJECT.md only when the repo has one and nothing already imports it.
- 2026-11-12: Whether a plugin gets an init skill depends on the plugin. One that scaffolds something, such as PROJECT.md (/project-md:init), gets one; one that reviews code, such as bug-hunt, doesn't. Why: an init skill gets what a plugin scaffolds set up properly, and reviewing code has nothing to set up.
- 2026-11-12: corkboard is listed from its own repo, astrosteveo/corkboard, instead of living in `plugins/`, and follows that repo's rules: its CLI and session-start hook are Python 3.11+ with only the standard library. Why: it's a larger project with its own tests, CI and PROJECT.md, and the author chose to list it here as an exception.
- 2026-11-13: Dropped global-rules. Claude Code's new `/init` (`CLAUDE_CODE_NEW_INIT=1`) sets up a project's CLAUDE.md, CLAUDE.local.md, skills and hooks, `/doctor prompt-audit` checks instruction files, and memory carries corrections between sessions. Why: what was left, guidance for the rare edit to a short global CLAUDE.md, wasn't worth the upkeep of a hook, two skills and a docs fetcher.
- 2026-11-13: plain-english sets its rules with an output style that turns itself on (`force-for-plugin`), and hands the same text to subagents as SubagentStart context. Why: an output style is Claude Code's own way to set how Claude writes and reaches the main conversation and forks, but a subagent with its own system prompt doesn't get it, and `prompt.compose` doesn't run for one either.
- 2026-11-13: Added instructions, whose /instructions:init is a fork of the new `/init`'s prompt from Claude Code 2.1.325. It goes against Goal 2 and the non-goal of doing what Claude Code already does, on purpose. Drop its project half once `/init` shows its proposals, and the plugin once `/init` covers the global CLAUDE.md too. Why: `/init` asked "Does this look right?" with no proposal on screen in 2 of the author's runs, because after a tool call Claude writes the text it's told to print before AskUserQuestion only in its thinking (0 of 3 test runs showed it, 3 of 3 when the draft ends the turn). `/init` also has no option for the global `~/.claude/CLAUDE.md`. A `skill.prompt` hook that edits `/init`'s text was turned down: a text replacement breaks silently when the prompt changes, and the global flow is too large to add that way.
- 2026-11-13: Raised the Python floor for skill scripts and their tests from 3.8 to 3.11, the same as corkboard's. Why: no reason for 3.8 was recorded, its upstream support ended in October 2024, and neither script needs a change.
- 2026-11-14: Dropped the gates that refused `git add -A` and `git commit -a`. The plugins don't set rules for how to use Git. Why: how the author stages and commits belongs in their CLAUDE.md and each repo's rules.
- 2026-11-15: instructions' review runs Claude Code's bundled prompt audit on each file under review, and adds a short check list from the memory docs for what the audit doesn't cover. Why: the review rested on one sentence, and a copy of the audit's rubric would go stale with each Claude Code release ([0001](docs/decisions/0001-review-runs-the-prompt-audit.md)).
- 2026-11-16: Dropped github-tracking. Why: corkboard tracks the work in the repo.
- 2026-11-16: Plugins don't tell Claude how to work (Non-goals). The workflow and docs rules in corkboard's skills moved to the author's global CLAUDE.md, and its skills now say how corkboard works and what it needs. plain-english is the exception on purpose: a writing style is what it ships. Why: a review of every plugin found workflow rules riding along with corkboard's tracker and docs, so taking the function meant taking the workflow too.
- 2026-11-16: plain-english's style stays as rules, without example passages. Why: in its eval suite, passages from a Go blog post and a crates.io postmortem made replies 11% longer and raised bold from 12 spans to 21, with no measurable drop in hedging ([note](docs/notes/2026-11-16-what-the-plain-english-style-changes.md)).
- 2026-11-16: plain-english lists the stand-ins it replaces, such as "land" for merge and "the work" for a named task, each with the plain word to use, in place of a general rule against abstraction and metaphor. Why: in its evals the list raised replies with no metaphor verb from 17 to 22 of 27 on Opus 5.5 and from 15 to 21 on Fable 5.2, and removed the listed words, where the general rule had done little ([note](docs/notes/2026-11-16-what-the-name-things-rule-changes.md)).
- 2026-11-16: plain-english's Name things list stays at 0.2.0's ten stand-ins, and this line replaces the Opus figure in the one above. Why: adding "everything else", "the other option" and "hold up" cut them on Fable 5.2, but on Opus 5.5 vague references didn't fall and the listed phrases came up more often. A second run of 0.2.0 scored 17 of 27 on Opus for metaphor verbs, the same as 0.1.0, so the gain there isn't shown; Fable's held, at 21 and 23 against 15 ([note](docs/notes/2026-11-16-listing-vague-phrases-in-the-style.md)).
- 2026-11-17: plain-english's Name things list adds "hold up" and "turn up", replacing the line above that kept it at ten, and its eval suite drops the vague-reference grader. Why: the author is fine with vague references and wants dead metaphors such as "lands" gone. In the release cases, "hold up" fell from 11 in 27 replies to 2 in 18 on Opus 5.5 and from 7 to 0 on Fable 5.2, "turn up" fell to 0 on both, and no other metaphor rose ([note](docs/notes/2026-11-17-listing-hold-up-and-turn-up-in-the-style.md)).
- 2026-11-17: Restored github-tracking and dropped corkboard from the marketplace, replacing the 2026-11-12 line that lists corkboard from its own repo and the 2026-11-16 line that drops github-tracking. github-tracking's skills say only how the board works, and which work gets an issue moved to the author's global CLAUDE.md. The project's docs moved from `.project/docs/` to the repo's wiki. Why: the author's remotes are on GitHub, so they track the work with GitHub's own issues, Projects board and wiki, rather than keep up a custom web app that could break.
- 2026-11-17: Project docs live in `docs/`, shown as a site with `uvx zensical serve`, replacing the line above that moved them to the wiki. GitHub Pages isn't used, so every repo, public or private, reads its docs the same way. Why: a wiki needs its first page saved in the browser in each repo, and its Pages box lists every page with all its headings, so it doesn't scale. A `docs/` folder needs no setup and changes in the same PR as the code, and Zensical, the successor to Material for MkDocs, shows it with a sidebar, sections and search.
- 2026-11-17: Added docs-site, whose /docs-site:init writes a repo's `mkdocs.yml`, docs home page and `site/` ignore line with one script, rather than `zensical new`. Why: setting up the docs site by hand came up in every new repo, and `zensical new` writes a fixed `nav` list that each new page has to be added to, a demo page, a GitHub Pages workflow and a placeholder name and URL.
- 2026-11-17: Narrowed the workflow non-goal, replacing the 2026-11-16 line that plugins don't tell Claude how to work: a plugin leaves out the author's own habits, such as git, issue tracking and where docs go, and can still say how to use its own tool well. Why: every skill is instructions to Claude, so the broad wording read as ruling out any guidance a plugin gives, and the author suspected it was hurting some sessions.

## Open questions

None yet.

## Glossary

- Mod: a plugin whose TypeScript hooks module (`hooks/register.ts` or `.tsx`) changes Claude Code's interface or behavior.
- Gate: a check in the gates plugin that refuses a risky Bash command and tells Claude why and what to run instead.
- Global memory: a memory Claude writes that holds in every project, kept in `~/.claude/memory`.

## Status

Ten plugins are in the marketplace. The project's work is tracked on GitHub, in its issues and board #25, with github-tracking, and its decision records and notes are in `docs/`, which `uvx zensical serve` shows as a site. docs-site (#136) sets up that site in any repo with /docs-site:init. github-tracking (#131) is back: its skills say how the board and `board.py` work, and leave which work gets an issue to the author's CLAUDE.md. Since 0.5.0 (#143), /github-tracking:migrate moves a repo's corkboard items to issues on its board. instructions sets up and reviews a project's CLAUDE.md and CLAUDE.local.md and the global CLAUDE.md with /instructions:init, in place of the new `/init`, which asks for approval of a proposal it didn't show. Its review checks each file against Claude Code's docs and runs Claude Code's prompt audit, and it catches all 11 seeded defects in its review-me fixture, where 0.1.0 caught 9. plain-english makes Claude write plain English in the main conversation and in every subagent. In its eval suite, replies with it are about a quarter shorter than without it and don't hedge, and its list of stand-ins removes dead metaphors such as "land", "carry" and, since 0.2.1, "hold up". It leaves vague phrases such as "everything left", which the author is fine with. project-md loads PROJECT.md with a hook (#88), with /project-md:init to draft it and /project-md:review to keep it current (#92). bug-hunt (#67) hunts bugs across a whole codebase and reproduces each finding, leaving reviewing changes to Claude Code's /code-review. Parked: #44, letting memory recall pick global memories, until recall can be turned on in local sessions.
