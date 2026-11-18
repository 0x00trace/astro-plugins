import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))
import board
import migrate

URL = "https://github.com/me/game"


class FakeGitHub:
    """The GitHub calls migrate.py makes, kept in memory, with every change logged."""

    def __init__(self, linked=True):
        self.repo, self.owner, self.name, self.project = "me/game", "me", "game", None
        self.calls = []
        self.issue_list = []  # {number, id, state, body, title, labels, milestone, parent, blocked_by}
        self.prs = []
        self.milestone_list = []
        self.label_set = {"bug"}
        self.project_list = []
        self.board_items = {}  # issue number -> status
        self.closed_items = []  # {number, state, status}, on the board already
        self.views = {v["name"] for v in board.VIEWS}
        self.workflows_off = []
        self.latest_update = None
        self.linked = linked
        self.next_number = 100

    def log(self, *call):
        self.calls.append(call)

    # reads
    def issues(self):
        return [
            {k: i[k] for k in ("number", "id", "state", "body", "parent", "blocked_by")}
            for i in self.issue_list
        ]

    def merged_prs(self):
        return list(self.prs)

    def milestones(self):
        return [dict(m) for m in self.milestone_list]

    def labels(self):
        return {x.casefold() for x in self.label_set}

    def board(self):
        if not self.linked:
            return None
        return {
            "id": "PB",
            "number": 7,
            "title": "game",
            "field": {
                "id": "F",
                "options": [
                    {"id": s, "name": s} for s in ("Todo", "In Progress", "Done")
                ],
            },
        }

    def board_state(self, b):
        return {
            "views": set(self.views),
            "workflows_off": list(self.workflows_off),
            "items": [
                {"number": n, "state": "OPEN", "status": st}
                for n, st in self.board_items.items()
            ]
            + list(self.closed_items),
            "latest_update": self.latest_update,
        }

    def projects(self):
        return list(self.project_list)

    # writes
    def link_project(self, number):
        self.log("link_project", number)
        self.linked = True

    def create_project(self, title):
        self.log("create_project", title)
        self.linked = True
        return 9

    def add_views(self):
        self.log("add_views")
        self.views = {v["name"] for v in board.VIEWS}
        return []

    def create_milestone(self, title, description):
        self.log("create_milestone", title, description)
        number = len(self.milestone_list) + 1
        self.milestone_list.append(
            {
                "number": number,
                "title": title,
                "state": "open",
                "open_issues": 0,
                "closed_issues": 0,
            }
        )
        return number

    def set_milestone_state(self, number, state):
        self.log("set_milestone_state", number, state)

    def create_label(self, name):
        self.log("create_label", name)
        self.label_set.add(name)

    def create_issue(self, title, body, labels, milestone):
        self.next_number += 1
        n = self.next_number
        self.log("create_issue", n, title)
        self.issue_list.append(
            {
                "number": n,
                "id": f"I{n}",
                "state": "OPEN",
                "body": body,
                "title": title,
                "labels": labels,
                "milestone": milestone,
                "parent": None,
                "blocked_by": set(),
            }
        )
        return n, f"I{n}"

    def issue(self, number):
        return next(i for i in self.issue_list if i["number"] == number)

    def by_node(self, node):
        return next(i for i in self.issue_list if i["id"] == node)

    def edit_body(self, number, body):
        self.log("edit_body", number)
        self.issue(number)["body"] = body

    def add_to_board(self, b, node, status):
        self.log("add_to_board", node, status)
        self.board_items[self.by_node(node)["number"]] = status

    def add_sub_issue(self, parent, child):
        self.log("add_sub_issue", parent, child)
        self.by_node(child)["parent"] = self.by_node(parent)["number"]

    def add_blocked_by(self, issue, blocker):
        self.log("add_blocked_by", issue, blocker)
        self.by_node(issue)["blocked_by"].add(self.by_node(blocker)["number"])

    def move(self, number, status):
        self.log("move", number, status)

    def writes(self):
        return [c for c in self.calls]


def item(id, type="task", status="todo", body="", **fields):
    lines = [
        "---",
        f"id: {id}",
        f"type: {type}",
        f"title: {fields.pop('title', 'Do ' + id)}",
        f"status: {status}",
        "priority: medium",
        "owner: claude",
        "created: 2026-11-15",
    ]
    lines += [f"{k}: {v}" for k, v in fields.items()]
    return "\n".join(lines) + "\n---\n" + body


class RepoTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve() / "game"
        self.root.mkdir()
        self.git("init", "-q")
        self.gh = FakeGitHub()

    def git(self, *args):
        subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
            cwd=self.root,
            check=True,
            capture_output=True,
        )

    def write(self, files):
        for path, text in files.items():
            f = self.root / path
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "files", "--allow-empty")

    def run_migrate(self, command, *args):
        out, err = io.StringIO(), io.StringIO()
        with (
            contextlib.chdir(self.root),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            code = migrate.main([command, *args], github=self.gh)
        return code, out.getvalue(), err.getvalue()

    def read(self, path):
        return (self.root / path).read_text()

    def tree(self):
        return sorted(
            p.relative_to(self.root).as_posix()
            for p in self.root.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(self.root).parts
        )


class CorkboardRepo(RepoTest):
    """A repo like project-spaceport: open and done items, a release, docs and an ignore line."""

    def setUp(self):
        super().setUp()
        self.gh.prs = [{"number": 12, "title": "feat: drag cards (EX-2)"}]
        self.write(
            {
                ".project/config.yml": "name: Game\nprefix: EX\n",
                ".project/releases/alpha.md": "---\nname: alpha\nstatus: planned\n---\n"
                "Players log in. Design: [0001](../docs/decisions/0001-logins.md).\n",
                ".project/items/EX-1-accounts.md": item(
                    "EX-1", "epic", "in-progress", "Accounts.\n", release="alpha"
                ),
                ".project/items/EX-2-drag.md": item(
                    "EX-2", status="done", body="Done work.\n"
                ),
                ".project/items/EX-3-login.md": item(
                    "EX-3",
                    status="in-progress",
                    title='"Log in: with a screen"',
                    parent="EX-1",
                    labels="[ui, accounts]",
                    blocked_by="[EX-2, EX-4]",
                    body="Builds on EX-2 and EX-4. See [the spec](../docs/accounts.md).\n\n"
                    "```\nEX-4 in code stays\n```\n\n## Subtasks\n- [ ] Screen\n- [x] Server\n\n"
                    "## Log\n- 2026-11-15 17:50 claude: created\n",
                ),
                ".project/items/EX-4-server.md": item(
                    "EX-4", "bug", "todo", "The server drops.\n", parent="EX-1"
                ),
                ".project/items/EX-5-old.md": item("EX-5", status="cancelled"),
                ".project/docs/accounts.md": "# Accounts\n\nEX-3 adds the screen. See [CLI](cli.md), "
                "[the code](../../src/login.py) and [EX-1](../items/EX-1-accounts.md).\n",
                ".project/docs/decisions/0001-logins.md": "# Logins\n\nSee [accounts](../accounts.md).\n",
                ".project/docs/cli.md": "# CLI\n\n`EX-4` in code stays, EX-9 has no issue.\n",
                "PROJECT.md": "# Game\n\nSee [0001](.project/docs/decisions/0001-logins.md). "
                "EX-1 is in progress, EX-2 merged, and [EX-3](https://x.example/EX-3) is linked already.\n",
                "src/login.py": "print('EX-3')\n",
                ".prettierignore": "dist/\n# corkboard writes these files and owns their format\n.project/\n",
                "CLAUDE.md": "# Rules\n\nTrack work with corkboard.\n",
            }
        )


class ScanTest(CorkboardRepo):
    def test_scan_says_what_run_would_do_and_changes_nothing(self):
        before = {p: self.read(p) for p in self.tree()}
        code, out, err = self.run_migrate("scan")
        self.assertEqual(code, 0, err)
        self.assertEqual({p: self.read(p) for p in self.tree()}, before)
        self.assertEqual(self.gh.calls, [])
        self.assertIn(
            "corkboard in .project/: 5 items (3 open), 1 releases, 3 docs, IDs EX-N",
            out,
        )
        self.assertIn("1. make milestone alpha", out)
        self.assertIn("make labels accounts, ui", out)
        self.assertIn(
            "open 3 issues (1 epic, 1 task, 1 bug) on the board (2 In Progress, 1 Todo)",
            out,
        )
        self.assertIn("make 2 sub-issues and 1 blocked-by links", out)
        self.assertIn(
            "move .project/docs/ (3 files) to docs/ and fix the links to and from it",
            out,
        )
        self.assertIn(
            "remove .project/items, .project/releases, .project/config.yml", out
        )
        self.assertIn("remove the .project/ lines from .prettierignore", out)
        self.assertIn("CLAUDE.md:3 names corkboard: Track work with corkboard.", out)
        self.assertIn(
            "no open item or merged PR to link these IDs to, so they stay as text: EX-9",
            out,
        )


class RunTest(CorkboardRepo):
    def setUp(self):
        super().setUp()
        self.code, self.out, self.err = self.run_migrate("run")
        self.assertEqual(self.code, 0, self.err)
        self.issues = {i["title"]: i for i in self.gh.issue_list}

    def test_open_items_become_issues_and_done_ones_stay_in_history(self):
        self.assertEqual(
            sorted(self.issues), ["Do EX-1", "Do EX-4", "Log in: with a screen"]
        )

    def test_an_issue_keeps_the_items_text_its_labels_and_its_milestone(self):
        login = self.issues["Log in: with a screen"]
        self.assertEqual(login["labels"], ["ui", "accounts"])
        self.assertEqual(login["milestone"], 1)  # its epic's release
        body = login["body"]
        self.assertIn("## Subtasks\n- [ ] Screen\n- [x] Server", body)
        self.assertIn(
            "<details><summary>Corkboard log</summary>\n\n- 2026-11-15 17:50 claude: created",
            body,
        )
        self.assertTrue(
            body.endswith(
                "Moved from corkboard EX-3 · priority medium · created 2026-11-15\n<!-- corkboard: EX-3 -->"
            )
        )
        self.assertEqual(self.issues["Do EX-4"]["labels"], ["bug"])

    def test_ids_in_an_issue_link_to_issues_and_prs_but_not_inside_code(self):
        body = self.issues["Log in: with a screen"]["body"]
        server = self.issues["Do EX-4"]["number"]
        self.assertIn(
            f"Builds on [EX-2]({URL}/pull/12) and [EX-4]({URL}/issues/{server}).", body
        )
        self.assertIn("```\nEX-4 in code stays\n```", body)
        self.assertIn(f"[the spec]({URL}/blob/HEAD/docs/accounts.md)", body)

    def test_the_milestone_links_the_moved_docs(self):
        made = next(c for c in self.gh.calls if c[0] == "create_milestone")
        self.assertEqual(
            made[2],
            f"Players log in. Design: [0001]({URL}/blob/HEAD/docs/decisions/0001-logins.md).",
        )

    def test_statuses_parents_and_blockers(self):
        accounts, login, server = (
            self.issues[t] for t in ("Do EX-1", "Log in: with a screen", "Do EX-4")
        )
        self.assertEqual(self.gh.board_items[accounts["number"]], "In Progress")
        self.assertEqual(self.gh.board_items[login["number"]], "In Progress")
        self.assertEqual(self.gh.board_items[server["number"]], "Todo")
        self.assertEqual(login["parent"], accounts["number"])
        self.assertEqual(server["parent"], accounts["number"])
        # EX-2 is done, so only the open blocker becomes a link.
        self.assertEqual(login["blocked_by"], {server["number"]})

    def test_docs_move_with_their_links_fixed(self):
        self.assertFalse((self.root / ".project").exists())
        accounts = self.issues["Do EX-1"]["number"]
        login = self.issues["Log in: with a screen"]["number"]
        self.assertEqual(
            self.read("docs/accounts.md"),
            f"# Accounts\n\n[EX-3]({URL}/issues/{login}) adds the screen. See [CLI](cli.md), "
            f"[the code](../src/login.py) and [EX-1]({URL}/issues/{accounts}).\n",
        )
        self.assertEqual(
            self.read("docs/decisions/0001-logins.md"),
            "# Logins\n\nSee [accounts](../accounts.md).\n",
        )
        self.assertEqual(
            self.read("docs/cli.md"),
            "# CLI\n\n`EX-4` in code stays, EX-9 has no issue.\n",
        )

    def test_project_md_links_the_moved_docs_and_the_ids(self):
        accounts = self.issues["Do EX-1"]["number"]
        self.assertEqual(
            self.read("PROJECT.md"),
            f"# Game\n\nSee [0001](docs/decisions/0001-logins.md). [EX-1]({URL}/issues/{accounts}) is in "
            f"progress, [EX-2]({URL}/pull/12) merged, and [EX-3](https://x.example/EX-3) is linked already.\n",
        )
        self.assertEqual(self.read("src/login.py"), "print('EX-3')\n")

    def test_the_move_is_a_git_rename_and_the_rest_of_project_is_removed(self):
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        self.assertIn(
            "R  .project/docs/decisions/0001-logins.md -> docs/decisions/0001-logins.md",
            status,
        )
        self.assertIn("D  .project/items/EX-1-accounts.md", status)
        self.assertIn("D  .project/config.yml", status)

    def test_the_ignore_line_and_its_corkboard_comment_go(self):
        self.assertEqual(self.read(".prettierignore"), "dist/\n")

    def test_a_second_run_changes_nothing(self):
        calls = len(self.gh.calls)
        before = {p: self.read(p) for p in self.tree()}
        code, _out, err = self.run_migrate("run")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.gh.calls[calls:], [])
        self.assertEqual({p: self.read(p) for p in self.tree()}, before)


