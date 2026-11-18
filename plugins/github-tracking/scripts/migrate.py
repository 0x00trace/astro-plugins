#!/usr/bin/env python3
"""Move a repo's work from corkboard to GitHub, and fix what older github-tracking boards left.

scan reads only and prints what run would do. run does it: corkboard's open items become issues
on the board linked to the repo, its releases milestones, epics parent issues with sub-issues, and
blocked_by GitHub's blocked-by links. Each issue carries a marker, so a second run creates nothing
twice. Item IDs in the repo's Markdown become links, .project/docs/ moves to docs/, and the rest of
.project/ goes. Done and cancelled items stay in git history. Stdlib only, for Python 3.11+.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

import board as gb
from board import Fail

OPEN = ("backlog", "todo", "in-progress", "waiting")
STATUS = {
    "in-progress": "In Progress",
    "waiting": "In Progress",
    "todo": "Todo",
    "backlog": "Todo",
}
MARKER = re.compile(r"<!-- corkboard: ([A-Z][A-Z0-9]*-\d+) -->")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
LIST_ITEM = re.compile(r'\s*("(?:[^"\\]|\\.)*"|[^,]+)\s*(?:,|$)')
LINK = re.compile(r'(\]\()([^)\s]+)((?:\s+"[^"]*")?\))')
IGNORE_LINES = {
    ".project",
    ".project/",
    "/.project",
    "/.project/",
    ".project/**",
    "/.project/**",
}
OLD_DOCS = PurePosixPath(".project/docs")
NEW_DOCS = PurePosixPath("docs")


# ---------------------------------------------------------------- corkboard's files


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return re.sub(r'\\(["\\])', r"\1", value[1:-1])
    return value


def header(text: str, path: Path) -> tuple[dict, str]:
    """A corkboard file's strict-YAML header and its body."""
    if not text.startswith("---\n"):
        raise Fail(f"{path} doesn't start with a --- header")
    end = text.find("\n---", 3)
    if end == -1:
        raise Fail(f"{path}'s header has no closing ---")
    fields = {}
    for line in text[4:end].splitlines():
        key, sep, value = line.partition(":")
        if not sep:
            raise Fail(f"{path}: can't read header line {line!r}")
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            fields[key.strip()] = [
                unquote(m) for m in LIST_ITEM.findall(value[1:-1]) if m.strip()
            ]
        else:
            fields[key.strip()] = unquote(value)
    return fields, text[end + 4 :].lstrip("\n")


def outside_fences(text: str):
    """Yield (line, in_code) for each line, following CommonMark fences."""
    fence = None
    for line in text.splitlines():
        m = FENCE.match(line)
        if fence:
            closes = (
                m
                and m.group(1)[0] == fence[0]
                and len(m.group(1)) >= len(fence)
                and not m.group(2).strip()
            )
            yield line, True
            if closes:
                fence = None
        elif m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
            fence = m.group(1)
            yield line, True
        else:
            yield line, False


def sections(body: str) -> dict[str, str]:
    """An item body's description, ## Subtasks and ## Log."""
    out, current = {"": [], "Subtasks": [], "Log": []}, ""
    for line, code in outside_fences(body):
        if not code and line.strip() in ("## Subtasks", "## Log"):
            current = line.strip()[3:]
            continue
        out[current].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


@dataclass
class Item:
    id: str
    type: str
    title: str
    status: str
    priority: str
    created: str
    path: str
    parent: str = ""
    release: str = ""
    labels: list = field(default_factory=list)
    blocked_by: list = field(default_factory=list)
    related: list = field(default_factory=list)
    duplicate_of: str = ""
    description: str = ""
    subtasks: str = ""
    log: str = ""

    @property
    def open(self) -> bool:
        return self.status in OPEN


@dataclass
class Corkboard:
    prefix: str
    name: str
    items: dict
    releases: dict
    docs: list

    def release_of(self, item: Item) -> str:
        parent = self.items.get(item.parent)
        return item.release or (parent.release if parent else "")


