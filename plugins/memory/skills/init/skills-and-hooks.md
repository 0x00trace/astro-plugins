# Skills, hooks and permission rules

From Claude Code's docs (https://code.claude.com/docs/en/best-practices and https://code.claude.com/docs/en/skills) and Anthropic's skill guide (https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).

## Sort each candidate

- **Hook**: a shell command that must run every time an event happens, and that is fast and gives the same result each time. Examples: format or lint the changed file after each edit (`PostToolUse` on `Write|Edit`), or run a check when Claude finishes a turn (`Stop`, which fires after every turn, including turns that changed nothing). A rule with exceptions, such as "prefer named exports", stays in CLAUDE.md.
- **Permission rule**: something Claude must never do, or may always do, such as the deny rule `Read(./.env)` or `Bash(git push *)`. A deny rule holds in every permission mode, including `bypassPermissions`.
- **Skill**: a procedure with several steps, or knowledge needed only for some tasks, such as a release, a deploy, a migration or a review checklist. Claude sees a skill's name and description in every session, and reads the rest only when a task calls for it.

Propose only what the survey or the user gave evidence for. Don't add a skill for something Claude does well without one.

## Where they go

- For everyone in the repo: skills in `.claude/skills/<name>/SKILL.md`, hooks and permission rules in `.claude/settings.json`.
- For the user, in this repo: hooks and permission rules in `.claude/settings.local.json`.
- For the user, in every repo: skills in `~/.claude/skills/<name>/SKILL.md`, hooks and permission rules in `~/.claude/settings.json`.

## Write a skill

- Read the skills already in the target folder first. Never overwrite one, and choose a name that no other skill or command uses.
- `name`: lowercase letters, digits and hyphens, at most 64 characters. It becomes the `/name` command.
- `description`: what the skill does and when to use it, in the third person, with its main use first and the words a user would say. At most 1,024 characters. Put it in double quotes if it has a colon followed by a space. Write `[branch]`, not `<branch>`: angle brackets show as `&lt;` and `&gt;`.
- For a skill with side effects, such as a deploy or a release, add `disable-model-invocation: true` so only the user can start it. Take its input from `$ARGUMENTS`, with an `argument-hint`.
- The body holds the steps Claude can't guess, with the exact commands the survey found. Keep it under 500 lines, and don't explain what Claude already knows.
- Show the whole `SKILL.md` in the proposal.

## Write hooks and permission rules

Show each hook's JSON and each rule in the proposal. To write them, load the `update-config` skill with the Skill tool and follow it: it tests a hook's command before it writes the hook, and keeps the entries already in the settings file. If that skill isn't available, edit the settings file yourself, keep its entries, and check that the result parses as JSON.
