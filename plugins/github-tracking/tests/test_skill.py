"""Checks on what Claude Code acts on in the skills: frontmatter, allowed-tools, and the board.py and
migrate.py commands they run. What the skills tell Claude to do is checked by running them."""

import contextlib
import io
import re
import sys
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))
import board
import migrate

SKILLS = ["track", "init", "migrate"]
BOARD_SKILLS = ["track", "init"]


def skill(name):
    _, front, body = (
        (PLUGIN / "skills" / name / "SKILL.md").read_text().split("---\n", 2)
    )
    fields = {}
    for line in front.splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields, body


def help_text(main, argv):
    out = io.StringIO()
    with (
        unittest.TestCase().assertRaises(SystemExit) as done,
        contextlib.redirect_stdout(out),
    ):
        main(argv)
    return done.exception.code, out.getvalue()


class EverySkillTest(unittest.TestCase):
    def test_each_is_named_for_its_folder_and_fits_the_skill_listing(self):
        # Claude Code cuts a skill's description at 1,536 characters in the listing.
        for name in SKILLS:
            with self.subTest(name):
                front, _ = skill(name)
                self.assertEqual(front["name"], name)
                self.assertLess(len(front["description"]), 1536)


class BoardSkillsTest(unittest.TestCase):
    def test_every_board_py_command_each_runs_is_pre_approved(self):
        # An unapproved run stops the skill for a permission prompt, or fails outright under -p.
        for name in BOARD_SKILLS:
            with self.subTest(name):
                front, body = skill(name)
                runs = re.findall(r"python3 (\S+board\.py) ", body)
                self.assertTrue(runs)
                for script in set(runs):
                    self.assertIn(f"Bash(python3 {script} *)", front["allowed-tools"])

    def test_both_run_the_one_board_py_at_the_plugin_root(self):
        # ${CLAUDE_SKILL_DIR} is each skill's own folder, so a script both skills share is reached
        # from ${CLAUDE_PLUGIN_ROOT}, which Claude Code substitutes in a plugin skill's body and
        # allowed-tools alike.
        for name in BOARD_SKILLS:
            with self.subTest(name):
                front, body = skill(name)
                scripts = set(
                    re.findall(r"python3 (\S+board\.py)", front["allowed-tools"] + body)
                )
                self.assertEqual(scripts, {"${CLAUDE_PLUGIN_ROOT}/scripts/board.py"})
        self.assertTrue((PLUGIN / "scripts" / "board.py").is_file())

    def test_every_command_they_name_is_one_board_py_has(self):
        named = {
            name: set(re.findall(r"board\.py (?:--\S+ \S+ )*([a-z]+)", skill(name)[1]))
            for name in BOARD_SKILLS
        }
        self.assertEqual(named["track"], {"show", "move", "sub", "update"})
        self.assertEqual(named["init"], {"show", "views", "move"})
        for command in named["track"] | named["init"]:
            code, _ = help_text(board.main, [command, "--help"])
            self.assertEqual(code, 0, command)

    def test_every_gh_command_init_pre_approves_only_reads(self):
        # Making a board, a label or a milestone changes GitHub, so the user sees each one asked for.
        front, body = skill("init")
        approved = re.findall(r"Bash\((gh [a-z]+ [a-z]+) \*\)", front["allowed-tools"])
        self.assertEqual(set(approved), {"gh repo view", "gh issue list"})
        for command in approved:
            self.assertRegex(body, rf"(?m)^{command} ")


class TrackTest(unittest.TestCase):
    def setUp(self):
        self.front, self.body = skill("track")

    def operations(self):
        return re.findall(r"(?:\[|\| )([a-z]+)", self.front["argument-hint"])

    def test_it_pre_approves_only_board_py(self):
        # Claude loads track before every change, so approving gh issue create here would also
        # cover issues it files without being asked.
        self.assertEqual(
            self.front["allowed-tools"],
            "Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/board.py *)",
        )

    def test_it_places_its_argument_once(self):
        # Without the placeholder, Claude Code appends the argument after the last section.
        self.assertEqual(self.body.count("$ARGUMENTS"), 1)

    def test_every_operation_but_file_and_start_is_a_board_py_command(self):
        self.assertEqual(
            self.operations(), ["show", "file", "start", "move", "sub", "update"]
        )
        _, out = help_text(board.main, ["--help"])
        commands = set(re.search(r"\{([a-z,]+)\}", out).group(1).split(","))
        self.assertLessEqual(set(self.operations()) - {"file", "start"}, commands)

    def test_every_update_status_it_names_is_one_board_py_takes(self):
        named = set(
            re.findall(r"`(on-track|at-risk|off-track|complete|inactive)`", self.body)
        )
        self.assertEqual(named, set(board.UPDATE_STATUSES))


class MigrateTest(unittest.TestCase):
    def setUp(self):
        self.front, self.body = skill("migrate")
        self.allowed = self.front["allowed-tools"]

    def test_scan_and_the_git_reads_are_pre_approved_and_run_is_not(self):
        # run changes GitHub and the repo, so the user approves it at the prompt, after the plan.
        script = "${CLAUDE_PLUGIN_ROOT}/scripts/migrate.py"
        self.assertIn(f"Bash(python3 {script} scan)", self.allowed)
        self.assertIn(f"Bash(python3 {script} scan *)", self.allowed)
        self.assertNotIn(f"Bash(python3 {script} *)", self.allowed)
        self.assertNotIn(f"{script} run", self.allowed)
        for command in re.findall(r"`(git (?:log|show)) ", self.body):
            self.assertIn(f"Bash({command} *)", self.allowed)
        self.assertTrue((PLUGIN / "scripts" / "migrate.py").is_file())

    def test_every_command_and_option_it_names_is_one_migrate_py_has(self):
        commands = set(re.findall(r"migrate\.py (scan|run)\b", self.body))
        self.assertEqual(commands, {"scan", "run"})
        options = set(re.findall(r"`(--[a-z]+)", self.body))
        self.assertEqual(options, {"--project", "--prefix"})
        _, out = help_text(migrate.main, ["--help"])
        for option in options:
            self.assertIn(option, out)


if __name__ == "__main__":
    unittest.main()
