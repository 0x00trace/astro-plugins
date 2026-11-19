"""Checks on what Claude Code acts on in the skill and its agent: frontmatter, allowed-tools, the
agent's tools, and the numbers the map script defines. What the skill tells Claude to do is checked
by running it, with the cases in evals/."""

import json
import re
import sys
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "hunt" / "SKILL.md"
HUNTER = PLUGIN / "agents" / "hunter.md"
sys.path.insert(0, str(SKILL.parent / "scripts"))
import inventory


def split(path):
    _, front, body = path.read_text().split("---\n", 2)
    fields = {}
    for line in front.splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields, body


class SkillTest(unittest.TestCase):
    def setUp(self):
        self.front, self.body = split(SKILL)
        self.allowed = self.front["allowed-tools"]
        self.hunter_front, _ = split(HUNTER)

    def section(self, start, end):
        begin = self.body.index(start)
        return self.body[begin : self.body.index(end, begin)]

    def test_the_description_fits_the_skill_listing(self):
        # Claude Code cuts a skill's description at 1,536 characters in the listing.
        self.assertLess(len(self.front["description"]), 1536)
        self.assertEqual(self.front["name"], SKILL.parent.name)

    def test_every_git_and_gh_command_it_runs_is_pre_approved(self):
        # An unapproved command stops the skill for a permission prompt, or fails under -p.
        runs = set(re.findall(r"`(git [a-z-]+)", self.body)) | set(
            re.findall(r"^(git [a-z-]+)", self.body, re.MULTILINE)
        )
        runs |= set(re.findall(r"`(gh [a-z]+ [a-z]+)", self.body))
        forbidden = {
            "git checkout",
            "git restore",
            "git reset",
            "git stash",
            "git clean",
        }
        self.assertEqual(
            runs - forbidden,
            {
                "git rev-parse",
                "git status",
                "git branch",
                "git ls-files",
                "git merge-base",
                "gh pr view",
            },
        )
        for command in runs - forbidden:
            self.assertIn(f"Bash({command} *)", self.allowed)

    def test_commands_that_lose_uncommitted_work_are_never_pre_approved(self):
        for command in ("checkout", "restore", "reset", "stash", "clean"):
            self.assertNotIn(f"git {command}", self.allowed)

    def test_the_map_script_is_pre_approved_with_and_without_paths(self):
        run = "python3 ${CLAUDE_SKILL_DIR}/scripts/inventory.py"
        self.assertIn(run, self.body)
        self.assertIn(f"Bash({run})", self.allowed)
        self.assertIn(f"Bash({run} *)", self.allowed)
        self.assertTrue((SKILL.parent / "scripts" / "inventory.py").is_file())

    def test_the_hunter_it_sends_is_the_plugins_own_agent(self):
        manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
        agent = f"{manifest['name']}:{self.hunter_front['name']}"
        self.assertEqual(agent, "bug-hunt:hunter")
        self.assertIn(f"`{agent}`", self.section("## 3. Hunt", "## 4."))

    def test_hunters_can_only_read(self):
        # Hunters run side by side in the user's working tree: one that wrote a file could break
        # another's reading or the user's work, and Bash would bring permission prompts.
        tools = {t.strip() for t in self.hunter_front["tools"].split(",")}
        self.assertEqual(tools, {"Read", "Grep", "Glob"})

    def test_the_component_size_is_the_scripts_budget(self):
        budget = f"{inventory.DEFAULT_BUDGET:,}"
        self.assertIn(budget, self.section("## 2. Map", "## 3."))


if __name__ == "__main__":
    unittest.main()