def load_corkboard(root: Path) -> Corkboard | None:
    base = root / ".project"
    if not (base / "config.yml").is_file() and not (base / "items").is_dir():
        return None
    config = {}
    if (base / "config.yml").is_file():
        for line in (base / "config.yml").read_text().splitlines():
            key, sep, value = line.partition(":")
            if sep:
                config[key.strip()] = unquote(value)
    items = {}
    for path in sorted((base / "items").glob("*.md")):
        fields, body = header(path.read_text(), path)
        parts = sections(body)
        known = {k: v for k, v in fields.items() if k in Item.__dataclass_fields__}
        item = Item(
            **known,
            path=path.relative_to(root).as_posix(),
            description=parts[""],
            subtasks=parts["Subtasks"],
            log=parts["Log"],
        )
        items[item.id] = item
    releases = {}
    for path in sorted((base / "releases").glob("*.md")):
        fields, body = header(path.read_text(), path)
        releases[fields.get("name", path.stem)] = (
            body.strip(),
            path.relative_to(root).as_posix(),
        )
    docs = (
        sorted(p for p in (base / "docs").rglob("*") if p.is_file())
        if (base / "docs").is_dir()
        else []
    )
    prefix = config.get("prefix") or (next(iter(items)).split("-")[0] if items else "")
    return Corkboard(prefix, config.get("name", root.name), items, releases, docs)


# ---------------------------------------------------------------- GitHub


