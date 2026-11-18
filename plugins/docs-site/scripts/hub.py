#!/usr/bin/env python3
"""Run every project's docs site at once behind one address, with a dashboard that lists them.

install writes a Docker Compose project in the docs-site data folder: one container per project
running `zensical serve` from Zensical's own image, and a Caddy proxy on one host port. Each site
is at http://NAME.localhost:PORT and the dashboard at http://localhost:PORT. The sites publish no
host ports, so `uvx zensical serve` in a repo still works while the hub runs. The projects are the
repos scaffold.py has recorded. Stdlib only, for Python 3.11 and later.
"""

from __future__ import annotations

import argparse
import html
import http.client
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import scaffold
from scaffold import Fail

PORT = 8099
PROJECT = "docs-site"
ZENSICAL = "zensical/zensical:latest"
CADDY = "caddy:2-alpine"
# The port every site serves on inside its own container.
INNER = 8000
NOTE = "Written by docs-site's hub.py from the repos it has recorded. Edits are overwritten."
FILES = ("compose.yml", "caddy/Caddyfile", "www/index.html")


@dataclass
class Site:
    name: str  # its subdomain
    root: Path
    description: str
    repo_url: str

    @property
    def service(self) -> str:
        # Prefixed, so no repo's name can be the proxy's.
        return f"site-{self.name}"


def hub_dir() -> Path:
    return scaffold.ports_file().parent / "hub"


def slug(text: str) -> str:
    """text as one DNS label: lowercase letters, digits and hyphens."""
    label = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:50].strip("-")
    return label or "site"


def setting(text: str, key: str) -> str:
    """A top-level value in mkdocs.yml (key: x) or zensical.toml (key = "x"), or ""."""
    found = re.search(rf"^\s*{key}\s*[:=]\s*(.+?)\s*$", text, re.MULTILINE)
    if not found:
        return ""
    value = found.group(1)
    if value.startswith('"'):
        try:
            return str(json.JSONDecoder().raw_decode(value)[0])
        except ValueError:
            pass
    return re.sub(r"\s+#.*$", "", value).strip("'\"")


def summary(index: Path) -> str:
    """The first sentence of a docs home page, as plain text."""
    try:
        lines = index.read_text().splitlines()
    except OSError:
        return ""
    for line in lines:
        line = line.strip()
        if not line or line.startswith(("#", "---", "<!--", "```")):
            continue
        line = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", line)
        line = re.sub(r"[*_`]+", "", line)
        first = re.match(r"(.+?[.!?])(?:\s|$)", line)
        return (first.group(1) if first else line).strip()
    return ""


def sites() -> list[Site]:
    """The recorded repos, in the order they were recorded, each with a name no other has."""
    ports = scaffold.load_ports(scaffold.ports_file())
    found, taken = [], set()
    for root, _ in sorted(ports.items(), key=lambda item: (item[1], item[0])):
        path = Path(root)
        config = next(
            (path / c for c in scaffold.CONFIGS if (path / c).is_file()), None
        )
        text = config.read_text() if config else ""
        base = slug(path.name)
        name, n = base, 1
        while name in taken:
            n += 1
            name = f"{base}-{n}"
        taken.add(name)
        url = setting(text, "repo_url")
        found.append(
            Site(
                name,
                path,
                summary(path / (setting(text, "docs_dir") or "docs") / "index.md"),
                url if url.startswith(("https://", "http://")) else "",
            )
        )
    return found


def quoted(text: object) -> str:
    """A YAML double-quoted string that Compose won't read a $ in as a variable."""
    return json.dumps(str(text), ensure_ascii=False).replace("$", "$$")


def bind(source: object, target: object, read_only: bool = False) -> list[str]:
    lines = [
        "      - type: bind",
        f"        source: {quoted(source)}",
        f"        target: {quoted(target)}",
    ]
    return lines + (["        read_only: true"] if read_only else [])


def compose_text(found: list[Site], port: int, hub: Path, user: str, ipv6: bool) -> str:
    lines = [
        f"# {NOTE}",
        f"name: {PROJECT}",
        "services:",
        "  proxy:",
        f"    image: {CADDY}",
        "    ports:",
        f'      - "127.0.0.1:{port}:{port}"',
    ]
    if ipv6:
        lines.append(f'      - "[::1]:{port}:{port}"')
    lines += ["    volumes:"]
    lines += bind(hub / "caddy", "/etc/caddy", read_only=True)
    lines += bind(hub / "www", "/srv/hub", read_only=True)
    lines += ["    restart: unless-stopped"]
    for site in found:
        lines += [
            f"  {site.service}:",
            f"    image: {ZENSICAL}",
            # The repo's owner, so the site/ and .cache/ it writes in the repo aren't root's.
            f"    user: {quoted(user)}",
            f'    command: ["serve", "-a", "0.0.0.0:{INNER}"]',
            f"    working_dir: {quoted(site.root)}",
            "    volumes:",
            *bind(site.root, site.root),
            "    restart: unless-stopped",
        ]
    return "\n".join(lines) + "\n"


