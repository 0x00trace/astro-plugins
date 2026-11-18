#!/usr/bin/env python3
"""Set up a repo's docs site for Zensical: mkdocs.yml, the docs home page and site/ in .gitignore.

The same repo always gets the same files, and a file that already exists is kept, so a second run
changes nothing. The config has no nav list, so every page in the docs folder shows in the sidebar
without a config change. Each repo's site gets its own port, written as dev_addr, from a record of
the ports handed out on this machine, so any number of sites can be served at once. Stdlib only,
for Python 3.11 and later.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path

CONFIGS = ("mkdocs.yml", "mkdocs.yaml", "zensical.toml")
HOST = "127.0.0.1"
PORTS = range(8100, 9000)
# dev_addr in an existing mkdocs.yml (dev_addr: x) or zensical.toml (dev_addr = "x").
DEV_ADDR = re.compile(
    r"""^(\s*dev_addr\s*[:=]\s*)["']?([^"'#\s]+)["']?(.*)$""", re.MULTILINE
)
# A GitHub remote over SSH or HTTPS, with or without credentials and .git.
GITHUB = re.compile(
    r"^(?:git@github\.com:|ssh://git@github\.com/|https://(?:[^@/]+@)?github\.com/)"
    r"([^/]+/[^/]+?)(?:\.git)?/?$"
)
HTTPS = re.compile(r"^https://(?:[^@/]+@)?([^/]+/.+?)(?:\.git)?/?$")
# docs_dir in an existing mkdocs.yml (docs_dir: x) or zensical.toml (docs_dir = "x").
DOCS_DIR = re.compile(
    r"""^\s*docs_dir\s*[:=]\s*["']?([^"'#\n]+?)["']?\s*(?:#.*)?$""", re.MULTILINE
)
THEME = """theme:
  name: material
  palette:
    scheme: slate
  features:
    - navigation.sections
    - navigation.indexes
    - search.highlight
"""


class Fail(Exception):
    """A problem the caller can fix; main prints it without a traceback."""


def git(cwd: Path, *args: str) -> str | None:
    try:
        done = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        return None
    return done.stdout.strip() if done.returncode == 0 and done.stdout.strip() else None


def repo_root(cwd: Path) -> Path:
    top = git(cwd, "rev-parse", "--show-toplevel")
    return Path(top) if top else cwd


def web_url(remote: str) -> str | None:
    """A remote's web URL, without credentials, or None for a remote that has none."""
    if m := GITHUB.match(remote):
        return f"https://github.com/{m.group(1)}"
    if m := HTTPS.match(remote):
        return f"https://{m.group(1)}"
    return None


def repo_url(root: Path) -> str | None:
    remote = git(root, "remote", "get-url", "origin")
    return web_url(remote) if remote else None


def quoted(text: str) -> str:
    # A JSON string is a valid YAML double-quoted scalar, whatever the text holds.
    return json.dumps(text, ensure_ascii=False)


def config(name: str, url: str | None, docs_dir: str, port: int) -> str:
    lines = [f"site_name: {quoted(name)}"]
    if url:
        lines.append(f"repo_url: {quoted(url)}")
    if docs_dir != "docs":
        lines.append(f"docs_dir: {quoted(docs_dir)}")
    lines.append(f"dev_addr: {quoted(f'{HOST}:{port}')}")
    return "\n".join(lines) + "\n" + THEME


def ports_file() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
    return Path(base) / "docs-site" / "ports.json"


def load_ports(path: Path) -> dict[str, int]:
    """The ports handed out, by repo root. A repo that's gone gives its port back."""
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        raise Fail(f"{path} isn't valid JSON: fix it, or delete it to start over")
    return {
        root: port
        for root, port in data.items()
        if isinstance(port, int) and Path(root).is_dir()
    }


