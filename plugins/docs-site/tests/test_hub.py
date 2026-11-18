import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))
import hub

# The real function, for the tests that fake the docker command itself.
REAL_DOCKER = hub.docker


class FakeDocker:
    """Answers hub.docker's calls the way Docker would, and records them."""

    def __init__(self):
        self.calls = []
        self.proxy_running = False
        self.reload_failures = 0
        self.states = {}

    def __call__(self, *args, check=True):
        self.calls.append(args)
        if args[:2] == ("compose", "version"):
            return "Docker Compose version 5.7.1\n"
        rest = args[3:]
        if rest[:1] == ("ps",) and "-q" in rest:
            return "abc123\n" if self.proxy_running else ""
        if rest[:1] == ("ps",):
            return "\n".join(
                json.dumps({"Service": service, "State": state})
                for service, state in self.states.items()
            )
        if rest[:1] == ("up",):
            self.proxy_running = True
        if rest[:1] == ("exec",) and self.reload_failures:
            self.reload_failures -= 1
            raise hub.Fail("caddy isn't ready")
        if rest[:1] == ("down",):
            self.proxy_running = False
        return ""

    def ran(self, *words):
        """How many compose calls started with these words."""
        return sum(1 for call in self.calls if call[3 : 3 + len(words)] == words)