def caddy_text(found: list[Site], port: int) -> str:
    lines = [
        f"# {NOTE}",
        "{",
        "\tauto_https off",
        "}",
        f"http://localhost:{port}, http://127.0.0.1:{port}, http://[::1]:{port} {{",
        "\troot * /srv/hub",
        "\tfile_server",
        "}",
    ]
    for site in found:
        lines += [
            f"http://{site.name}.localhost:{port} {{",
            f"\treverse_proxy {site.service}:{INNER} {{",
            "\t\t# Zensical's server answers 400 unless Host and Origin are localhost.",
            f"\t\theader_up Host localhost:{INNER}",
            f"\t\theader_up Origin http://localhost:{INNER}",
            "\t}",
            "\thandle_errors {",
            (
                f'\t\trespond "The docs site for {site.name} is not running. '
                f'See: docker compose -p {PROJECT} logs {site.service}" 502'
            ),
            "\t}",
            "}",
        ]
    lines += [
        f"http://*.localhost:{port} {{",
        (
            f'\trespond "No docs site has that name. '
            f'The dashboard at http://localhost:{port} lists them." 404'
        ),
        "}",
    ]
    return "\n".join(lines) + "\n"


STYLE = """
:root {
  --bg: #ffffff; --ink: #16181d; --muted: #585d6b; --faint: #9a9fac;
  --rule: #e4e6ec; --accent: #4051b5;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: hsl(225 15% 8%); --ink: hsl(225 15% 92%); --muted: hsl(225 12% 68%);
    --faint: hsl(225 10% 44%); --rule: hsl(225 14% 17%); --accent: #8fa0ff;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font: 400 1.0625rem/1.55 Inter, ui-sans-serif, system-ui, "Segoe UI", sans-serif;
  -webkit-font-smoothing: antialiased;
}
main {
  max-width: 60rem; margin: 0 auto;
  padding: clamp(2rem, 7vh, 5.5rem) clamp(1.25rem, 4vw, 3rem) 4rem;
}
h1 { margin: 0; font-size: 1.125rem; font-weight: 600; letter-spacing: -0.01em; }
.count { margin: 0.1rem 0 0; color: var(--muted); }
.sites { list-style: none; margin: 2.75rem 0 0; padding: 0; border-top: 1px solid var(--rule); }
.site { padding: 1.7rem 0 1.8rem; border-bottom: 1px solid var(--rule); }
.address {
  display: inline-block; color: var(--ink); text-decoration: none; overflow-wrap: anywhere;
  font-size: clamp(1.6rem, 1.05rem + 2.4vw, 2.75rem); line-height: 1.12;
  font-weight: 650; letter-spacing: -0.028em;
}
.address .rest { color: var(--faint); font-weight: 400; }
.address:hover .name, .address:focus-visible .name { color: var(--accent); }
.about { margin: 0.6rem 0 0; max-width: 44rem; color: var(--muted); }
.repo { margin: 0.5rem 0 0; font-size: 0.9375rem; }
.repo a { color: var(--accent); text-decoration-thickness: 0.06em; text-underline-offset: 0.2em; }
a:focus-visible { outline: 2px solid var(--accent); outline-offset: 4px; border-radius: 2px; }
.note { margin: 2rem 0 0; color: var(--muted); font-size: 0.9375rem; }
.empty { margin: 2.75rem 0 0; padding-top: 1.7rem; border-top: 1px solid var(--rule); font-size: 1.25rem; }
code { font: inherit; color: var(--ink); background: color-mix(in srgb, var(--ink) 8%, transparent);
  padding: 0.05em 0.35em; border-radius: 0.25em; }
""".strip()


