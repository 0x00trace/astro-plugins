import contextlib
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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
    """A git repo in a temporary folder, with its own record of ports and no port in use."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name).resolve()
        self.root = self.repo("my-project")
        data = self.tmp / "data"
        env = mock.patch.dict(os.environ, {"XDG_DATA_HOME": str(data)})
        env.start()
        self.addCleanup(env.stop)
        self.record = data / "docs-site" / "ports.json"
        self.busy = set()
        probe = mock.patch.object(scaffold, "in_use", lambda port: port in self.busy)
        probe.start()
        self.addCleanup(probe.stop)

    def repo(self, name):
        root = self.tmp / name
        root.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        return root

    def remote(self, url):
        subprocess.run(
            ["git", "remote", "add", "origin", url], cwd=self.root, check=True
        )

    def read(self, name):
        return (self.root / name).read_text()

    def ports(self):
        return json.loads(self.record.read_text())


class NewRepoTest(RepoTest):
    def test_it_writes_the_config_the_home_page_and_the_ignore_line(self):
        self.remote("git@github.com:someone/my-project.git")
        code, out, _ = run(self.root, "--description", "Tools for\n  my project.")
        self.assertEqual(code, 0)
        self.assertEqual(
            self.read("mkdocs.yml"),
            "site_name: my-project\n"
            "repo_url: https://github.com/someone/my-project\n"
            "site_dir: .site\n"
            "dev_addr: 127.0.0.1:8100\n" + THEME,
        )
        self.assertEqual(
            self.read("docs/index.md"), "# my-project\n\nTools for my project.\n"
        )
        self.assertEqual(self.read(".gitignore"), ".site/\n.cache/\n")
        self.assertEqual(
            out.splitlines(),
            [
                f"{self.root}:",
                "  created mkdocs.yml, with dev_addr 127.0.0.1:8100",
                "  created docs/index.md",
                "  created .gitignore with .site/ and .cache/",
                "  uvx zensical serve shows it at http://127.0.0.1:8100",
            ],
        )

    def test_the_config_has_no_nav_so_new_pages_show_on_their_own(self):
        run(self.root)
        self.assertNotRegex(self.read("mkdocs.yml"), r"(?m)^nav:")

    def test_a_second_run_changes_nothing(self):
        self.remote("https://github.com/someone/my-project.git")
        run(self.root, "--description", "First.")
        files = ("mkdocs.yml", "docs/index.md", ".gitignore")
        before = {p: self.read(p) for p in files}
        record = self.record.read_text()
        code, out, _ = run(self.root, "--name", "Other", "--description", "Second.")
        self.assertEqual(code, 0)
        self.assertEqual({p: self.read(p) for p in files}, before)
        self.assertEqual(self.record.read_text(), record)
        self.assertEqual(
            out.splitlines()[1:],
            [
                "  kept mkdocs.yml (it exists)",
                "  kept dev_addr 127.0.0.1:8100 in mkdocs.yml",
                "  kept site_dir .site in mkdocs.yml",
                "  kept docs/index.md (it exists)",
                "  kept .gitignore (it ignores .site/ and .cache/)",
                "  uvx zensical serve shows it at http://127.0.0.1:8100",
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
        folder = self.tmp / "notes"
        folder.mkdir()
        run(folder)
        self.assertTrue((folder / "mkdocs.yml").is_file())
        self.assertIn("site_name: notes", (folder / "mkdocs.yml").read_text())


class PortTest(RepoTest):
    def test_each_repo_gets_its_own_port_and_keeps_it(self):
        other = self.repo("other")
        run(self.root)
        run(other)
        run(self.root)
        self.assertIn("dev_addr: 127.0.0.1:8100", self.read("mkdocs.yml"))
        self.assertIn("dev_addr: 127.0.0.1:8101", (other / "mkdocs.yml").read_text())
        self.assertEqual(self.ports(), {str(self.root): 8100, str(other): 8101})

    def test_a_port_in_use_now_is_skipped(self):
        self.busy = {8100, 8101}
        run(self.root)
        self.assertIn("dev_addr: 127.0.0.1:8102", self.read("mkdocs.yml"))

    def test_a_repo_keeps_its_port_while_its_own_site_is_running(self):
        run(self.root)
        self.busy = {8100}
        _, out, _ = run(self.root)
        self.assertIn("  kept dev_addr 127.0.0.1:8100 in mkdocs.yml", out.splitlines())

    def test_a_config_without_dev_addr_gets_the_line(self):
        (self.root / "mkdocs.yml").write_text("site_name: Mine")
        _, out, _ = run(self.root)
        self.assertEqual(
            self.read("mkdocs.yml"),
            "site_name: Mine\ndev_addr: 127.0.0.1:8100\nsite_dir: .site\n",
        )
        self.assertIn("  added dev_addr 127.0.0.1:8100 to mkdocs.yml", out.splitlines())

    def test_a_configs_own_free_port_is_kept_and_recorded(self):
        (self.root / "mkdocs.yml").write_text(
            "site_name: Mine\ndev_addr: localhost:8500\nsite_dir: .site\n"
        )
        run(self.root)
        self.assertEqual(
            self.read("mkdocs.yml"),
            "site_name: Mine\ndev_addr: localhost:8500\nsite_dir: .site\n",
        )
        self.assertEqual(self.ports(), {str(self.root): 8500})

    def test_a_config_with_another_repos_port_gets_a_new_one(self):
        other = self.repo("other")
        run(other)
        shutil.copy(other / "mkdocs.yml", self.root / "mkdocs.yml")
        code, out, _ = run(self.root)
        self.assertEqual(code, 0)
        self.assertIn("dev_addr: 127.0.0.1:8101", self.read("mkdocs.yml"))
        self.assertIn(
            "  changed dev_addr in mkdocs.yml from 127.0.0.1:8100 to 127.0.0.1:8101,"
            f" as 8100 is the port of {other}",
            out.splitlines(),
        )
        self.assertEqual(self.ports(), {str(other): 8100, str(self.root): 8101})

    def test_a_repo_that_is_gone_gives_its_port_back(self):
        gone = self.repo("gone")
        run(gone)
        shutil.rmtree(gone)
        run(self.root)
        self.assertIn("dev_addr: 127.0.0.1:8100", self.read("mkdocs.yml"))
        self.assertEqual(self.ports(), {str(self.root): 8100})

    def test_a_zensical_toml_without_dev_addr_is_left_alone_and_named(self):
        (self.root / "zensical.toml").write_text('[project]\nsite_name = "x"\n')
        _, out, _ = run(self.root)
        self.assertEqual(self.read("zensical.toml"), '[project]\nsite_name = "x"\n')
        self.assertIn(
            '  zensical.toml has no dev_addr: add dev_addr = "127.0.0.1:8100" under [project]',
            out.splitlines(),
        )

    def test_a_zensical_toml_with_another_repos_port_is_changed(self):
        other = self.repo("other")
        run(other)
        (self.root / "zensical.toml").write_text(
            '[project]\ndev_addr = "127.0.0.1:8100"  # serve here\n'
        )
        run(self.root)
        self.assertEqual(
            self.read("zensical.toml"),
            '[project]\ndev_addr = "127.0.0.1:8101"  # serve here\n',
        )

    def test_an_unreadable_dev_addr_fails_and_changes_nothing(self):
        (self.root / "mkdocs.yml").write_text("dev_addr: somewhere\n")
        code, out, err = run(self.root)
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("can't read a port in mkdocs.yml's dev_addr: somewhere", err)
        self.assertEqual(self.read("mkdocs.yml"), "dev_addr: somewhere\n")
        self.assertFalse(self.record.exists())

    def test_a_broken_record_fails_with_its_path(self):
        self.record.parent.mkdir(parents=True)
        self.record.write_text("{")
        code, _, err = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn(f"{self.record} isn't valid JSON", err)

    def test_when_every_port_is_taken_it_fails(self):
        self.busy = set(scaffold.PORTS)
        code, _, err = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("no free port from 8100 to 8999", err)
        self.assertFalse((self.root / "mkdocs.yml").exists())


class HubTest(RepoTest):
    def hub(self, result):
        """Pretend a hub is installed, and that hub.py answers with result."""
        compose = self.record.parent / "hub" / "compose.yml"
        compose.parent.mkdir(parents=True)
        compose.write_text("name: docs-site\n")
        self.asked = []

        def run_hub(root):
            # By now the repo has to be in the record, or the hub can't find it.
            self.asked.append((root, json.loads(self.record.read_text())))
            return result

        patch = mock.patch.object(scaffold, "run_hub", run_hub)
        patch.start()
        self.addCleanup(patch.stop)

    def test_run_hub_runs_hub_py_which_does_nothing_without_a_hub(self):
        # The real call: this interpreter, hub.py beside scaffold.py, and the record in the environment.
        self.assertEqual(scaffold.run_hub(self.root), (0, "", ""))

    def test_with_no_hub_installed_hub_py_is_not_run(self):
        with mock.patch.object(scaffold, "run_hub", side_effect=AssertionError):
            code, out, _ = run(self.root)
        self.assertEqual(code, 0)
        self.assertNotIn("hub", out)

    def test_with_a_hub_the_repo_is_added_and_its_address_reported(self):
        self.hub((0, "the hub serves it at http://my-project.localhost:8099\n", ""))
        code, out, _ = run(self.root)
        self.assertEqual(code, 0)
        self.assertEqual(
            out.splitlines()[-2:],
            [
                "  uvx zensical serve shows it at http://127.0.0.1:8100",
                "  the hub serves it at http://my-project.localhost:8099",
            ],
        )
        self.assertEqual(self.asked, [(self.root, {str(self.root): 8100})])

    def test_a_hub_that_fails_is_reported_and_the_site_is_still_set_up(self):
        self.hub((1, "", "hub.py: Cannot connect to the Docker daemon\n"))
        code, out, _ = run(self.root)
        self.assertEqual(code, 0)
        self.assertEqual(
            out.splitlines()[-1],
            "  the hub wasn't updated: Cannot connect to the Docker daemon",
        )
        self.assertTrue((self.root / "mkdocs.yml").is_file())


class InUseTest(unittest.TestCase):
    def test_a_bound_port_is_in_use_and_a_released_one_is_not(self):
        with socket.socket() as held:
            held.bind((scaffold.HOST, 0))
            held.listen()
            port = held.getsockname()[1]
            self.assertTrue(scaffold.in_use(port))
        self.assertFalse(scaffold.in_use(port))


class ExistingFilesTest(RepoTest):
    def test_an_existing_config_is_kept_and_its_docs_dir_used(self):
        config = (
            "site_name: Mine\ndocs_dir: handbook  # pages\nsite_dir: .site\n"
            "dev_addr: 127.0.0.1:8100\n"
        )
        (self.root / "mkdocs.yml").write_text(config)
        code, out, _ = run(self.root)
        self.assertEqual(code, 0)
        self.assertEqual(self.read("mkdocs.yml"), config)
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
        self.assertEqual(
            self.read(".gitignore"), "__pycache__/\n.venv\n.site/\n.cache/\n"
        )
        self.assertIn("  added .site/ and .cache/ to .gitignore", out.splitlines())

    def test_any_form_of_the_ignore_lines_counts(self):
        for line in [".site", ".site/", "/.site", "/.site/"]:
            with self.subTest(line):
                (self.root / ".gitignore").write_text(f"x\n  {line}\n/.cache\n")
                run(self.root)
                self.assertEqual(self.read(".gitignore"), f"x\n  {line}\n/.cache\n")

    def test_a_gitignore_with_the_site_folder_gets_only_the_cache_line(self):
        (self.root / ".gitignore").write_text(".site/\n")
        _, out, _ = run(self.root)
        self.assertEqual(self.read(".gitignore"), ".site/\n.cache/\n")
        self.assertIn("  added .cache/ to .gitignore", out.splitlines())


class SiteDirTest(RepoTest):
    def test_a_config_without_site_dir_gets_the_line_and_its_ignore_line(self):
        # A repo set up before docs-site built into .site: its old site/ line stays.
        (self.root / "mkdocs.yml").write_text(
            "site_name: Mine\ndev_addr: 127.0.0.1:8100\n"
        )
        (self.root / ".gitignore").write_text("site/\n.cache/\n")
        code, out, _ = run(self.root)
        self.assertEqual(code, 0)
        self.assertEqual(
            self.read("mkdocs.yml"),
            "site_name: Mine\ndev_addr: 127.0.0.1:8100\nsite_dir: .site\n",
        )
        self.assertEqual(self.read(".gitignore"), "site/\n.cache/\n.site/\n")
        self.assertIn("  added site_dir .site to mkdocs.yml", out.splitlines())
        self.assertIn("  added .site/ to .gitignore", out.splitlines())

    def test_a_configs_own_site_dir_is_kept_and_ignored(self):
        config = "site_name: Mine\nsite_dir: 'public/'  # built here\n"
        (self.root / "mkdocs.yml").write_text(config)
        _, out, _ = run(self.root)
        self.assertEqual(self.read("mkdocs.yml"), config + "dev_addr: 127.0.0.1:8100\n")
        self.assertEqual(self.read(".gitignore"), "public/\n.cache/\n")
        self.assertIn("  kept site_dir public/ in mkdocs.yml", out.splitlines())

    def test_a_zensical_toml_without_site_dir_is_left_alone_and_named(self):
        (self.root / "zensical.toml").write_text(
            '[project]\ndev_addr = "127.0.0.1:8100"\n'
        )
        _, out, _ = run(self.root)
        self.assertEqual(
            self.read("zensical.toml"), '[project]\ndev_addr = "127.0.0.1:8100"\n'
        )
        self.assertIn(
            '  zensical.toml has no site_dir: add site_dir = ".site" under [project]',
            out.splitlines(),
        )
        self.assertEqual(self.read(".gitignore"), ".site/\n.cache/\n")

    def test_a_zensical_toml_with_site_dir_keeps_it(self):
        (self.root / "zensical.toml").write_text(
            '[project]\nsite_dir = ".site"\ndev_addr = "127.0.0.1:8100"\n'
        )
        _, out, _ = run(self.root)
        self.assertIn("  kept site_dir .site in zensical.toml", out.splitlines())
        self.assertNotIn("has no site_dir", out)


class DocsDirTest(RepoTest):
    def test_a_docs_dir_elsewhere_goes_in_the_config(self):
        (self.root / ".project" / "docs").mkdir(parents=True)
        (self.root / ".project" / "docs" / "cli.md").write_text("# CLI\n")
        code, out, _ = run(self.root, "--docs-dir", ".project/docs/")
        self.assertEqual(code, 0)
        self.assertEqual(
            self.read("mkdocs.yml"),
            "site_name: my-project\ndocs_dir: .project/docs\nsite_dir: .site\n"
            "dev_addr: 127.0.0.1:8100\n" + THEME,
        )
        self.assertEqual(self.read(".project/docs/index.md"), "# my-project\n")
        self.assertEqual(self.read(".project/docs/cli.md"), "# CLI\n")
        self.assertIn("  created .project/docs/index.md", out.splitlines())

    def test_an_absolute_docs_dir_inside_the_repo_is_made_relative(self):
        run(self.root, "--docs-dir", str(self.root / "handbook"))
        self.assertIn("docs_dir: handbook", self.read("mkdocs.yml"))

    def test_a_docs_dir_outside_the_repo_or_at_its_root_fails_and_writes_nothing(self):
        for docs_dir in ["..", "../elsewhere", ".", "/tmp"]:
            with self.subTest(docs_dir):
                code, out, err = run(self.root, "--docs-dir", docs_dir)
                self.assertEqual(code, 1)
                self.assertEqual(out, "")
                self.assertTrue(err.startswith("scaffold.py: --docs-dir "))
                self.assertEqual(sorted(p.name for p in self.root.iterdir()), [".git"])
                self.assertFalse(self.record.exists())


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


class ScalarTest(unittest.TestCase):
    def test_text_yaml_reads_as_text_goes_without_quotes(self):
        for text in [
            "astrocode",
            "my-project",
            "My project",
            "https://github.com/o/r",
            "127.0.0.1:8101",
            ".project/docs",
            "v1.2",
        ]:
            with self.subTest(text):
                self.assertEqual(scaffold.scalar(text), text)

    def test_text_yaml_would_read_as_something_else_is_quoted(self):
        for text in [
            "12",
            "1.5",
            "0x1F",
            "1:20",
            "yes",
            "No",
            "null",
            "~",
            ".inf",
            "2026-11-17",
            "a: b",
            "a:",
            "#x",
            "-x",
            "it's",
            "",
        ]:
            with self.subTest(text):
                self.assertEqual(scaffold.scalar(text), json.dumps(text))
