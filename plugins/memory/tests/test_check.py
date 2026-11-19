"""Tests for skills/init/scripts/check.py. Each test builds a project and a home folder in a
temporary directory, runs the script there and reads its report."""

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1] / "skills" / "init" / "scripts" / "check.py"
)
SPEC = importlib.util.spec_from_file_location("memory_check", SCRIPT)
check = sys.modules["memory_check"] = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check)

ENTRY = (
    "---\nname: {name}\ndescription: A fact.\nmetadata:\n  type: {type}\n---\n\nBody.\n"
)


class Sandbox:
    """A home folder holding ~/.claude and a project at ~/proj."""

    def __init__(self, test: unittest.TestCase):
        tmp = tempfile.TemporaryDirectory()
        test.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name).resolve()
        self.home = self.base / "home"
        self.project = self.home / "proj"
        self.config = self.home / ".claude"
        self.memory = self.config / "projects" / "proj" / "memory"
        self.project.mkdir(parents=True)

    def write(self, rel: str, text: str, base: Path | None = None) -> Path:
        path = (base or self.project) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def memories(self, base: Path, *entries: tuple[str, str], index: str | None = None):
        for name, kind in entries:
            self.write(f"{name}.md", ENTRY.format(name=name, type=kind), base)
        lines = [f"- [{n}]({n}.md) — a fact" for n, _ in entries]
        self.write(
            "MEMORY.md", index if index is not None else "\n".join(lines) + "\n", base
        )

    def git_init(self):
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)

    def run(self, *args: str) -> str:
        env = {
            **os.environ,
            "HOME": str(self.home),
            "GIT_CEILING_DIRECTORIES": str(self.base),
        }
        env.pop("CLAUDE_CONFIG_DIR", None)
        command = [sys.executable, str(SCRIPT), "--root", str(self.project), *args]
        done = subprocess.run(
            command, env=env, capture_output=True, text=True, check=True
        )
        return done.stdout


class ImportTest(unittest.TestCase):
    def test_an_import_resolves_from_the_file_that_has_it(self):
        s = Sandbox(self)
        s.write("docs/a.md", "@b.md\n")
        s.write("docs/b.md", "b\n")
        s.write("CLAUDE.md", "See @docs/a.md.\n")
        out = s.run()
        self.assertIn("1 line, 3 with imports", out)
        self.assertIn("Problems: none found.", out)

    def test_a_space_needs_a_backslash_and_a_quoted_path_isnt_imported(self):
        s = Sandbox(self)
        s.write("Design Docs/api.md", "api\n")
        s.write("CLAUDE.md", '@Design\\ Docs/api.md\n@"Design Docs/api.md"\n')
        out = s.run()
        self.assertIn('CLAUDE.md:2  @"Design Docs/api.md" is quoted', out)
        self.assertIn("Problems (1)", out)

    def test_code_and_comments_hold_no_imports(self):
        s = Sandbox(self)
        s.write(
            "CLAUDE.md",
            "Install `@types/node` first.\n```\n@missing.md\n```\n<!-- @gone.md\n@also-gone.md -->\n",
        )
        self.assertIn("Problems: none found.", s.run())

    def test_a_missing_import_is_a_problem(self):
        s = Sandbox(self)
        s.write("CLAUDE.md", "# Rules\n\nSee @docs/api.md for the API.\n")
        self.assertIn("CLAUDE.md:3  @docs/api.md doesn't exist", s.run())

    def test_imports_past_four_hops_dont_load(self):
        s = Sandbox(self)
        s.write("CLAUDE.md", "@1.md\n")
        for n in range(1, 5):
            s.write(f"{n}.md", f"@{n + 1}.md\n")
        s.write("5.md", "five\n")
        out = s.run()
        self.assertIn("4.md:1  @5.md is 5 imports deep", out)
        self.assertIn("Problems (1)", out)

    def test_a_cycle_loads_each_file_once(self):
        s = Sandbox(self)
        s.write("CLAUDE.md", "@a.md\n")
        s.write("a.md", "@b.md\n")
        s.write("b.md", "@a.md\n")
        self.assertIn("1 line, 3 with imports", s.run())

    def test_imported_lines_count_toward_the_200(self):
        s = Sandbox(self)
        s.write("CLAUDE.md", "@more.md\n" + "- a rule\n" * 149)
        s.write("more.md", "- another rule\n" * 60)
        self.assertIn("CLAUDE.md  210 lines with its imports", s.run())


