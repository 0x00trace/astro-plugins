---
id: AP-18
type: task
title: Give the global CLAUDE.md a header in /instructions:init
status: done
priority: high
owner: claude
created: 2026-11-15
labels: [instructions]
---
/instructions:init puts `/init`'s `# CLAUDE.md` header on a project CLAUDE.md, but SKILL.md:180 tells it not to put one on the global ~/.claude/CLAUDE.md ("Don't start it with the project file's opening lines"). The user expects the global file to get a header too. The review also has no check for a missing header, so reviewing an existing file never adds one.

## Subtasks
- [x] Global file starts with its own header in "What goes in each file"
- [x] Add a header check to "Check every file", so a review adds a missing one
- [x] Test the new wording
- [x] README: list the header check
- [x] See it working in a second session
- [x] Release 0.2.1 and update the installed copy

## Log
- 2026-11-15 15:31 claude: created
- 2026-11-15 15:31 claude: moved to in-progress
- 2026-11-15 15:31 claude: done subtask: Global file starts with its own header in "What goes in each file"
- 2026-11-15 15:31 claude: done subtask: Add a header check to "Check every file", so a review adds a missing one
- 2026-11-15 15:31 claude: done subtask: Test the new wording
- 2026-11-15 15:31 claude: done subtask: README: list the header check
- 2026-11-15 15:47 claude: Seen working: /instructions:init (Global, review) on the real ~/.claude/CLAUDE.md drafted edit 1 adding the header, citing the Header check; nothing written
- 2026-11-15 15:47 claude: done subtask: See it working in a second session
- 2026-11-15 15:47 claude: done subtask: Release 0.2.1 and update the installed copy
- 2026-11-15 15:47 claude: moved to done