class GitHub:
    """Every call the migration makes to GitHub, through the gh CLI."""

    def __init__(self, repo: str, project: int | None):
        self.repo, self.project = repo, project
        self.owner, self.name = repo.split("/")

    def paged(self, query: str, path: list[str]) -> list[dict]:
        nodes, after = [], None
        while True:
            data = gb.graphql(
                query,
                owner=self.owner,
                name=self.name,
                **({"after": after} if after else {}),
            )
            for key in path:
                data = data[key]
            nodes += data["nodes"]
            if not data["pageInfo"]["hasNextPage"]:
                return nodes
            after = data["pageInfo"]["endCursor"]

    def issues(self) -> list[dict]:
        found = self.paged(
            """query($owner:String!,$name:String!,$after:String){repository(owner:$owner,name:$name){
            issues(first:100,after:$after){pageInfo{hasNextPage endCursor}
            nodes{number id state body parent{number} blockedBy(first:50){nodes{number}}}}}}""",
            ["repository", "issues"],
        )
        return [
            {
                "number": i["number"],
                "id": i["id"],
                "state": i["state"],
                "body": i["body"],
                "parent": (i["parent"] or {}).get("number"),
                "blocked_by": {b["number"] for b in i["blockedBy"]["nodes"]},
            }
            for i in found
        ]

    def merged_prs(self) -> list[dict]:
        return self.paged(
            """query($owner:String!,$name:String!,$after:String){repository(owner:$owner,name:$name){
            pullRequests(first:100,after:$after,states:MERGED){pageInfo{hasNextPage endCursor}
            nodes{number title}}}}""",
            ["repository", "pullRequests"],
        )

    def milestones(self) -> list[dict]:
        return json.loads(
            gb.gh("api", f"repos/{self.repo}/milestones?state=all&per_page=100")
        )

    def labels(self) -> set[str]:
        found = json.loads(gb.gh("api", f"repos/{self.repo}/labels?per_page=100"))
        return {label["name"].casefold() for label in found}

    def board(self) -> dict | None:
        try:
            return gb.board(self.repo, self.project)
        except Fail as problem:
            if "no board is linked" in str(problem):
                return None
            raise

    def board_state(self, b: dict) -> dict:
        items, after, page = [], None, None
        while True:
            page = gb.graphql(
                gb.ITEMS, id=b["id"], **({"after": after} if after else {})
            )["node"]
            items += page["items"]["nodes"]
            if not page["items"]["pageInfo"]["hasNextPage"]:
                break
            after = page["items"]["pageInfo"]["endCursor"]
        updates = page["statusUpdates"]["nodes"]
        return {
            "views": {v["name"] for v in page["views"]["nodes"]},
            "workflows_off": [
                w["name"] for w in page["workflows"]["nodes"] if not w["enabled"]
            ],
            "items": [
                {
                    "number": (i["content"] or {}).get("number"),
                    "state": (i["content"] or {}).get("state"),
                    "status": (i["status"] or {}).get("name"),
                }
                for i in items
                if (i["content"] or {}).get("number")
            ],
            "latest_update": updates[0]["createdAt"][:10] if updates else None,
        }

    def projects(self) -> list[dict]:
        found = json.loads(
            gb.gh(
                "project",
                "list",
                "--owner",
                self.owner,
                "--format",
                "json",
                "--limit",
                "200",
            )
        )
        return [
            {
                "number": p["number"],
                "title": p["title"],
                "closed": p["closed"],
                "items": p["items"]["totalCount"],
            }
            for p in found["projects"]
        ]

    def link_project(self, number: int) -> None:
        gb.gh(
            "project", "link", str(number), "--owner", self.owner, "--repo", self.repo
        )

    def create_project(self, title: str) -> int:
        made = gb.gh(
            "project",
            "create",
            "--owner",
            self.owner,
            "--title",
            title,
            "--format",
            "json",
        )
        number = json.loads(made)["number"]
        self.link_project(number)
        return number

    def add_views(self) -> list[str]:
        return gb.views(self.repo, self.project)

    def post(self, path: str, payload: dict, method: str = "POST") -> dict:
        return json.loads(
            gb.gh(
                "api",
                "-X",
                method,
                f"repos/{self.repo}/{path}",
                "--input",
                "-",
                input=json.dumps(payload),
            )
        )

    def create_milestone(self, title: str, description: str) -> int:
        return self.post("milestones", {"title": title, "description": description})[
            "number"
        ]

    def set_milestone_state(self, number: int, state: str) -> None:
        self.post(f"milestones/{number}", {"state": state}, "PATCH")

    def create_label(self, name: str) -> None:
        self.post("labels", {"name": name, "color": "ededed"})

    def create_issue(
        self, title: str, body: str, labels: list[str], milestone: int | None
    ) -> tuple[int, str]:
        payload = {"title": title, "body": body, "labels": labels}
        if milestone:
            payload["milestone"] = milestone
        made = self.post("issues", payload)
        return made["number"], made["node_id"]

    def edit_body(self, number: int, body: str) -> None:
        self.post(f"issues/{number}", {"body": body}, "PATCH")

    def add_to_board(self, b: dict, node: str, status: str) -> None:
        option = next(
            (
                o
                for o in b["field"]["options"]
                if o["name"].casefold() == status.casefold()
            ),
            None,
        )
        if not option:
            raise Fail(f"the board {b['title']} has no status {status!r}")
        item = gb.graphql(
            "mutation($p:ID!,$c:ID!){addProjectV2ItemById(input:{projectId:$p,contentId:$c}){item{id}}}",
            p=b["id"],
            c=node,
        )["addProjectV2ItemById"]["item"]["id"]
        gb.graphql(
            """mutation($p:ID!,$i:ID!,$f:ID!,$o:String!){updateProjectV2ItemFieldValue(input:{projectId:$p,
            itemId:$i,fieldId:$f,value:{singleSelectOptionId:$o}}){projectV2Item{id}}}""",
            p=b["id"],
            i=item,
            f=b["field"]["id"],
            o=option["id"],
        )

    def add_sub_issue(self, parent: str, child: str) -> None:
        gb.graphql(
            "mutation($p:ID!,$c:ID!){addSubIssue(input:{issueId:$p,subIssueId:$c}){issue{id}}}",
            p=parent,
            c=child,
        )

    def add_blocked_by(self, issue: str, blocker: str) -> None:
        gb.graphql(
            "mutation($i:ID!,$b:ID!){addBlockedBy(input:{issueId:$i,blockingIssueId:$b}){issue{id}}}",
            i=issue,
            b=blocker,
        )

    def move(self, number: int, status: str) -> None:
        gb.move(self.repo, self.project, str(number), status)


# ---------------------------------------------------------------- text


def resolve(target: str, old_file: PurePosixPath) -> PurePosixPath | None:
    """A relative link's target as a path from the repo root, or None for a URL or anchor."""
    if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE) or target.startswith(
        ("#", "/")
    ):
        return None
    parts = []
    for part in (old_file.parent / target.split("#")[0]).parts:
        if part == "..":
            if not parts:
                return None
            parts.pop()
        elif part != ".":
            parts.append(part)
    return PurePosixPath(*parts) if parts else None