class NamedPathTest(unittest.TestCase):
    def test_only_paths_that_dont_exist_are_listed(self):
        s = Sandbox(self)
        s.write("scripts/build.sh", "")
        s.write("package.json", "{}")
        s.write(
            "CLAUDE.md",
            "Run `scripts/build.sh`, see `package.json:12` and `docs/gone.md`.\n"
            "Use `/compact`, `github.com/a/b`, `npm test` and `os.path`.\n",
        )
        out = s.run()
        self.assertIn("CLAUDE.md:1  `docs/gone.md`", out)
        listed = out.split("don't exist (some may be examples):")[1].split("\n\n")[0]
        self.assertEqual(listed.strip().count("\n"), 0, listed)


class RuleTest(unittest.TestCase):
    def test_a_rule_without_paths_loads_at_launch(self):
        s = Sandbox(self)
        s.write(".claude/rules/style.md", "- Use tabs.\n")
        launch = s.run().split("Load at launch:")[1].split("\n\n")[0]
        self.assertIn(".claude/rules/style.md", launch)

    def test_a_rule_with_paths_loads_with_matching_files(self):
        s = Sandbox(self)
        s.write("src/api/handler.ts", "")
        s.write(
            ".claude/rules/api.md",
            '---\npaths:\n  - "src/**/*.ts"\n---\n- Validate input.\n',
        )
        out = s.run()
        self.assertIn("Load when Claude works with matching files:", out)
        self.assertIn("paths: src/**/*.ts", out)
        self.assertIn("Problems: none found.", out)
        self.assertNotIn("matches no file", out)

    def test_an_unquoted_star_breaks_the_frontmatter(self):
        s = Sandbox(self)
        s.write(".claude/rules/ts.md", "---\npaths: **/*.ts\n---\n- Prefer type.\n")
        self.assertIn("frontmatter doesn't parse", s.run())

    def test_fields_other_than_paths_are_ignored(self):
        s = Sandbox(self)
        s.write("a.py", "")
        s.write(
            ".claude/rules/py.md", "---\ndescription: Python\npaths: '*.py'\n---\n- x\n"
        )
        self.assertIn("`description:` is ignored", s.run())

    def test_a_pattern_that_matches_nothing_is_noted(self):
        s = Sandbox(self)
        s.write(".claude/rules/old.md", "---\npaths: legacy/**, src/[ab.ts\n---\n- x\n")
        out = s.run()
        self.assertIn("`legacy/**` matches no file in the project", out)
        self.assertIn("`src/[ab.ts` has a [ with no ]", out)

    def test_globs(self):
        cases = [
            ("*.md", "docs/a.md", True),
            ("/*.md", "docs/a.md", False),
            ("/*.md", "a.md", True),
            ("src/**/*.ts", "src/a.ts", True),
            ("src/**/*.ts", "src/x/y/a.ts", True),
            ("src/**/*.ts", "lib/src/a.ts", False),
            ("tests/", "tests/unit/a.py", True),
        ]
        for pattern, path, expected in cases:
            with self.subTest(pattern=pattern, path=path):
                self.assertEqual(bool(check.glob_regex(pattern).match(path)), expected)
        self.assertEqual(
            check.expand_braces("src/*.{ts,tsx}"), ["src/*.ts", "src/*.tsx"]
        )


class AgentsTest(unittest.TestCase):
    def test_agents_md_loads_when_no_claude_md_exists(self):
        s = Sandbox(self)
        s.write("AGENTS.md", "- Run make test.\n")
        launch = s.run().split("Load at launch:")[1]
        self.assertIn("AGENTS.md", launch)

    def test_a_claude_md_stops_agents_md_loading(self):
        s = Sandbox(self)
        s.write("AGENTS.md", "- Run make test.\n")
        s.write("CLAUDE.local.md", "- I'm new here.\n")
        self.assertIn("not read, because a CLAUDE.md file exists", s.run())

    def test_an_import_loads_agents_md_with_claude_md(self):
        s = Sandbox(self)
        s.write("AGENTS.md", "- Run make test.\n")
        s.write("CLAUDE.md", "@AGENTS.md\n")
        self.assertIn("loads through an @ import", s.run())


