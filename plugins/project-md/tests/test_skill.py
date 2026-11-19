"""Checks on what Claude Code acts on in the two skills: allowed-tools, the git commands they run,
and the files they read. What the skills tell Claude to do is checked by running them."""

import re
import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[1] / "skills"


def skill(name):
    _, front, body = (SKILLS / name / "SKILL.md").read_text().split("---\n", 2)
    return front, body


def field(front, key):
    return next(line for line in front.splitlines() if line.startswith(f"{key}:"))


class SkillTest(unittest.TestCase):
    def test_every_git_command_each_runs_is_pre_approved(self):
        # An unapproved run stops the skill for a permission prompt, or fails outright under -p.
        for name, expected in [
            ("init", {"rev-parse", "log"}),
            ("review", {"rev-parse", "status", "log", "diff"}),
        ]:
            with self.subTest(name):
                front, body = skill(name)
                runs = set(re.findall(r"^git ([a-z-]+)", body, re.MULTILINE))
                runs |= set(re.findall(r"`git ([a-z-]+)", body))
                self.assertEqual(runs, expected)
                for command in runs:
                    self.assertIn(
                        f"Bash(git {command} *)", field(front, "allowed-tools")
                    )

    def test_neither_reads_a_file_beside_it(self):
        # Claude Code asks before the Read tool or cat opens a file outside the project, which an
        # installed plugin always is, so each skill holds what it needs in its own text.
        for name in ["init", "review"]:
            with self.subTest(name):
                self.assertNotIn("CLAUDE_SKILL_DIR", skill(name)[1])

    def test_git_finds_the_root_project_md_from_any_folder(self):
        # A pathspec after -- is read from the current folder, so in a subfolder
        # `git log -1 -- PROJECT.md` prints nothing for a committed PROJECT.md. :/ starts at the root.
        specs = re.findall(r"git (?:log|diff)[^`\n]* -- ([^\s`]+)", skill("review")[1])
        self.assertTrue(specs)
        self.assertEqual(set(specs), {":/PROJECT.md"})


if __name__ == "__main__":
    unittest.main()
