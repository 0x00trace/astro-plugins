import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import fixture_repo

# Names in review-me's CLAUDE.md that are missing on purpose: D5's stale path, a file that's
# git-ignored, and one the file says never to commit.
MISSING_ON_PURPOSE = {"src/routes/", ".env", "package-lock.json"}
# dot-claude's build output.
BUILD_OUTPUT = {"bin/notes"}
# pnpm's own commands and package binaries, which aren't scripts in package.json.
PNPM_COMMANDS = {"install", "vitest"}
FILE = re.compile(r"^[\w.-]+\.(md|ts|mjs|sql|json|go|mod|example)$")


def git(repo, *args):
    command = ["git", "-C", str(repo), *args]
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout


def section(text, heading):
    start = text.index(f"\n{heading}\n")
    end = text.find("\n## ", start + 1)
    return text[start : end if end > 0 else None]


def named_paths(text):
    """The backticked spans in an instruction file that name a file or folder in the repo."""
    for span in re.findall(r"`([^`\n]+)`", text):
        if " " in span and not span.startswith("Design Docs/"):
            continue
        if span.startswith(("/", "~")) or re.search(r"[<>*(){}=$\"']", span):
            continue
        if "/" in span or FILE.match(span):
            yield span


class FixturesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory()
        root = Path(cls.scratch.name)
        cls.review_me = fixture_repo.build("review-me", root / "review-me")
        cls.dot_claude = fixture_repo.build("dot-claude", root / "dot-claude")
        cls.text = (cls.review_me / "CLAUDE.md").read_text()
        cls.scripts = json.loads((cls.review_me / "package.json").read_text())[
            "scripts"
        ]

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def test_the_stored_fixtures_never_load_in_this_repo(self):
        # A CLAUDE.md or .claude/ under tests/ would load into this repo's own sessions as soon as
        # Claude read a file next to it, flawed rules included.
        for path in fixture_repo.FIXTURES.rglob("*"):
            self.assertNotIn(
                path.name, {"CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", ".claude"}
            )

    def test_a_built_fixture_is_a_clean_git_repo_with_one_commit(self):
        for repo in (self.review_me, self.dot_claude):
            self.assertEqual(git(repo, "rev-list", "--count", "HEAD").strip(), "1")
            self.assertEqual(git(repo, "status", "--porcelain"), "")

    def test_the_readme_lists_the_cases_these_tests_check(self):
        readme = (fixture_repo.FIXTURES / "README.md").read_text()
        ids = re.findall(r"^\| ([DK]\d+) \|", readme, re.MULTILINE)
        self.assertEqual(ids, [f"D{n}" for n in range(1, 13)] + ["K1", "K2", "K3"])

    def test_review_me_holds_every_seeded_defect(self):
        text, repo = self.text, self.review_me
        with self.subTest("D1: over 200 lines"):
            self.assertGreater(len(text.splitlines()), 210)
        with self.subTest("D2: a dense paragraph of rules"):
            paragraph = section(text, "## Working rules").strip().split("\n\n")[1]
            self.assertNotIn("\n", paragraph)
            self.assertGreaterEqual(paragraph.count(". "), 5)
        with self.subTest("D3: pressure language"):
            self.assertIn("IMPORTANT: you MUST ALWAYS run `pnpm test`", text)
        with self.subTest("D4: a command that doesn't exist"):
            self.assertIn("`pnpm run lint:all`", text)
            self.assertNotIn("lint:all", self.scripts)
            self.assertIn("lint", self.scripts)
        with self.subTest("D5: a path that doesn't exist"):
            self.assertIn("Route handlers live in `src/routes/`", text)
            self.assertFalse((repo / "src" / "routes").exists())
            self.assertTrue((repo / "src" / "api" / "handlers.ts").exists())
        with self.subTest("D6: a contradiction with a rule file"):
            rule = (repo / ".claude" / "rules" / "testing.md").read_text()
            self.assertIn("Put each test next to the file it tests", text)
            self.assertIn("Put tests in `tests/`, never next to the source file", rule)
            self.assertFalse(
                rule.startswith("---"), "a rule with no paths loads in every session"
            )
        with self.subTest("D7: an import that stops at the space"):
            self.assertRegex(text, r"(?m)^API reference: @Design Docs/api\.md$")
            self.assertTrue((repo / "Design Docs" / "api.md").exists())
            self.assertFalse((repo / "Design").exists())
        with self.subTest("D8: a rule that must always hold"):
            self.assertIn("Never read or print `.env`", text)
        with self.subTest("D9: a directory tree"):
            self.assertIn("├──", section(text, "## Directory structure"))
        with self.subTest("D10: a procedure with several steps"):
            steps = re.findall(r"(?m)^\d+\. ", section(text, "## Releasing"))
            self.assertGreaterEqual(len(steps), 8)
        with self.subTest("D11: history"):
            self.assertIn("We moved from npm to pnpm in PR #12", text)

    def test_review_me_keeps_the_lines_a_review_must_not_cut(self):
        for line in [
            "Integration tests need `DATABASE_URL` pointed at a scratch database, never the dev one",
            "Use the error helpers in `src/lib/errors.ts`, never throw raw strings",
            "Run one test file with `pnpm vitest run tests/handlers.spec.ts`",
        ]:
            self.assertIn(line, self.text)

    def test_review_me_has_no_stale_name_but_the_seeded_ones(self):
        # A path or command that's missing by accident would be a defect the score doesn't count.
        for path in set(named_paths(self.text)) - MISSING_ON_PURPOSE:
            self.assertTrue((self.review_me / path).exists(), path)
        self.assertTrue((self.review_me / "tests" / "handlers.spec.ts").exists())
        for name in (
            set(re.findall(r"`pnpm (?:run )?([\w:-]+)", self.text)) - PNPM_COMMANDS
        ):
            if name != "lint:all":
                self.assertIn(name, self.scripts)

    def test_dot_claude_keeps_a_sound_file_under_dot_claude(self):
        # D12: the project file can live at ./.claude/CLAUDE.md, and nothing else is wrong with it.
        text = (self.dot_claude / ".claude" / "CLAUDE.md").read_text()
        self.assertFalse((self.dot_claude / "CLAUDE.md").exists())
        self.assertLess(len(text.splitlines()), 50)
        for path in set(named_paths(text)) - BUILD_OUTPUT:
            self.assertTrue((self.dot_claude / path).exists(), path)
        targets = re.findall(r"(?m)^(\w+):", (self.dot_claude / "Makefile").read_text())
        for target in re.findall(r"`make (\w+)`", text):
            self.assertIn(target, targets)


if __name__ == "__main__":
    unittest.main()