def page_text(found: list[Site], port: int) -> str:
    """The dashboard: each site's address as its headline, a line about it, and its repo."""
    rows = []
    for site in found:
        row = [
            '    <li class="site">',
            (
                f'      <a class="address" href="http://{site.name}.localhost:{port}/">'
                f'<span class="name">{site.name}</span>'
                f'<span class="rest">.localhost:{port}</span></a>'
            ),
        ]
        if site.description:
            row.append(f'      <p class="about">{html.escape(site.description)}</p>')
        if site.repo_url:
            where = " on GitHub" if "//github.com/" in site.repo_url else ""
            row.append(
                f'      <p class="repo"><a href="{html.escape(site.repo_url, quote=True)}">'
                f"Repository{where}</a></p>"
            )
        rows += [*row, "    </li>"]
    count = f"{len(found)} project{'' if len(found) == 1 else 's'}"
    if found:
        body = [
            '  <ul class="sites">',
            *rows,
            "  </ul>",
            '  <p class="note">To add a project, run <code>/docs-site:init</code> in its repo.</p>',
        ]
    else:
        body = [
            (
                '  <p class="empty">No projects yet. Run <code>/docs-site:init</code> in a repo, '
                "and its docs show up here.</p>"
            )
        ]
    return (
        "\n".join(
            [
                "<!doctype html>",
                f"<!-- {NOTE} -->",
                '<html lang="en">',
                "<head>",
                '<meta charset="utf-8">',
                '<meta name="viewport" content="width=device-width, initial-scale=1">',
                '<meta name="color-scheme" content="light dark">',
                "<title>Docs on this machine</title>",
                "<style>",
                STYLE,
                "</style>",
                "</head>",
                "<body>",
                "<main>",
                "  <h1>Docs on this machine</h1>",
                f'  <p class="count">{count}</p>',
                *body,
                "</main>",
                "</body>",
                "</html>",
            ]
        )
        + "\n"
    )


def write(path: Path, text: str) -> str:
    if path.is_file() and path.read_text() == text:
        return "kept"
    state = "updated" if path.exists() else "created"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return state