def save_ports(path: Path, ports: dict[str, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(ports, indent=2, sort_keys=True) + "\n")
    temp.replace(path)


def in_use(port: int) -> bool:
    with socket.socket() as probe:
        try:
            probe.bind((HOST, port))
        except OSError:
            return True
    return False


def config_port(text: str, path: Path) -> tuple[re.Match | None, int | None]:
    """The dev_addr line in a config and its port, or (None, None) when it has none."""
    found = DEV_ADDR.search(text)
    if not found:
        return None, None
    try:
        return found, int(found.group(2).rsplit(":", 1)[1])
    except (IndexError, ValueError):
        raise Fail(f"can't read a port in {path.name}'s dev_addr: {found.group(2)}")


def pick_port(key: str, ports: dict[str, int], current: int | None) -> int:
    """This repo's port: its config's or its recorded one if no other repo has it, else a new one."""
    taken = {port for root, port in ports.items() if root != key}
    for port in (current, ports.get(key)):
        if port is not None and port not in taken:
            return port
    for port in PORTS:
        if port not in taken and not in_use(port):
            return port
    raise Fail(f"no free port from {PORTS.start} to {PORTS.stop - 1}")


def port_in_config(
    path: Path, text: str, key: str, ports: dict[str, int], report: list[str]
) -> int:
    """Give an existing config this repo's port, keeping its own dev_addr unless another repo has it."""
    found, current = config_port(text, path)
    port = pick_port(key, ports, current)
    if found and current == port:
        report.append(f"kept dev_addr {found.group(2)} in {path.name}")
    elif found:
        host = found.group(2).rsplit(":", 1)[0]
        owner = next(root for root, p in ports.items() if p == current and root != key)
        line = f"{found.group(1)}{quoted(f'{host}:{port}')}{found.group(3)}"
        path.write_text(text[: found.start()] + line + text[found.end() :])
        report.append(
            f"changed dev_addr in {path.name} from {found.group(2)} to {host}:{port},"
            f" as {current} is the port of {owner}"
        )
    elif path.suffix == ".toml":
        report.append(
            f'{path.name} has no dev_addr: add dev_addr = "{HOST}:{port}" under [project]'
        )
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        path.write_text(text + f"dev_addr: {quoted(f'{HOST}:{port}')}\n")
        report.append(f"added dev_addr {HOST}:{port} to {path.name}")
    return port


def home(name: str, description: str | None) -> str:
    text = f"# {name}\n"
    if description:
        text += "\n" + " ".join(description.split()) + "\n"
    return text


def inside(root: Path, docs_dir: str) -> str:
    """docs_dir as a relative path under root, or Fail."""
    path = Path(docs_dir)
    if path.is_absolute():
        try:
            path = path.resolve().relative_to(root.resolve())
        except ValueError:
            raise Fail(f"--docs-dir {docs_dir} is outside the repo at {root}")
    resolved = (root / path).resolve()
    if resolved == root.resolve() or not resolved.is_relative_to(root.resolve()):
        raise Fail(
            f"--docs-dir {docs_dir} has to be a folder inside the repo at {root}"
        )
    return resolved.relative_to(root.resolve()).as_posix()


def scaffold(
    cwd: Path, name: str | None, description: str | None, docs_dir: str | None
) -> list[str]:
    root = repo_root(cwd)
    name = name or root.name
    report = []
    record = ports_file()
    ports = load_ports(record)
    key = str(root.resolve())

    existing = next((c for c in CONFIGS if (root / c).is_file()), None)
    if existing:
        report.append(f"kept {existing} (it exists)")
        text = (root / existing).read_text()
        if docs_dir is None:
            found = DOCS_DIR.search(text)
            docs_dir = found.group(1).strip() if found else "docs"
    docs_dir = inside(root, docs_dir or "docs")
    if existing:
        port = port_in_config(root / existing, text, key, ports, report)
    else:
        port = pick_port(key, ports, None)
        (root / "mkdocs.yml").write_text(config(name, repo_url(root), docs_dir, port))
        report.append(f"created mkdocs.yml, with dev_addr {HOST}:{port}")
    if ports.get(key) != port:
        ports[key] = port
        save_ports(record, ports)

    index = root / docs_dir / "index.md"
    if index.exists():
        report.append(f"kept {docs_dir}/index.md (it exists)")
    else:
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text(home(name, description))
        report.append(f"created {docs_dir}/index.md")

    ignore = root / ".gitignore"
    text = ignore.read_text() if ignore.is_file() else ""
    if any(
        line.strip() in ("site/", "/site/", "site", "/site")
        for line in text.splitlines()
    ):
        report.append("kept .gitignore (it ignores site/)")
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        ignore.write_text(text + "site/\n")
        report.append(
            "added site/ to .gitignore" if text else "created .gitignore with site/"
        )
    report.append(f"uvx zensical serve shows it at http://{HOST}:{port}")
    return [f"{root}:"] + [f"  {line}" for line in report]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Set up a repo's docs site for Zensical, keeping any file that exists."
    )
    parser.add_argument(
        "--name", help="the site's name; the repo's folder name by default"
    )
    parser.add_argument(
        "--description", help="a line for the home page, under its heading"
    )
    parser.add_argument(
        "--docs-dir",
        help="the folder the docs are in, relative to the repo root; docs by default",
    )
    args = parser.parse_args(argv)
    try:
        print(
            "\n".join(scaffold(Path.cwd(), args.name, args.description, args.docs_dir))
        )
    except Fail as problem:
        print(f"scaffold.py: {problem}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
