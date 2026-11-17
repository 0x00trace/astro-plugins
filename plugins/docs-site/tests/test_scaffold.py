import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))
import scaffold

THEME = scaffold.THEME


def run(cwd, *args):
    """Run scaffold.py's main in cwd; return its exit code, stdout and stderr."""
    out, err = io.StringIO(), io.StringIO()
    with (
        contextlib.chdir(cwd),
        contextlib.redirect_stdout(out),
        contextlib.redirect_stderr(err),
    ):
        code = scaffold.main(list(args))
    return code, out.getvalue(), err.getvalue()


class RepoTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve() / "my-project"
        self.root.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)

    def remote(self, url):
        subprocess.run(
            ["git", "remote", "add", "origin", url], cwd=self.root, check=True
        )

    def read(self, name):
        return (self.root / name).read_text()


class NewRepoTest(RepoTest):
    def test_it_writes_the_config_the_home_page_and_the_ignore_line(self):
        self.remote("git@github.com:someone/my-project.git")
        code, out, _ = run(self.root, "--description", "Tools for\n  my project.")
        self.assertEqual(code, 0)
        self.assertEqual(
            self.read("mkdocs.yml"),
            'site_name: "my-project"\n'
            'repo_url: "https://github.com/someone/my-project"\n' + THEME,
        )
        self.assertEqual(
            self.read("docs/index.md"), "# my-project\n\nTools for my project.\n"
        )
        self.assertEqual(self.read(".gitignore"), "site/\n")
        self.assertEqual(
            out.splitlines(),
            [
                f"{self.root}:",
                "  created mkdocs.yml",
                "  created docs/index.md",
                "  created .gitignore with site/",
            ],
        )

    def test_the_config_has_no_nav_so_new_pages_show_on_their_own(self):
        run(self.root)
        self.assertNotRegex(self.read("mkdocs.yml"), r"(?m)^nav:")

    def test_a_second_run_changes_nothing(self):
        self.remote("https://github.com/someone/my-project.git")
        run(self.root, "--description", "First.")
        before = {
            p: (self.root / p).read_text()
            for p in ("mkdocs.yml", "docs/index.md", ".gitignore")
        }
        code, out, _ = run(self.root, "--name", "Other", "--description", "Second.")
        self.assertEqual(code, 0)
        self.assertEqual({p: (self.root / p).read_text() for p in before}, before)
        self.assertEqual(
            out.splitlines()[1:],
            [
                "  kept mkdocs.yml (it exists)",
                "  kept docs/index.md (it exists)",
                "  kept .gitignore (it ignores site/)",
            ],
        )

    def test_without_a_description_the_home_page_is_its_heading(self):
        run(self.root)
        self.assertEqual(self.read("docs/index.md"), "# my-project\n")

    def test_a_repo_with_no_remote_gets_no_repo_url(self):
        run(self.root)
        self.assertNotIn("repo_url", self.read("mkdocs.yml"))

    def test_name_overrides_the_folder_and_is_quoted(self):
        run(self.root, "--name", 'Docs: "a" #1')
        self.assertTrue(
            self.read("mkdocs.yml").startswith('site_name: "Docs: \\"a\\" #1"\n')
        )
        self.assertEqual(self.read("docs/index.md"), '# Docs: "a" #1\n')

    def test_run_from_a_subfolder_it_writes_at_the_repo_root(self):
        (self.root / "src" / "deep").mkdir(parents=True)
        code, out, _ = run(self.root / "src" / "deep")
        self.assertEqual(code, 0)
        self.assertTrue((self.root / "mkdocs.yml").is_file())
        self.assertTrue((self.root / "docs" / "index.md").is_file())
        self.assertFalse((self.root / "src" / "deep" / "mkdocs.yml").exists())
        self.assertEqual(out.splitlines()[0], f"{self.root}:")

    def test_outside_a_git_repo_it_uses_the_folder_it_runs_in(self):
        with tempfile.TemporaryDirectory() as plain:
            folder = Path(plain).resolve() / "notes"
            folder.mkdir()
            run(folder)
            self.assertTrue((folder / "mkdocs.yml").is_file())
            self.assertIn('site_name: "notes"', (folder / "mkdocs.yml").read_text())