def docker(*args: str, check: bool = True) -> str:
    try:
        done = subprocess.run(
            ["docker", *args], capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        raise Fail(
            "the hub needs Docker with its compose plugin, and docker isn't on the PATH"
        )
    if check and done.returncode != 0:
        said = (done.stderr.strip() or done.stdout.strip()).splitlines()[-4:]
        raise Fail("\n".join(said) or f"docker {args[0]} failed")
    return done.stdout


def compose(hub: Path, *args: str, check: bool = True) -> str:
    return docker("compose", "-f", str(hub / "compose.yml"), *args, check=check)


def ipv6_loopback() -> bool:
    """Whether ::1 can be bound, so the proxy can be published on it too."""
    try:
        with socket.socket(socket.AF_INET6) as probe:
            probe.bind(("::1", 0))
    except OSError:
        return False
    return True


def answers(port: int, host: str) -> int | None:
    """The status the hub gives for host's front page, or None when nothing answers."""
    try:
        link = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        link.request("GET", "/", headers={"Host": f"{host}:{port}"})
        status = link.getresponse().status
        link.close()
    except (OSError, http.client.HTTPException):
        return None
    return status


def wait(port: int, hosts: list[str], seconds: float) -> set[str]:
    """The hosts that still don't answer 200 after up to seconds."""
    pending = set(hosts)
    deadline = time.monotonic() + seconds
    while True:
        pending = {host for host in pending if answers(port, host) != 200}
        if not pending or time.monotonic() >= deadline:
            return pending
        time.sleep(0.5)


def installed_port(hub: Path) -> int | None:
    """The port of the hub that's installed, or None when there's none."""
    try:
        found = re.search(
            r'"127\.0\.0\.1:(\d+):\d+"', (hub / "compose.yml").read_text()
        )
    except OSError:
        return None
    return int(found.group(1)) if found else None


def reload_proxy(hub: Path) -> None:
    """Have the running proxy read its routes again. It can take a moment to be ready."""
    for attempt in range(6):
        try:
            compose(
                hub,
                "exec",
                "-T",
                "proxy",
                "caddy",
                "reload",
                "--config",
                "/etc/caddy/Caddyfile",
            )
            return
        except Fail:
            if attempt == 5:
                raise
            time.sleep(1)


def address(name: str, port: int) -> str:
    return f"http://{name}.localhost:{port}"


def said(site: Site, port: int, down: set[str]) -> str:
    if f"{site.name}.localhost" in down:
        return (
            f"{address(site.name, port)} (not answering yet: "
            f"docker compose -p {PROJECT} logs {site.service})"
        )
    return address(site.name, port)


def apply(port: int) -> tuple[list[Site], list[str], set[str]]:
    """Write the hub's files, start what isn't running, and wait for the sites to answer."""
    hub = hub_dir()
    docker("compose", "version")
    found = sites()
    had_proxy = (hub / "compose.yml").is_file() and bool(
        compose(hub, "ps", "-q", "proxy", check=False).strip()
    )
    texts = (
        compose_text(found, port, hub, f"{os.getuid()}:{os.getgid()}", ipv6_loopback()),
        caddy_text(found, port),
        page_text(found, port),
    )
    states = {name: write(hub / name, text) for name, text in zip(FILES, texts)}
    report = [f"{state} {name}" for name, state in states.items()]
    compose(hub, "up", "-d", "--remove-orphans")
    if had_proxy and states["caddy/Caddyfile"] != "kept":
        reload_proxy(hub)
        report.append("reloaded the proxy's routes")
    hosts = ["localhost"] + [f"{site.name}.localhost" for site in found]
    return found, report, wait(port, hosts, 45)


def install(port: int | None) -> list[str]:
    hub = hub_dir()
    port = port or installed_port(hub) or PORT
    found, report, down = apply(port)
    if "localhost" in down:
        report.append(
            f"the dashboard isn't answering on port {port}: docker compose -p {PROJECT} logs proxy"
        )
    else:
        report.append(f"dashboard: http://localhost:{port}")
    report += [f"{site.name}: {said(site, port, down)}" for site in found]
    return [f"{hub}:"] + [f"  {line}" for line in report]


def update(repo: str | None) -> list[str]:
    """Bring an installed hub in line with the recorded repos. Does nothing when there's no hub."""
    hub = hub_dir()
    port = installed_port(hub)
    if port is None:
        return []
    found, _, down = apply(port)
    if repo is None:
        return [f"{site.name}: {said(site, port, down)}" for site in found]
    root = Path(repo).resolve()
    return [
        f"the hub serves it at {said(site, port, down)}"
        for site in found
        if site.root.resolve() == root
    ]


def status() -> tuple[list[str], bool]:
    hub = hub_dir()
    port = installed_port(hub)
    if port is None:
        raise Fail("the hub isn't installed: hub.py install sets it up")
    out = compose(hub, "ps", "--all", "--format", "json").strip()
    # Compose prints one JSON object a line, and older versions one list.
    rows = (
        json.loads(out)
        if out.startswith("[")
        else [json.loads(x) for x in out.splitlines() if x]
    )
    state = {row["Service"]: row.get("State", "?") for row in rows}
    lines = [f"{hub}:"]
    ok = True

    def line(label: str, service: str, host: str, url: str) -> None:
        nonlocal ok
        code = answers(port, host)
        good = code == 200
        ok = ok and good
        answer = "answering" if good else f"not answering ({code or 'no reply'})"
        lines.append(
            f"  {label}: {url}  container {state.get(service, 'missing')}, {answer}"
        )

    line("dashboard", "proxy", "localhost", f"http://localhost:{port}")
    for site in sites():
        line(
            site.name, site.service, f"{site.name}.localhost", address(site.name, port)
        )
    return lines, ok


def remove() -> list[str]:
    hub = hub_dir()
    if not (hub / "compose.yml").is_file():
        return [f"{hub}:", "  there's no hub to remove"]
    compose(hub, "down", "--volumes", "--remove-orphans")
    shutil.rmtree(hub)
    return [
        f"{hub}:",
        "  stopped and removed the hub's containers",
        "  removed the hub's folder",
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Serve every recorded project's docs at NAME.localhost, with a dashboard."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    i = commands.add_parser(
        "install",
        help="write the hub's files and start it; run again to bring it up to date",
    )
    i.add_argument("--port", type=int, help=f"the hub's one port ({PORT} by default)")
    u = commands.add_parser(
        "update",
        help="bring an installed hub up to date; does nothing when there's none",
    )
    u.add_argument("--repo", help="say only where this repo's site is")
    commands.add_parser("status", help="whether the dashboard and each site answer")
    commands.add_parser(
        "remove", help="stop the hub and remove its containers and folder"
    )
    args = parser.parse_args(argv)
    try:
        if args.command == "install":
            print("\n".join(install(args.port)))
        elif args.command == "update":
            lines = update(args.repo)
            if lines:
                print("\n".join(lines))
        elif args.command == "status":
            lines, ok = status()
            print("\n".join(lines))
            return 0 if ok else 1
        else:
            print("\n".join(remove()))
    except Fail as problem:
        print(f"hub.py: {problem}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
