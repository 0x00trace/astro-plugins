import contextlib
import io
import re
import sys
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))
import scaffold

SCRIPT = "${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py"


def skill():
    _, front, body = (
        (PLUGIN / "skills" / "init" / "SKILL.md").read_text().split("---\n", 2)
    )
    return front, body


def allowed(front):
    line = next(
        line for line in front.splitlines() if line.startswith("allowed-tools:")
    )
    return re.findall(r"Bash\(([^)]*)\)", line)


class InitSkillTest(unittest.TestCase):
    def setUp(self):
        self.front, self.body = skill()

    def test_every_command_it_runs_is_pre_approved(self):
        # An unapproved run stops the skill for a permission prompt, or fails outright under -p.
        runs = re.findall(r"(?m)^(python3 \S+|uvx zensical build)\b", self.body)
        self.assertEqual(set(runs), {f"python3 {SCRIPT}", "uvx zensical build"})
        for command in set(runs):
            self.assertIn(f"{command} *", allowed(self.front))

    def test_it_runs_the_script_at_the_plugin_root(self):
        self.assertIn(f"python3 {SCRIPT} ", self.body)
        self.assertTrue((PLUGIN / "scripts" / "scaffold.py").is_file())

    def test_every_option_it_names_is_one_the_script_takes(self):
        named = set(re.findall(r"`(--[a-z-]+)`", self.body)) | set(
            re.findall(rf"{re.escape(SCRIPT)} (--[a-z-]+)", self.body)
        )
        self.assertEqual(named, {"--description", "--docs-dir", "--name"})
        out = io.StringIO()
        with self.assertRaises(SystemExit), contextlib.redirect_stdout(out):
            scaffold.main(["--help"])
        for option in named:
            self.assertIn(option, out.getvalue())

    def test_it_names_the_words_the_script_reports(self):
        source = (PLUGIN / "scripts" / "scaffold.py").read_text()
        for word in ["created", "kept", "added", "changed"]:
            self.assertIn(f"{word} ", source)
        self.assertIn("created, kept, added or changed", self.body)
        self.assertIn("scaffold.py: --docs-dir", self.body)
        self.assertIn('f"--docs-dir {docs_dir}', source)

    def test_it_writes_no_pages_workflow_and_commits_nothing(self):
        # Sites are read locally with zensical serve, the same in public and private repos.
        self.assertIn("commits nothing", self.body)
        self.assertNotIn("workflow", self.body)
        self.assertNotIn("git commit", self.body)


if __name__ == "__main__":
    unittest.main()


def hub_skill():
    _, front, body = (
        (PLUGIN / "skills" / "hub" / "SKILL.md").read_text().split("---\n", 2)
    )
    return front, body


class HubSkillTest(unittest.TestCase):
    def setUp(self):
        import hub

        self.hub = hub
        self.front, self.body = hub_skill()
        self.script = "${CLAUDE_PLUGIN_ROOT}/scripts/hub.py"

    def test_only_status_is_pre_approved(self):
        # install and remove start and stop containers, so the user sees each one asked for.
        self.assertEqual(allowed(self.front), [f"python3 {self.script} status"])

    def test_every_command_it_names_is_one_hub_py_has(self):
        named = set(re.findall(rf"{re.escape(self.script)} ([a-z]+)", self.body))
        self.assertEqual(named, {"install", "status", "remove"})
        for command in named:
            out = io.StringIO()
            with self.assertRaises(SystemExit) as done, contextlib.redirect_stdout(out):
                self.hub.main([command, "--help"])
            self.assertEqual(done.exception.code, 0, command)
        self.assertTrue((PLUGIN / "scripts" / "hub.py").is_file())

    def test_it_names_the_port_project_images_and_files_hub_py_uses(self):
        self.assertIn(f"http://localhost:{self.hub.PORT}", self.front + self.body)
        self.assertIn(f"`{self.hub.PROJECT}`", self.body)
        self.assertIn(f"docker compose -p {self.hub.PROJECT} logs site-NAME", self.body)
        for image in (self.hub.ZENSICAL.split(":")[0], self.hub.CADDY):
            self.assertIn(f"`{image}`", self.body)
        for name in self.hub.FILES:
            self.assertIn(name, self.body)

    def test_it_says_the_words_hub_py_prints(self):
        source = (PLUGIN / "scripts" / "hub.py").read_text()
        for words in ["not answering yet", "not answering", "container "]:
            self.assertIn(words, source)
            self.assertIn(words, self.body)
        self.assertIn("is not running", source)
        self.assertIn('"The docs site for NAME is not running"', self.body)

    def test_init_says_what_it_does_when_a_hub_is_installed(self):
        _, body = skill()
        self.assertIn("(`/docs-site:hub`)", body)
        self.assertIn("the hub wasn't updated", body)
        self.assertIn(
            "f\"the hub wasn't updated: ",
            (PLUGIN / "scripts" / "scaffold.py").read_text(),
        )