class RerunTest(CorkboardRepo):
    def test_a_run_cut_short_finishes_what_is_missing_and_opens_no_duplicates(self):
        self.run_migrate("run")
        login = next(
            i for i in self.gh.issue_list if i["title"] == "Log in: with a screen"
        )
        login["parent"] = None
        login["body"] = "Edited by hand.\n<!-- corkboard: EX-3 -->"
        self.git(
            "reset", "-q", "--hard"
        )  # the files as they were, as if run stopped before them
        self.gh.calls.clear()
        code, _out, err = self.run_migrate("run")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(self.gh.issue_list), 3)
        made = [c[0] for c in self.gh.calls]
        self.assertNotIn("create_issue", made)
        self.assertNotIn(
            "edit_body", made
        )  # an issue made before is the user's to edit
        self.assertEqual(made.count("add_sub_issue"), 1)
        self.assertEqual(login["body"], "Edited by hand.\n<!-- corkboard: EX-3 -->")
        self.assertFalse((self.root / ".project").exists())


class OffBoardTest(CorkboardRepo):
    def test_a_rerun_puts_an_issue_opened_before_on_the_board(self):
        self.run_migrate("run")
        accounts = next(i for i in self.gh.issue_list if i["title"] == "Do EX-1")
        del self.gh.board_items[
            accounts["number"]
        ]  # as if run stopped before putting it there
        self.git("reset", "-q", "--hard")
        self.gh.calls.clear()
        _, scan, _ = self.run_migrate("scan")
        self.assertIn(
            f"put 1 issues opened before on the board, if they aren't on it: #{accounts['number']}",
            scan,
        )
        self.run_migrate("run")
        self.assertEqual(self.gh.board_items[accounts["number"]], "In Progress")
        self.assertEqual([c[0] for c in self.gh.calls].count("add_to_board"), 1)