def moved(path: PurePosixPath, move: bool) -> PurePosixPath:
    if move and path.is_relative_to(OLD_DOCS):
        return NEW_DOCS / path.relative_to(OLD_DOCS)
    return path


def relink(
    text: str,
    old_file: PurePosixPath,
    new_file: PurePosixPath | None,
    url: str,
    links: dict,
    move: bool,
) -> str:
    """Point relative links at where their targets are once the docs have moved.

    new_file is where the text will live in the repo; None means on GitHub, where a relative link
    becomes a URL. A link to a corkboard item becomes a link to its issue or PR, when it has one.
    """

    def fix(m: re.Match) -> str:
        target = resolve(m.group(2), old_file)
        if target is None:
            return m.group(0)
        anchor = "#" + m.group(2).split("#", 1)[1] if "#" in m.group(2) else ""
        if target.parent == PurePosixPath(".project/items"):
            found = re.match(r"[A-Z][A-Z0-9]*-\d+", target.name)
            link = links.get(found.group(0)) if found else None
            return m.group(1) + link + m.group(3) if link else m.group(0)
        target = moved(target, move)
        if new_file is None:
            new = f"{url}/blob/HEAD/{target}"
        else:
            new = Path(os.path.relpath(target, new_file.parent)).as_posix()
        if new == m.group(2).split("#")[0]:
            return m.group(0)
        return m.group(1) + new + anchor + m.group(3)

    return LINK.sub(fix, text)


def link_ids(
    text: str, prefix: str, links: dict, missing: set | None = None
) -> tuple[str, int]:
    """Turn each bare item ID outside code, links and URLs into a link to its issue or PR.

    An ID with no link is left as it is, and added to missing.
    """
    if not prefix:
        return text, 0
    pattern = re.compile(
        rf"(\[[^\]]*\]\([^)]*\))|(https?://\S+)|((?<![\w/#-]){re.escape(prefix)}-\d+(?![\w-]))"
    )
    count = 0

    def fix(m: re.Match) -> str:
        nonlocal count
        if m.group(3) and m.group(3) in links:
            count += 1
            return f"[{m.group(3)}]({links[m.group(3)]})"
        if m.group(3) and missing is not None:
            missing.add(m.group(3))
        return m.group(0)

    out = []
    for line, code in outside_fences(text):
        if code:
            out.append(line)
            continue
        pieces = re.split(r"(`+[^`]*`+)", line)
        out.append(
            "".join(p if p.startswith("`") else pattern.sub(fix, p) for p in pieces)
        )
    return "\n".join(out) + ("\n" if text.endswith("\n") else ""), count


def issue_body(item: Item, prefix: str, links: dict, url: str, move: bool) -> str:
    parts = []
    if item.description:
        parts.append(item.description)
    if item.subtasks:
        parts.append("## Subtasks\n" + item.subtasks)
    if item.related:
        parts.append("Related: " + ", ".join(item.related))
    if item.duplicate_of:
        parts.append("Duplicate of " + item.duplicate_of)
    if item.log:
        parts.append(
            "<details><summary>Corkboard log</summary>\n\n"
            + item.log
            + "\n\n</details>"
        )
    text = relink("\n\n".join(parts), PurePosixPath(item.path), None, url, links, move)
    text, _ = link_ids(text, prefix, links)
    footer = f"Moved from corkboard {item.id} · priority {item.priority} · created {item.created}"
    return (text + "\n\n" if text else "") + footer + f"\n<!-- corkboard: {item.id} -->"


# ---------------------------------------------------------------- the plan


@dataclass
class Plan:
    root: Path
    gh: GitHub
    cork: Corkboard | None
    prefix: str = ""
    docs_move: bool = False
    actions: list = field(default_factory=list)  # (description, function)
    notes: list = field(default_factory=list)  # for the user to look at
    found: list = field(default_factory=list)  # what the scan saw
    board: dict | None = None
    milestones: dict = field(default_factory=dict)  # release name -> milestone number
    links: dict = field(default_factory=dict)  # item ID -> issue or PR URL
    planned: dict = field(default_factory=dict)  # links, with the issues run will open
    issues: dict = field(default_factory=dict)  # item ID -> issue
    on_board: set | None = None  # issue numbers on the board, when it's known

    def do(self, description: str, function) -> None:
        self.actions.append((description, function))

    @property
    def url(self) -> str:
        return f"https://github.com/{self.gh.repo}"


