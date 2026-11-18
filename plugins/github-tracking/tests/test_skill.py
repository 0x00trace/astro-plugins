import contextlib
import io
import re
import sys
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))
import board

SKILLS = ["track", "init"]


def skill(name):
    _, front, body = (
        (PLUGIN / "skills" / name / "SKILL.md").read_text().split("---\n", 2)
    )
    return front, body


def field(front, key):
    return next(line for line in front.splitlines() if line.startswith(f"{key}:"))


class BothSkillsTest(unittest.TestCase):
    def test_every_board_py_command_each_runs_is_pre_approved(self):
        # An unapproved run stops the skill for a permission prompt, or fails outright under -p.
        for name in SKILLS:
            with self.subTest(name):
                front, body = skill(name)
                runs = re.findall(r"python3 (\S+board\.py) ", body)
                self.assertTrue(runs)
                for script in set(runs):
                    self.assertIn(
                        f"Bash(python3 {script} *)", field(front, "allowed-tools")
                    )

    def test_both_run_the_one_board_py_at_the_plugin_root(self):
        # ${CLAUDE_SKILL_DIR} is each skill's own folder, so a script both skills share is reached
        # from ${CLAUDE_PLUGIN_ROOT}, which Claude Code substitutes in a plugin skill's body and
        # allowed-tools alike.
        for name in SKILLS:
            with self.subTest(name):
                front, body = skill(name)
                scripts = set(re.findall(r"python3 (\S+board\.py)", front + body))
                self.assertEqual(scripts, {"${CLAUDE_PLUGIN_ROOT}/scripts/board.py"})
        self.assertTrue((PLUGIN / "scripts" / "board.py").is_file())

    def test_every_command_they_name_is_one_board_py_has(self):
        named = {}
        for name in SKILLS:
            named[name] = set(
                re.findall(r"board\.py (?:--\S+ \S+ )*([a-z]+)", skill(name)[1])
            )
        self.assertEqual(named["track"], {"show", "move", "sub", "update"})
        self.assertEqual(named["init"], {"show", "views", "move"})
        for command in named["track"] | named["init"]:
            with (
                self.assertRaises(SystemExit) as done,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                board.main([command, "--help"])
            self.assertEqual(done.exception.code, 0, command)

    def test_every_gh_command_init_pre_approves_only_reads(self):
        # Making a board, a label or a milestone changes GitHub, so the user sees each one asked for.
        approved = re.findall(
            r"Bash\((gh [a-z]+ [a-z]+) \*\)", field(skill("init")[0], "allowed-tools")
        )
        self.assertEqual(set(approved), {"gh repo view", "gh issue list"})
        body = skill("init")[1]
        for command in approved:
            self.assertRegex(body, rf"(?m)^{command} ")


class TrackTest(unittest.TestCase):
    def setUp(self):
        self.front, self.body = skill("track")

    def test_it_carries_the_user_s_rules_for_issues(self):
        # Claude Code's docs put a procedure for one task in that task's skill, not in a
        # CLAUDE.md that loads in every session (PROJECT.md, Decisions, 2026-11-18).
        self.assertIn("before you start a change", field(self.front, "description"))
        rules = self.body[
            self.body.index("## Which work gets an issue") : self.body.index(
                "## What GitHub does on its own"
            )
        ]
        self.assertIn("follow the repo", rules)
        for rule in [
            "Every change you commit gets an issue",
            "one issue in progress at a time",
            "gets its own issue",
            "`Closes #N`",
            "The commit type goes in a label",
            "Tick each criterion",
        ]:
            self.assertIn(rule, rules)
        headings = ["Problem", "Goal", "Acceptance criteria", "Open questions"]
        at = [rules.index(f"`### {heading}`") for heading in headings]
        self.assertEqual(at, sorted(at))

    def test_every_update_status_it_names_is_one_board_py_takes(self):
        named = set(
            re.findall(r"`(on-track|at-risk|off-track|complete|inactive)`", self.body)
        )
        self.assertEqual(named, set(board.UPDATE_STATUSES))

    def test_setting_up_a_board_is_left_to_init(self):
        # Setup runs once per repo; track loads for every change, so it only points the way.
        self.assertIn("/github-tracking:init", field(self.front, "description"))
        no_board = self.body[self.body.index("## A repo with no board") :]
        self.assertIn("/github-tracking:init", no_board)
        self.assertIn("save that in the project's memory", no_board)
        self.assertNotIn("gh project create", self.body)


class InitTest(unittest.TestCase):
    def setUp(self):
        self.front, self.body = skill("init")

    def test_it_makes_and_links_the_board_then_gives_it_views(self):
        self.assertLess(
            self.body.index("gh project create"), self.body.index("gh project link")
        )
        self.assertLess(
            self.body.index("gh project link"), self.body.index("Run `board.py views`")
        )

    def test_a_second_run_adds_only_what_is_missing(self):
        self.assertIn("Skip this if `show` printed a board", self.body)
        self.assertIn("so a second run changes nothing", self.body)

    def test_it_makes_no_labels_or_milestones(self):
        self.assertIn("It makes no labels or milestones.", self.body)
        self.assertIn("The track skill makes an issue's label", self.body)
        self.assertNotIn("gh label create", self.body)
        self.assertNotIn("/milestones -f", self.body)

    def test_it_asks_for_the_workflows_the_api_cannot_turn_on(self):
        for workflow in ["Item closed", "Pull request merged", "Auto-add sub-issues"]:
            self.assertIn(workflow, self.body)
        self.assertIn("the API can't turn on a workflow", self.body)


if __name__ == "__main__":
    unittest.main()


class MigrateTest(unittest.TestCase):
    def setUp(self):
        self.front, self.body = skill("migrate")
        self.allowed = field(self.front, "allowed-tools")

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
        import migrate

        commands = set(re.findall(r"migrate\.py (scan|run)\b", self.body))
        self.assertEqual(commands, {"scan", "run"})
        options = set(re.findall(r"`(--[a-z]+)", self.body))
        self.assertEqual(options, {"--project", "--prefix"})
        out = io.StringIO()
        with self.assertRaises(SystemExit), contextlib.redirect_stdout(out):
            migrate.main(["--help"])
        for option in options:
            self.assertIn(option, out.getvalue())

    def test_the_plan_ends_the_turn_before_run(self):
        show = self.body[
            self.body.index("## 2. Show the plan") : self.body.index("## 3. Migrate")
        ]
        self.assertIn("end your turn there", show)
        self.assertIn("Don't ask with a question dialog", show)
        self.assertIn("Once the user approves, run `run`", self.body)

    def test_track_points_a_corkboard_repo_to_migrate(self):
        self.assertIn("(`/github-tracking:migrate`)", skill("track")[1])