def run(*args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = hub.main(list(args))
    return code, out.getvalue(), err.getvalue()


class HubTest(unittest.TestCase):
    """A data folder of its own, a fake Docker, and sites that all answer."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name).resolve()
        self.data = self.tmp / "data"
        self.hub = self.data / "docs-site" / "hub"
        self.docker = FakeDocker()
        self.down = set()
        patches = [
            mock.patch.dict(os.environ, {"XDG_DATA_HOME": str(self.data)}),
            mock.patch.object(hub, "docker", self.docker),
            mock.patch.object(
                hub, "answers", lambda port, host: None if host in self.down else 200
            ),
            mock.patch.object(hub, "ipv6_loopback", lambda: True),
            mock.patch.object(hub.time, "sleep", lambda seconds: None),
            mock.patch.object(
                hub.time, "monotonic", mock.Mock(side_effect=range(10**6))
            ),
            mock.patch.object(hub.os, "getuid", lambda: 1000),
            mock.patch.object(hub.os, "getgid", lambda: 1000),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)
        self.ports = {}

    def repo(self, path, port, config="site_name: x\n", index="# x\n\nAbout x.\n"):
        root = self.tmp / path
        (root / "docs").mkdir(parents=True)
        if config is not None:
            (root / "mkdocs.yml").write_text(config)
        (root / "docs" / "index.md").write_text(index)
        self.ports[str(root)] = port
        record = self.data / "docs-site" / "ports.json"
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text(json.dumps(self.ports))
        return root

    def read(self, name):
        return (self.hub / name).read_text()


class SitesTest(HubTest):
    def test_names_are_dns_labels(self):
        for folder, name in [
            ("astro-plugins", "astro-plugins"),
            ("My Project_2", "my-project-2"),
            ("--x--", "x"),
            ("...", "site"),
        ]:
            with self.subTest(folder):
                self.assertEqual(hub.slug(folder), name)

    def test_repos_come_in_the_order_they_were_recorded_and_share_no_name(self):
        self.repo("b/docs-app", 8101)
        self.repo("a/docs-app", 8100)
        self.repo("c/Docs App", 8102)
        found = hub.sites()
        self.assertEqual(
            [s.name for s in found], ["docs-app", "docs-app-2", "docs-app-3"]
        )
        self.assertEqual(found[0].root, self.tmp / "a/docs-app")
        self.assertEqual(found[1].service, "site-docs-app-2")

    def test_a_site_reads_its_summary_and_repo_from_the_repo(self):
        self.repo(
            "app",
            8100,
            'site_name: "App"\nrepo_url: https://github.com/me/app  # the repo\ndocs_dir: handbook\n',
        )
        (self.tmp / "app" / "handbook").mkdir()
        (self.tmp / "app" / "handbook" / "index.md").write_text(
            "# App\n\nTools for **my** [project](https://x.example), in `Go`. More text here.\n"
        )
        (site,) = hub.sites()
        self.assertEqual(site.repo_url, "https://github.com/me/app")
        self.assertEqual(site.description, "Tools for my project, in Go.")

    def test_a_repo_url_that_is_no_web_address_is_left_out(self):
        self.repo("app", 8100, "repo_url: javascript:alert(1)\n")
        self.assertEqual(hub.sites()[0].repo_url, "")

    def test_a_repo_on_a_branch_with_no_config_is_still_a_site(self):
        root = self.repo("app", 8100, config=None)
        (root / ".git").mkdir()
        (root / "docs" / "index.md").unlink()
        (site,) = hub.sites()
        self.assertEqual((site.name, site.description, site.repo_url), ("app", "", ""))

    def test_an_empty_folder_left_where_a_repo_was_is_no_site(self):
        self.repo("app", 8100)
        left = self.tmp / "deleted"
        left.mkdir()
        self.ports[str(left)] = 8101
        self.repo("other", 8102)
        self.assertEqual([s.name for s in hub.sites()], ["app", "other"])

    def test_a_repo_whose_folder_is_gone_is_no_site(self):
        self.repo("app", 8100)
        self.ports["/nowhere/gone"] = 8101
        self.repo("other", 8102)
        self.assertEqual([s.name for s in hub.sites()], ["app", "other"])

    def test_setting_reads_plain_quoted_and_toml_values(self):
        for text, value in [
            ("site_name: My project\n", "My project"),
            ('site_name: "Docs: \\"a\\" #1"\n', 'Docs: "a" #1'),
            ("site_name: 'x'  # note\n", "x"),
            ('[project]\nsite_name = "From toml"\n', "From toml"),
            ("other: 1\n", ""),
        ]:
            with self.subTest(text):
                self.assertEqual(hub.setting(text, "site_name"), value)


class TextTest(unittest.TestCase):
    def setUp(self):
        self.site = hub.Site(
            "app",
            Path("/home/me/app"),
            "Tools & <things>.",
            "https://github.com/me/app",
        )

    def test_the_compose_file(self):
        self.assertEqual(
            hub.compose_text([self.site], 8099, Path("/data/hub"), "1000:1000", True),
            f"""# {hub.NOTE}
name: docs-site
services:
  proxy:
    image: caddy:2-alpine
    ports:
      - "127.0.0.1:8099:8099"
      - "[::1]:8099:8099"
    volumes:
      - type: bind
        source: "/data/hub/caddy"
        target: "/etc/caddy"
        read_only: true
        bind:
          create_host_path: false
      - type: bind
        source: "/data/hub/www"
        target: "/srv/hub"
        read_only: true
        bind:
          create_host_path: false
    restart: unless-stopped
  site-app:
    image: zensical/zensical:latest
    user: "1000:1000"
    command: ["serve", "-a", "0.0.0.0:8000"]
    working_dir: "/home/me/app"
    volumes:
      - type: bind
        source: "/home/me/app"
        target: "/home/me/app"
        bind:
          create_host_path: false
    restart: unless-stopped
""",
        )

    def test_the_sites_publish_no_host_ports(self):
        text = hub.compose_text([self.site], 8099, Path("/h"), "1:1", False)
        self.assertEqual(text.count("ports:"), 1)
        self.assertNotIn("[::1]", text)

    def test_no_mount_lets_docker_make_a_missing_folder(self):
        # Docker would make it as root, where a deleted repo was.
        text = hub.compose_text([self.site], 8099, Path("/h"), "1:1", False)
        self.assertEqual(text.count("type: bind"), 3)
        self.assertEqual(text.count("create_host_path: false"), 3)

    def test_a_dollar_in_a_path_is_not_a_compose_variable(self):
        site = hub.Site("a", Path("/home/me/a$HOME"), "", "")
        self.assertIn(
            'source: "/home/me/a$$HOME"',
            hub.compose_text([site], 8099, Path("/h"), "1:1", False),
        )

    def test_the_proxy_routes(self):
        self.assertEqual(
            hub.caddy_text([self.site], 8099),
            f"""# {hub.NOTE}
{{
	auto_https off
}}
http://localhost:8099, http://127.0.0.1:8099, http://[::1]:8099 {{
	root * /srv/hub
	file_server
}}
http://app.localhost:8099 {{
	reverse_proxy site-app:8000 {{
		# Zensical's server answers 400 unless Host and Origin are localhost.
		header_up Host localhost:8000
		header_up Origin http://localhost:8000
	}}
	handle_errors {{
		respond "The docs site for app is not running. See: docker compose -p docs-site logs site-app" 502
	}}
}}
http://*.localhost:8099 {{
	respond "No docs site has that name. The dashboard at http://localhost:8099 lists them." 404
}}
""",
        )

    def test_the_dashboard_lists_each_site_by_its_address(self):
        page = hub.page_text([self.site], 8099)
        self.assertIn(
            '<a class="address" href="http://app.localhost:8099/">'
            '<span class="name">app</span><span class="rest">.localhost:8099</span></a>',
            page,
        )
        self.assertIn('<p class="about">Tools &amp; &lt;things&gt;.</p>', page)
        self.assertIn(
            '<p class="repo"><a href="https://github.com/me/app">Repository on GitHub</a></p>',
            page,
        )
        self.assertIn('<p class="count">1 project</p>', page)
        self.assertNotIn("http://fonts.", page)
        self.assertNotIn("<script", page)

    def test_a_site_with_nothing_to_say_has_only_its_address(self):
        page = hub.page_text([hub.Site("a", Path("/a"), "", ""), self.site], 8099)
        self.assertEqual(page.count('class="about"'), 1)
        self.assertEqual(page.count('class="repo"'), 1)
        self.assertIn('<p class="count">2 projects</p>', page)

    def test_a_repo_elsewhere_is_not_called_github(self):
        site = hub.Site("a", Path("/a"), "", "https://gitlab.com/me/a")
        self.assertIn(">Repository</a>", hub.page_text([site], 8099))

    def test_with_no_sites_the_dashboard_says_how_to_add_one(self):
        page = hub.page_text([], 8099)
        self.assertIn(
            "No projects yet. Run <code>/docs-site:init</code> in a repo", page
        )
        self.assertNotIn('<ul class="sites">', page)


class InstallTest(HubTest):
    def test_it_writes_the_files_starts_the_hub_and_says_where_things_are(self):
        self.repo("app", 8100)
        code, out, err = run("install")
        self.assertEqual(code, 0, err)
        self.assertEqual(
            out.splitlines(),
            [
                f"{self.hub}:",
                "  created compose.yml",
                "  created caddy/Caddyfile",
                "  created www/index.html",
                "  dashboard: http://localhost:8099",
                "  app: http://app.localhost:8099",
            ],
        )
        self.assertIn("  site-app:", self.read("compose.yml"))
        self.assertIn("http://app.localhost:8099 {", self.read("caddy/Caddyfile"))
        self.assertIn("app.localhost:8099/", self.read("www/index.html"))
        self.assertEqual(
            self.docker.calls[-1],
            (
                "compose",
                "-f",
                str(self.hub / "compose.yml"),
                "up",
                "-d",
                "--remove-orphans",
            ),
        )
        self.assertEqual(self.docker.ran("exec"), 0)

    def test_a_second_run_keeps_the_files_and_reloads_nothing(self):
        self.repo("app", 8100)
        run("install")
        before = {name: self.read(name) for name in hub.FILES}
        _, out, _ = run("install")
        self.assertEqual({name: self.read(name) for name in hub.FILES}, before)
        self.assertEqual(
            out.splitlines()[1:4],
            ["  kept compose.yml", "  kept caddy/Caddyfile", "  kept www/index.html"],
        )
        self.assertEqual(self.docker.ran("up"), 2)
        self.assertEqual(self.docker.ran("exec"), 0)

    def test_a_new_repo_is_added_and_the_running_proxy_reads_its_route(self):
        self.repo("app", 8100)
        run("install")
        self.repo("other", 8101)
        _, out, _ = run("install")
        self.assertIn("  reloaded the proxy's routes", out.splitlines())
        self.assertIn("  other: http://other.localhost:8099", out.splitlines())
        self.assertIn("  site-other:", self.read("compose.yml"))
        self.assertEqual(
            self.docker.calls[-1][3:],
            (
                "exec",
                "-T",
                "proxy",
                "caddy",
                "reload",
                "--config",
                "/etc/caddy/Caddyfile",
            ),
        )

    def test_the_reload_is_tried_again_while_the_proxy_gets_ready(self):
        self.repo("app", 8100)
        run("install")
        self.repo("other", 8101)
        self.docker.reload_failures = 3
        code, _, err = run("install")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.docker.ran("exec"), 4)

    def test_a_reload_that_keeps_failing_fails_the_run(self):
        self.repo("app", 8100)
        run("install")
        self.repo("other", 8101)
        self.docker.reload_failures = 99
        code, _, err = run("install")
        self.assertEqual(code, 1)
        self.assertIn("hub.py: caddy isn't ready", err)

    def test_a_port_given_once_is_kept_on_later_runs(self):
        self.repo("app", 8100)
        run("install", "--port", "9000")
        _, out, _ = run("install")
        self.assertIn("  dashboard: http://localhost:9000", out.splitlines())
        self.assertIn('"127.0.0.1:9000:9000"', self.read("compose.yml"))

    def test_a_site_that_does_not_answer_is_named_with_where_to_look(self):
        self.repo("app", 8100)
        self.repo("other", 8101)
        self.down = {"other.localhost"}
        code, out, _ = run("install")
        self.assertEqual(code, 0)
        self.assertIn(
            "  other: http://other.localhost:8099 (not answering yet: "
            "docker compose -p docs-site logs site-other)",
            out.splitlines(),
        )
        self.assertIn("  app: http://app.localhost:8099", out.splitlines())

    def test_with_no_repos_it_still_serves_the_dashboard(self):
        code, out, _ = run("install")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[-1], "  dashboard: http://localhost:8099")
        self.assertIn("No projects yet.", self.read("www/index.html"))

    def test_without_docker_it_says_what_it_needs_and_writes_nothing(self):
        self.repo("app", 8100)
        with (
            mock.patch.object(hub, "docker", REAL_DOCKER),
            mock.patch.object(hub.subprocess, "run", side_effect=FileNotFoundError),
        ):
            code, _, err = run("install")
        self.assertEqual(code, 1)
        self.assertIn("the hub needs Docker with its compose plugin", err)
        self.assertFalse(self.hub.exists())


class DockerTest(unittest.TestCase):
    def test_a_failed_command_gives_dockers_last_lines(self):
        done = subprocess.CompletedProcess(
            [], 1, stdout="", stderr="a\nb\nc\nd\nport is already allocated\n"
        )
        with (
            mock.patch.object(hub.subprocess, "run", return_value=done),
            self.assertRaises(hub.Fail) as failed,
        ):
            hub.docker("compose", "up")
        self.assertEqual(str(failed.exception), "b\nc\nd\nport is already allocated")

    def test_a_failure_can_be_let_through(self):
        done = subprocess.CompletedProcess([], 1, stdout="", stderr="no such service")
        with mock.patch.object(hub.subprocess, "run", return_value=done):
            self.assertEqual(hub.docker("compose", "ps", check=False), "")


class UpdateTest(HubTest):
    def test_with_no_hub_it_does_nothing(self):
        self.repo("app", 8100)
        code, out, err = run("update", "--repo", str(self.tmp / "app"))
        self.assertEqual((code, out, err), (0, "", ""))
        self.assertEqual(self.docker.calls, [])
        self.assertFalse(self.hub.exists())

    def test_with_a_hub_it_adds_the_repo_and_says_where_its_site_is(self):
        self.repo("app", 8100)
        run("install")
        other = self.repo("other", 8101)
        code, out, _ = run("update", "--repo", str(other))
        self.assertEqual(code, 0)
        self.assertEqual(out, "the hub serves it at http://other.localhost:8099\n")
        self.assertIn("  site-other:", self.read("compose.yml"))

    def test_without_a_repo_it_lists_every_site(self):
        self.repo("app", 8100)
        self.repo("other", 8101)
        run("install")
        _, out, _ = run("update")
        self.assertEqual(
            out.splitlines(),
            ["app: http://app.localhost:8099", "other: http://other.localhost:8099"],
        )


class StatusTest(HubTest):
    def test_with_no_hub_it_says_how_to_get_one(self):
        code, _, err = run("status")
        self.assertEqual(code, 1)
        self.assertEqual(
            err, "hub.py: the hub isn't installed: hub.py install sets it up\n"
        )

    def test_it_says_whether_each_container_runs_and_each_site_answers(self):
        self.repo("app", 8100)
        self.repo("other", 8101)
        run("install")
        self.docker.states = {
            "proxy": "running",
            "site-app": "running",
            "site-other": "restarting",
        }
        self.down = {"other.localhost"}
        code, out, _ = run("status")
        self.assertEqual(code, 1)
        self.assertEqual(
            out.splitlines(),
            [
                f"{self.hub}:",
                "  dashboard: http://localhost:8099  container running, answering",
                "  app: http://app.localhost:8099  container running, answering",
                "  other: http://other.localhost:8099  container restarting, not answering (no reply)",
            ],
        )

    def test_when_everything_answers_it_exits_0(self):
        self.repo("app", 8100)
        run("install")
        self.docker.states = {"proxy": "running", "site-app": "running"}
        self.assertEqual(run("status")[0], 0)


class RemoveTest(HubTest):
    def test_it_takes_the_containers_down_and_removes_the_folder(self):
        self.repo("app", 8100)
        run("install")
        code, out, _ = run("remove")
        self.assertEqual(code, 0)
        self.assertEqual(
            self.docker.calls[-1][3:], ("down", "--volumes", "--remove-orphans")
        )
        self.assertFalse(self.hub.exists())
        self.assertTrue((self.data / "docs-site" / "ports.json").is_file())
        self.assertIn("  stopped and removed the hub's containers", out.splitlines())

    def test_with_no_hub_it_says_so(self):
        code, out, _ = run("remove")
        self.assertEqual(code, 0)
        self.assertIn("  there's no hub to remove", out.splitlines())
        self.assertEqual(self.docker.calls, [])


if __name__ == "__main__":
    unittest.main()