def git(root: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False
    )
    if done.returncode != 0:
        raise Fail(done.stderr.strip() or f"git {args[0]} failed")
    return done.stdout


def tracked(root: Path, *suffixes: str) -> list[PurePosixPath]:
    return [
        PurePosixPath(p)
        for p in git(root, "ls-files", "-z").split("\0")
        if p and (not suffixes or p.endswith(suffixes)) and (root / p).is_file()
    ]


def plan_board(p: Plan) -> None:
    gh = p.gh
    p.board = gh.board()
    if p.board:
        state = gh.board_state(p.board)
        p.on_board = {i["number"] for i in state["items"]}
        p.found.append(
            f"board {p.board['number']} ({p.board['title']}) is linked to {gh.repo}"
        )
        missing = [v["name"] for v in gb.VIEWS if v["name"] not in state["views"]]
        if missing:
            p.do(f"add the board's missing views: {', '.join(missing)}", gh.add_views)
        stale = [
            i
            for i in state["items"]
            if i["state"] in ("CLOSED", "MERGED") and i["status"] != "Done"
        ]
        if stale:
            numbers = ", ".join(f"#{i['number']}" for i in stale)

            def done():
                for i in stale:
                    gh.move(i["number"], "Done")

            p.do(f"move {len(stale)} closed issues and PRs to Done: {numbers}", done)
        if state["workflows_off"]:
            p.notes.append(
                "the board's workflows that are off: "
                + ", ".join(state["workflows_off"])
                + ". The API can't turn one on: switch them on in the board's Workflows settings"
            )
        if state["latest_update"]:
            p.notes.append(
                f"the board's latest status update is from {state['latest_update']}"
            )
        return
    names = {gh.name.casefold()} | ({p.cork.name.casefold()} if p.cork else set())
    candidates = [
        x for x in gh.projects() if not x["closed"] and x["title"].casefold() in names
    ]
    if candidates:
        pick = candidates[0]
        p.found.append(
            f"no board is linked to {gh.repo}, but project {pick['number']} "
            f"({pick['title']}, {pick['items']} items) has its name"
        )

        def link():
            gh.link_project(pick["number"])
            p.board = gh.board()

        p.do(f"link project {pick['number']} ({pick['title']}) to {gh.repo}", link)
    else:
        title = p.cork.name if p.cork else gh.name
        p.found.append(f"no board is linked to {gh.repo}")

        def create():
            gh.create_project(title)
            p.board = gh.board()

        p.do(f"make a board named {title} and link it to {gh.repo}", create)
    p.do(
        "give the board any of its views it lacks: "
        + ", ".join(v["name"] for v in gb.VIEWS),
        gh.add_views,
    )


def plan_milestones(p: Plan) -> None:
    gh, cork = p.gh, p.cork
    milestones = gh.milestones()
    by_title = {m["title"].casefold(): m for m in milestones}
    wanted = (
        sorted({cork.release_of(i) for i in cork.items.values() if i.open} - {""})
        if cork
        else []
    )
    for name in wanted:
        existing = by_title.get(name.casefold())
        if existing:
            p.milestones[name] = existing["number"]
            if existing["state"] == "closed":
                p.do(
                    f"reopen milestone {name}",
                    lambda n=existing["number"]: gh.set_milestone_state(n, "open"),
                )
            continue
        body, path = cork.releases.get(name, ("", ".project/releases/x.md"))
        text = relink(body, PurePosixPath(path), None, p.url, {}, p.docs_move)

        def make(name=name, text=text):
            p.milestones[name] = gh.create_milestone(name, text)

        p.do(f"make milestone {name}", make)
    wanted_titles = {w.casefold() for w in wanted}
    for m in milestones:
        if (
            m["state"] == "open"
            and m["open_issues"] == 0
            and m["closed_issues"] > 0
            and m["title"].casefold() not in wanted_titles
        ):
            p.do(
                f"close milestone {m['title']}, whose {m['closed_issues']} issues are all closed",
                lambda n=m["number"]: gh.set_milestone_state(n, "closed"),
            )