class ExistingFilesTest(RepoTest):
    def test_an_existing_config_is_kept_and_its_docs_dir_used(self):
        (self.root / "mkdocs.yml").write_text(
            "site_name: Mine\ndocs_dir: handbook  # pages\n"
        )
        code, out, _ = run(self.root)
        self.assertEqual(code, 0)
        self.assertEqual(
            self.read("mkdocs.yml"), "site_name: Mine\ndocs_dir: handbook  # pages\n"
        )
        self.assertTrue((self.root / "handbook" / "index.md").is_file())
        self.assertFalse((self.root / "docs").exists())
        self.assertIn("  kept mkdocs.yml (it exists)", out.splitlines())
        self.assertIn("  created handbook/index.md", out.splitlines())

    def test_an_existing_zensical_toml_counts_as_the_config(self):
        (self.root / "zensical.toml").write_text('[project]\ndocs_dir = "pages"\n')
        run(self.root)
        self.assertFalse((self.root / "mkdocs.yml").exists())
        self.assertTrue((self.root / "pages" / "index.md").is_file())

    def test_an_existing_home_page_is_kept(self):
        (self.root / "docs").mkdir()
        (self.root / "docs" / "index.md").write_text("# Home\n\nMine.\n")
        run(self.root, "--description", "Not this.")
        self.assertEqual(self.read("docs/index.md"), "# Home\n\nMine.\n")

    def test_it_adds_the_ignore_line_after_a_file_with_no_final_newline(self):
        (self.root / ".gitignore").write_text("__pycache__/\n.venv")
        _, out, _ = run(self.root)
        self.assertEqual(self.read(".gitignore"), "__pycache__/\n.venv\nsite/\n")
        self.assertIn("  added site/ to .gitignore", out.splitlines())

    def test_any_form_of_the_site_line_counts(self):
        for line in ["site", "site/", "/site", "/site/"]:
            with self.subTest(line):
                (self.root / ".gitignore").write_text(f"x\n  {line}\n")
                run(self.root)
                self.assertEqual(self.read(".gitignore"), f"x\n  {line}\n")


class DocsDirTest(RepoTest):
    def test_a_docs_dir_elsewhere_goes_in_the_config(self):
        (self.root / ".project" / "docs").mkdir(parents=True)
        (self.root / ".project" / "docs" / "cli.md").write_text("# CLI\n")
        code, out, _ = run(self.root, "--docs-dir", ".project/docs/")
        self.assertEqual(code, 0)
        self.assertEqual(
            self.read("mkdocs.yml"),
            'site_name: "my-project"\ndocs_dir: ".project/docs"\n' + THEME,
        )
        self.assertEqual(self.read(".project/docs/index.md"), "# my-project\n")
        self.assertEqual(self.read(".project/docs/cli.md"), "# CLI\n")
        self.assertIn("  created .project/docs/index.md", out.splitlines())

    def test_an_absolute_docs_dir_inside_the_repo_is_made_relative(self):
        run(self.root, "--docs-dir", str(self.root / "handbook"))
        self.assertIn('docs_dir: "handbook"', self.read("mkdocs.yml"))

    def test_a_docs_dir_outside_the_repo_or_at_its_root_fails_and_writes_nothing(self):
        for docs_dir in ["..", "../elsewhere", ".", "/tmp"]:
            with self.subTest(docs_dir):
                code, out, err = run(self.root, "--docs-dir", docs_dir)
                self.assertEqual(code, 1)
                self.assertEqual(out, "")
                self.assertTrue(err.startswith("scaffold.py: --docs-dir "))
                self.assertEqual(sorted(p.name for p in self.root.iterdir()), [".git"])


class WebUrlTest(unittest.TestCase):
    def test_github_remotes_become_their_web_url(self):
        for remote in [
            "git@github.com:someone/my-project.git",
            "git@github.com:someone/my-project",
            "ssh://git@github.com/someone/my-project.git",
            "https://github.com/someone/my-project.git",
            "https://github.com/someone/my-project/",
            "https://someone:ghp_secret@github.com/someone/my-project.git",
        ]:
            with self.subTest(remote):
                self.assertEqual(
                    scaffold.web_url(remote), "https://github.com/someone/my-project"
                )

    def test_another_https_host_keeps_its_url_without_credentials(self):
        self.assertEqual(
            scaffold.web_url("https://me:token@gitlab.com/group/sub/project.git"),
            "https://gitlab.com/group/sub/project",
        )

    def test_a_remote_with_no_web_url_gives_none(self):
        for remote in [
            "git@gitlab.com:group/project.git",
            "/srv/git/project.git",
            "file:///x",
        ]:
            with self.subTest(remote):
                self.assertIsNone(scaffold.web_url(remote))


if __name__ == "__main__":
    unittest.main()
