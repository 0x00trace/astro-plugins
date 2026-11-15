---
id: AP-9
type: task
title: Add the check list for what the audit doesn't cover
status: todo
priority: medium
owner: claude
created: 2026-11-15
parent: AP-2
---
A short list from the memory and best-practices docs, applied to fresh drafts and reviews: under 200 lines; headings and bullets, each rule with its reason; lines specific enough to check; each line in the right place (hook or deny rule, skill, path-scoped rule, CLAUDE.local.md, global file); nothing Claude can read from the code; `@` imports that resolve; rule-file frontmatter; git rules while `includeGitInstructions` is on.

Done when SKILL.md applies the list to drafts and reviews, and tests pin the 200-line, import, placement and git-instructions items.

## Subtasks
- [ ] Write the list in SKILL.md
- [ ] Point Phase 4 at it for drafts and reviews
- [ ] Wording tests

## Log
- 2026-11-15 12:51 claude: created