def pr_links(p: Plan, ids: set[str]) -> None:
    """Link each ID to the first merged PR whose title names it, unless it has a link already."""
    if not p.prefix:
        return
    for pr in sorted(p.gh.merged_prs(), key=lambda x: x["number"]):
        for item_id in re.findall(rf"\b{re.escape(p.prefix)}-\d+\b", pr["title"]):
            if item_id in ids and item_id not in p.links:
                p.links[item_id] = f"{p.url}/pull/{pr['number']}"


def plan_issues(p: Plan, issues: list[dict]) -> None:
    gh, cork = p.gh, p.cork
    marked = {}
    for issue in issues:
        found = MARKER.search(issue["body"] or "")
        if found:
            marked[found.group(1)] = issue
    p.issues = dict(marked)
    for item_id, issue in marked.items():
        p.links[item_id] = f"{p.url}/issues/{issue['number']}"
    pr_links(p, {i.id for i in cork.items.values() if not i.open})
    open_items = sorted(
        (i for i in cork.items.values() if i.open),
        key=lambda i: int(i.id.split("-")[1]),
    )
    todo = [i for i in open_items if i.id not in marked]
    if len(todo) < len(open_items):
        p.found.append(
            f"{len(open_items) - len(todo)} open items already have issues: "
            + ", ".join(
                f"{i.id} (#{marked[i.id]['number']})"
                for i in open_items
                if i.id in marked
            )
        )
    p.planned = {**p.links, **{i.id: f"{p.url}/issues/new" for i in todo}}

    have = gh.labels()
    wanted = sorted(
        {lb for i in todo for lb in i.labels + (["bug"] if i.type == "bug" else [])}
    )
    new_labels = [lb for lb in wanted if lb.casefold() not in have]
    if new_labels:

        def labels():
            for lb in new_labels:
                gh.create_label(lb)

        p.do(f"make labels {', '.join(new_labels)}", labels)
    if todo:
        kinds = [
            (t, sum(1 for i in todo if i.type == t)) for t in ("epic", "task", "bug")
        ]
        states = [
            (s, sum(1 for i in todo if STATUS[i.status] == s))
            for s in ("In Progress", "Todo")
        ]

        def create():
            for item in todo:
                labels = item.labels + (["bug"] if item.type == "bug" else [])
                milestone = p.milestones.get(cork.release_of(item))
                body = issue_body(item, cork.prefix, p.links, p.url, p.docs_move)
                number, node = gh.create_issue(item.title, body, labels, milestone)
                p.issues[item.id] = {
                    "number": number,
                    "id": node,
                    "parent": None,
                    "blocked_by": set(),
                    "body": body,
                    "new": True,
                }
                p.links[item.id] = f"{p.url}/issues/{number}"
                gh.add_to_board(p.board, node, STATUS[item.status])
                print(f"   #{number} {item.id} {item.title} ({STATUS[item.status]})")

        p.do(
            f"open {len(todo)} issues ("
            + ", ".join(f"{n} {k}{'s' if n != 1 else ''}" for k, n in kinds if n)
            + ") on the board ("
            + ", ".join(f"{n} {s}" for s, n in states if n)
            + ")",
            create,
        )

    subs = [
        i for i in open_items if i.parent in cork.items and cork.items[i.parent].open
    ]
    blocks = [
        (i, b)
        for i in open_items
        for b in i.blocked_by
        if b in cork.items and cork.items[b].open
    ]
    off_board = [
        i
        for i in open_items
        if i.id in marked and marked[i.id]["number"] not in (p.on_board or set())
    ]
    if off_board:

        def board_them():
            # Checked again now, as a board linked by this run may hold some already.
            have = {i["number"] for i in gh.board_state(p.board)["items"]}
            for item in off_board:
                if marked[item.id]["number"] not in have:
                    gh.add_to_board(p.board, marked[item.id]["id"], STATUS[item.status])

        p.do(
            f"put {len(off_board)} issues opened before on the board, if they aren't on it: "
            + ", ".join(f"#{marked[i.id]['number']}" for i in off_board),
            board_them,
        )
    new_subs = [i for i in subs if i.id not in marked or marked[i.id]["parent"] is None]
    new_blocks = [
        (i, b)
        for i, b in blocks
        if i.id not in marked
        or b not in marked
        or marked[b]["number"] not in marked[i.id]["blocked_by"]
    ]
    if new_subs or new_blocks:

        def relate():
            for item in new_subs:
                gh.add_sub_issue(p.issues[item.parent]["id"], p.issues[item.id]["id"])
            for item, blocker in new_blocks:
                gh.add_blocked_by(p.issues[item.id]["id"], p.issues[blocker]["id"])

        p.do(
            f"make {len(new_subs)} sub-issues and {len(new_blocks)} blocked-by links",
            relate,
        )
    if todo:

        def bodies():
            # Only the issues this run opened: a later edit on GitHub is the user's.
            for item in todo:
                issue = p.issues[item.id]
                body = issue_body(item, cork.prefix, p.links, p.url, p.docs_move)
                if body != issue["body"]:
                    gh.edit_body(issue["number"], body)

        p.do("link the item IDs in the new issues to their issues and PRs", bodies)