class BoardTest(RepoTest):
    def setUp(self):
        super().setUp()
        self.write({"README.md": "# Game\n"})

    def test_an_unlinked_project_with_the_repos_name_is_linked(self):
        self.gh.linked = False
        self.gh.project_list = [
            {"number": 3, "title": "Other", "closed": False, "items": 1},
            {"number": 23, "title": "GAME", "closed": False, "items": 62},
        ]
        code, _out, _ = self.run_migrate("run")
        self.assertEqual(code, 0)
        self.assertIn(("link_project", 23), self.gh.calls)
        self.assertIn(("add_views",), self.gh.calls)

    def test_with_no_project_to_link_it_makes_one(self):
        self.gh.linked = False
        self.run_migrate("run")
        self.assertIn(("create_project", "game"), self.gh.calls)

    def test_a_linked_board_gets_its_missing_views_and_closed_items_move_to_done(self):
        self.gh.views = {"Open work"}
        self.gh.closed_items = [
            {"number": 5, "state": "CLOSED", "status": "In Progress"},
            {"number": 6, "state": "CLOSED", "status": "Done"},
            {"number": 8, "state": "OPEN", "status": "Todo"},
        ]
        self.gh.workflows_off = ["Auto-add sub-issues"]
        self.gh.latest_update = "2026-11-13"
        self.gh.milestone_list = [
            {
                "number": 1,
                "title": "Factions",
                "state": "open",
                "open_issues": 0,
                "closed_issues": 4,
            },
            {
                "number": 2,
                "title": "Later",
                "state": "open",
                "open_issues": 2,
                "closed_issues": 1,
            },
            {
                "number": 3,
                "title": "Empty",
                "state": "open",
                "open_issues": 0,
                "closed_issues": 0,
            },
        ]
        _, scan, _ = self.run_migrate("scan")
        self.assertIn("add the board's missing views: Milestones, Recently done", scan)
        self.assertIn("move 1 closed issues and PRs to Done: #5", scan)
        self.assertIn("close milestone Factions, whose 4 issues are all closed", scan)
        self.assertIn("workflows that are off: Auto-add sub-issues", scan)
        self.assertIn("latest status update is from 2026-11-13", scan)
        self.run_migrate("run")
        self.assertEqual(
            self.gh.calls,
            [("add_views",), ("move", 5, "Done"), ("set_milestone_state", 1, "closed")],
        )

    def test_a_tidy_repo_has_nothing_to_migrate(self):
        code, out, _ = self.run_migrate("run")
        self.assertEqual(code, 0)
        self.assertIn("Nothing to migrate.", out)
        self.assertEqual(self.gh.calls, [])


