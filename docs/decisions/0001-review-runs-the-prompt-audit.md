# Review runs the prompt audit

Status: accepted 2026-11-15 · AP-2

## Context

The review in `/instructions:init` 0.1.0 rests on one sentence: "The existing file is the baseline: catch what's missing, outdated or bloated." It checks nothing against Anthropic's guidance. It doesn't look at format, size, wording, placement, conflicts with other instruction files, or whether the paths and commands a file names still exist.

Claude Code 2.1.325 ships `/doctor prompt-audit`, which runs the bundled `claude-api` skill's `prompt-audit` subcommand. Its rubric (`shared/prompt-audit.md` in the binary) covers pressure language such as `IMPORTANT` and `MUST`, hedges on real requirements, paths and commands that no longer exist, files that contradict each other, and history such as PR numbers. The memory docs (code.claude.com/docs/en/memory, "Write effective instructions") and the best-practices docs add rules the audit doesn't cover: under 200 lines per file, headings and bullets, rules that must always hold go in a hook or deny rule, procedures go in skills, `@` import syntax, and rule-file frontmatter.

## Decision

The review runs the bundled prompt audit in a subagent on each file under review (AP-8), and adds a short check list from the memory and best-practices docs for what the audit doesn't cover (AP-9). Each proposed edit names the check or finding it fixes (AP-10).

This rests on AP-5: a subagent has to be able to start the audit through the Skill tool. If it can't, this record is superseded before AP-8 starts.

## Turned down

- Copying the audit's rubric into SKILL.md. It would go stale with each Claude Code release, against PROJECT.md's Goal 2 (build on Claude Code's current docs and APIs rather than copying its behavior).
- Having Phase 8 run `/doctor prompt-audit` instead of suggesting it. Its findings would arrive after the user approved and the file was written.

## Consequences

- A review costs one more subagent, run next to the surveys in Phase 2.
- The review depends on the bundled `claude-api` skill. When `skillOverrides` or `disableBundledSkills` turns it off, the review says so in one line and uses the check list alone.
- The drop condition in PROJECT.md stays the same: once `/init` shows its proposals, the project half goes, and `/doctor prompt-audit` covers the review.
