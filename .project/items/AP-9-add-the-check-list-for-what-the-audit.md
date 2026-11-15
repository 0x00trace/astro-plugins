---
id: AP-9
type: task
title: Add the check list for what the audit doesn't cover
status: done
priority: medium
owner: claude
created: 2026-11-15
parent: AP-2
---
A short list from the memory and best-practices docs, applied to fresh drafts and reviews: under 200 lines; headings and bullets, each rule with its reason; lines specific enough to check; each line in the right place (hook or deny rule, skill, path-scoped rule, CLAUDE.local.md, global file); nothing Claude can read from the code; `@` imports that resolve; rule-file frontmatter; git rules while `includeGitInstructions` is on.

Done when SKILL.md applies the list to drafts and reviews, and tests pin the 200-line, import, placement and git-instructions items.

## Subtasks
- [x] Write the list in SKILL.md
- [x] Point Phase 4 at it for drafts and reviews
- [x] Wording tests

## Log
- 2026-11-15 12:51 claude: created
- 2026-11-15 13:23 claude: moved to in-progress
- 2026-11-15 13:24 claude: done subtask: Write the list in SKILL.md
- 2026-11-15 13:24 claude: done subtask: Point Phase 4 at it for drafts and reviews
- 2026-11-15 13:24 claude: done subtask: Wording tests
- 2026-11-15 13:24 claude: The list sits under 'What goes in each file' as '### Check every file'. Phase 4 checks drafts and reviewed files against it. It repeats the audit's main checks (volume, true, consistent, current) in short form because it's also the fallback when the audit is off, and the audit never sees fresh drafts. Phase 4 can now propose a **Permission** rule, and Phase 5 writes approved ones into permissions.deny or allow. Live scoring happens in AP-12.
- 2026-11-15 13:24 claude: moved to done