class PrefixTest(RepoTest):
    def test_without_project_ids_link_to_the_prs_that_name_them(self):
        self.gh.prs = [
            {"number": 120, "title": "feat: review (AP-2)"},
            {"number": 127, "title": "feat: list (AP-28)"},
        ]
        self.write({"docs/notes/n.md": "# N\n\nAP-2, AP-28 and AP-30.\n"})
        _, scan, _ = self.run_migrate("scan", "--prefix", "AP")
        self.assertIn("link 2 item IDs in 1 files", scan)
        self.assertIn(
            "no open item or merged PR to link these IDs to, so they stay as text: AP-30",
            scan,
        )
        self.run_migrate("run", "--prefix", "AP")
        self.assertEqual(
            self.read("docs/notes/n.md"),
            f"# N\n\n[AP-2]({URL}/pull/120), [AP-28]({URL}/pull/127) and AP-30.\n",
        )


class DocsInTheWayTest(RepoTest):
    def test_with_files_in_docs_the_corkboard_docs_stay_put(self):
        self.write(
            {
                ".project/config.yml": "name: Game\nprefix: EX\n",
                ".project/docs/a.md": "# A\n",
                "docs/index.md": "# Home\n",
            }
        )
        _, scan, _ = self.run_migrate("scan")
        self.assertIn(
            "docs/ already has files, so .project/docs/ stays where it is", scan
        )
        self.run_migrate("run")
        self.assertEqual(self.read(".project/docs/a.md"), "# A\n")
        self.assertFalse((self.root / ".project/config.yml").exists())


class ParseTest(unittest.TestCase):
    def test_a_header_reads_quotes_escapes_and_lists(self):
        fields, body = migrate.header(
            '---\nid: EX-1\ntitle: "Fix: \\"drop\\" \\\\ now"\nlabels: ["a, b", ui]\nblocked_by: []\n---\nBody.\n',
            Path("x.md"),
        )
        self.assertEqual(fields["title"], 'Fix: "drop" \\ now')
        self.assertEqual(fields["labels"], ["a, b", "ui"])
        self.assertEqual(fields["blocked_by"], [])
        self.assertEqual(body, "Body.\n")

    def test_a_heading_inside_a_fence_doesnt_start_a_section(self):
        parts = migrate.sections(
            "Top.\n\n````\n## Log\n```\n````\n\n## Subtasks\n- [ ] One\n## Log\n- created\n"
        )
        self.assertEqual(parts[""], "Top.\n\n````\n## Log\n```\n````")
        self.assertEqual(parts["Subtasks"], "- [ ] One")
        self.assertEqual(parts["Log"], "- created")

    def test_link_ids_leaves_code_links_urls_and_longer_ids(self):
        text, count = migrate.link_ids(
            "EX-1, `EX-1`, [EX-1](u), http://x/EX-1, EX-12, EX-1a, #EX-1.\n",
            "EX",
            {"EX-1": "L", "EX-12": "M"},
        )
        self.assertEqual(
            text,
            "[EX-1](L), `EX-1`, [EX-1](u), http://x/EX-1, [EX-12](M), EX-1a, #EX-1.\n",
        )
        self.assertEqual(count, 2)

    def test_relink_moves_paths_inside_and_outside_the_docs(self):
        old = PurePosixPath(".project/docs/guides/a.md")
        new = PurePosixPath("docs/guides/a.md")
        text = "[b](../b.md) [c](../../../src/c.py#L2) [d](https://x/y) [e](#top)"
        self.assertEqual(
            migrate.relink(text, old, new, URL, {}, True),
            "[b](../b.md) [c](../../src/c.py#L2) [d](https://x/y) [e](#top)",
        )


if __name__ == "__main__":
    unittest.main()