class LocalFileTest(unittest.TestCase):
    def test_claude_local_md_must_be_gitignored(self):
        s = Sandbox(self)
        s.git_init()
        s.write("CLAUDE.local.md", "- My sandbox is at localhost:3000.\n")
        self.assertIn("isn't gitignored", s.run())
        s.write(".gitignore", "CLAUDE.local.md\n")
        self.assertNotIn("isn't gitignored", s.run())


class AutoMemoryTest(unittest.TestCase):
    def test_index_and_files_are_checked_against_each_other(self):
        s = Sandbox(self)
        s.memories(s.memory, ("role", "user"), ("testing", "feedback"))
        s.write("orphan.md", ENTRY.format(name="orphan", type="project"), s.memory)
        s.write(
            "MEMORY.md",
            (s.memory / "MEMORY.md").read_text() + "- [Gone](gone.md) — x\n",
            s.memory,
        )
        s.write("odd.md", ENTRY.format(name="odd", type="note"), s.memory)
        s.write("bare.md", "Just text.\n", s.memory)
        out = s.run("--memory-dir", str(s.memory))
        self.assertIn("MEMORY.md:3  links to gone.md, which doesn't exist", out)
        self.assertIn("orphan.md  isn't in MEMORY.md", out)
        self.assertIn("odd.md:1  type is note", out)
        self.assertIn("bare.md:1  has no frontmatter", out)

    def test_entries_past_200_lines_never_load(self):
        s = Sandbox(self)
        names = [(f"m{n}", "project") for n in range(201)]
        s.memories(s.memory, *names)
        out = s.run("--memory-dir", str(s.memory))
        self.assertIn("MEMORY.md:201  m200.md is past the first 200 lines", out)
        self.assertNotIn("MEMORY.md:200  ", out)

    def test_a_memory_naming_a_missing_path_is_listed(self):
        s = Sandbox(self)
        s.memories(s.memory, ("db", "project"))
        s.write(
            "db.md",
            ENTRY.format(name="db", type="project") + "See `src/db.ts`.\n",
            s.memory,
        )
        self.assertIn("db.md:9  `src/db.ts`", s.run("--memory-dir", str(s.memory)))


class GlobalMemoryTest(unittest.TestCase):
    def test_global_memory_keeps_the_plugin_limits(self):
        s = Sandbox(self)
        folder = s.config / "memory"
        s.memories(folder, ("shell", "user"), ("work", "project"))
        s.write(
            "big.md", ENTRY.format(name="large", type="feedback") + "x" * 4100, folder
        )
        index = (
            (folder / "MEMORY.md").read_text() + "- [Big](big.md) — " + "y" * 150 + "\n"
        )
        s.write("MEMORY.md", index, folder)
        out = s.run()
        self.assertIn("work.md:1  type is project", out)
        self.assertIn("big.md:1  name large isn't the file's name", out)
        self.assertIn("big.md  is 4,", out)
        self.assertIn("MEMORY.md:3  is 168 characters", out)


class PathModeTest(unittest.TestCase):
    def test_named_files_and_folders_are_checked_alone(self):
        s = Sandbox(self)
        s.write("CLAUDE.md", "@nope.md\n")
        s.write("other/CLAUDE.md", "fine\n")
        s.memories(s.memory, ("role", "user"))
        out = s.run(str(s.project / "CLAUDE.md"), str(s.memory))
        self.assertIn("@nope.md doesn't exist", out)
        self.assertIn("auto memory", out)
        self.assertNotIn("other/CLAUDE.md", out)


class FrontmatterTest(unittest.TestCase):
    def test_the_yaml_frontmatter_holds(self):
        data, error = check.parse_yaml(
            "name: x\ndescription: >\n  two\n  lines\nmetadata:\n  type: user\n"
            "paths: [a, 'b']\nlist:\n  - one\n"
        )
        self.assertIsNone(error)
        self.assertEqual(data["description"], "two lines")
        self.assertEqual(data["metadata"], {"type": "user"})
        self.assertEqual(data["paths"], ["a", "b"])
        self.assertEqual(data["list"], ["one"])

    def test_broken_yaml_is_an_error(self):
        for text in ["name: 'x", "paths: **/*.ts", "a: b: c", "  - stray"]:
            with self.subTest(text=text):
                self.assertIsNotNone(check.parse_yaml(text)[1])


if __name__ == "__main__":
    unittest.main()