def file_edits(p: Plan, links: dict, missing: set | None = None) -> dict:
    """Each changed text file's new text and how many IDs it links, by its path after the move."""
    edits = {}
    for path in tracked(p.root, ".md", ".markdown"):
        if path.is_relative_to(".project/items") or path.is_relative_to(
            ".project/releases"
        ):
            continue
        old = (p.root / path).read_text()
        new_path = moved(path, p.docs_move)
        text = relink(old, path, new_path, p.url, links, p.docs_move)
        text, count = link_ids(text, p.prefix, links, missing)
        if text != old or new_path != path:
            edits[new_path] = (text, count)
    if p.docs_move:
        for name in ("mkdocs.yml", "mkdocs.yaml", "zensical.toml"):
            f = p.root / name
            if f.is_file() and ".project/docs" in f.read_text():
                edits[PurePosixPath(name)] = (
                    f.read_text().replace(".project/docs", "docs"),
                    0,
                )
    return edits


def plan_files(p: Plan) -> None:
    root, cork = p.root, p.cork
    missing = set()
    preview = file_edits(p, p.planned or p.links, missing)
    linked = {str(k): n for k, (_, n) in preview.items() if n}
    if missing:
        named = []
        for item_id in sorted(missing, key=lambda x: int(x.split("-")[1])):
            item = cork.items.get(item_id) if cork else None
            named.append(f"{item_id} ({item.status})" if item else item_id)
        p.notes.append(
            "no open item or merged PR to link these IDs to, so they stay as text: "
            + ", ".join(named)
        )
    said = []
    if p.docs_move:
        said.append(
            f"move .project/docs/ ({len(cork.docs)} files) to docs/ and fix the links to and from it"
        )
    if linked:
        said.append(
            f"link {sum(linked.values())} item IDs in {len(linked)} files to their issues and PRs: "
            + ", ".join(f"{k} ({n})" for k, n in sorted(linked.items()))
        )
    if not said and preview:
        said.append(f"fix links in {len(preview)} files")
    if said:

        def apply():
            # Worked out from the files as they are before the move, with every issue made.
            edits = file_edits(p, p.links)
            if p.docs_move:
                if (root / "docs").is_dir():
                    (root / "docs").rmdir()
                git(root, "mv", str(OLD_DOCS), str(NEW_DOCS))
            for path, (text, _) in edits.items():
                (root / path).write_text(text)

        p.do("; ".join(said), apply)
    if cork:
        gone = [
            x
            for x in (".project/items", ".project/releases", ".project/config.yml")
            if (root / x).exists()
        ]
        if gone:
            p.do(
                "remove " + ", ".join(gone) + " (git history keeps them)",
                lambda: git(root, "rm", "-r", "-q", *gone),
            )


def write_file(path: Path, text: str):
    return lambda: path.write_text(text)


def plan_ignores(p: Plan) -> None:
    for path in tracked(p.root):
        if not re.fullmatch(r"\.[a-z]*ignore", path.name):
            continue
        lines = (p.root / path).read_text().splitlines(keepends=True)
        keep, dropped = [], False
        for line in lines:
            if line.strip() in IGNORE_LINES:
                dropped = True
                if (
                    keep
                    and keep[-1].lstrip().startswith("#")
                    and "corkboard" in keep[-1].casefold()
                ):
                    keep.pop()
                continue
            keep.append(line)
        if dropped:
            p.do(
                f"remove the .project/ lines from {path}",
                write_file(p.root / path, "".join(keep)),
            )


def plan_mentions(p: Plan) -> None:
    ignored = {".gitignore", ".prettierignore"}
    for path in tracked(p.root, ".md", ".markdown", ".json", ".yml", ".yaml", ".toml"):
        if path.is_relative_to(".project") or path.name in ignored:
            continue
        text = (p.root / path).read_text(errors="replace")
        for number, line in enumerate(text.splitlines(), 1):
            if "corkboard" in line.casefold():
                p.notes.append(f"{path}:{number} names corkboard: {line.strip()[:160]}")


def make_plan(root: Path, gh: GitHub, prefix: str | None = None) -> Plan:
    p = Plan(root, gh, load_corkboard(root))
    p.prefix = p.cork.prefix if p.cork else (prefix or "")
    issues = gh.issues()
    if p.cork:
        n_open = sum(1 for i in p.cork.items.values() if i.open)
        p.found.append(
            f"corkboard in .project/: {len(p.cork.items)} items ({n_open} open), "
            f"{len(p.cork.releases)} releases, {len(p.cork.docs)} docs, IDs {p.cork.prefix}-N"
        )
        if p.cork.docs:
            if (root / "docs").exists() and any((root / "docs").iterdir()):
                p.notes.append(
                    "docs/ already has files, so .project/docs/ stays where it is: move its pages by hand"
                )
            else:
                p.docs_move = True
    plan_board(p)
    plan_milestones(p)
    if p.cork:
        plan_issues(p, issues)
    elif p.prefix:
        ids = set()
        for path in tracked(root, ".md", ".markdown"):
            ids |= set(
                re.findall(rf"\b{re.escape(p.prefix)}-\d+\b", (root / path).read_text())
            )
        pr_links(p, ids)
    if p.cork or p.prefix:
        plan_files(p)
    plan_ignores(p)
    plan_mentions(p)
    return p


def report(p: Plan) -> str:
    lines = [f"{p.root} ({p.gh.repo})", "Found:"] + [f"  {x}" for x in p.found]
    if p.actions:
        lines.append("run would:")
        lines += [f"  {n}. {d}" for n, (d, _) in enumerate(p.actions, 1)]
    else:
        lines.append("Nothing to migrate.")
    if p.notes:
        lines.append("For you to look at:")
        lines += [f"  - {x}" for x in p.notes]
    return "\n".join(lines)


def repo_root(cwd: Path) -> Path:
    top = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if top.returncode != 0:
        raise Fail("not in a git repo")
    return Path(top.stdout.strip())


def main(argv: list[str] | None = None, github=None) -> int:
    parser = argparse.ArgumentParser(
        description="Move a repo's work from corkboard to GitHub, and fix older board setups."
    )
    parser.add_argument(
        "command",
        choices=("scan", "run"),
        help="scan reads only; run makes the changes",
    )
    parser.add_argument(
        "--project", type=int, help="the board's number, when the repo has several"
    )
    parser.add_argument(
        "--prefix",
        help="the item ID prefix, such as AP, to link IDs to PRs in a repo whose .project/ is gone",
    )
    args = parser.parse_args(argv)
    try:
        root = repo_root(Path.cwd())
        os.chdir(root)
        gh = github or GitHub(gb.this_repo(), args.project)
        p = make_plan(root, gh, args.prefix)
        if args.command == "scan":
            print(report(p))
            return 0
        for n, (description, function) in enumerate(p.actions, 1):
            print(f"{n}. {description}")
            function()
        print("Done." if p.actions else "Nothing to migrate.")
        if p.notes:
            print("For you to look at:")
            print("\n".join(f"  - {x}" for x in p.notes))
    except Fail as problem:
        print(f"migrate.py: {problem}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
