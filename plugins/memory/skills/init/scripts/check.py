"""List the instruction and memory files Claude Code loads for a project, and check them.

    python3 check.py [--root DIR] [--memory-dir DIR] [PATH ...]

With no PATH, it reports on every file that loads for the project at --root (the current folder
by default): CLAUDE.md files, rules, AGENTS.md, other tools' instruction files, the project's auto
memory and the global memory. With PATHs, it checks only those: instruction files, or memory
folders. It reads files and changes nothing.

The limits come from Claude Code's memory docs (https://code.claude.com/docs/en/memory), and for
the global memory from the global-memory plugin.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

LINE_TARGET = 200  # "target under 200 lines per CLAUDE.md file"
ON_DEMAND_CHARS = (
    40_000  # a file that loads on demand reaches Claude cut to this (200K window)
)
MAX_BYTES = 4 * 1024 * 1024  # Claude Code skips a file over 4 MiB
IMPORT_HOPS = 4  # imports are followed "with a maximum depth of four hops"
INDEX_LINES, INDEX_BYTES = (
    200,
    25_000,
)  # MEMORY.md loads up to its first 200 lines or 25KB
GLOBAL_LINE_CHARS = 150  # the global-memory plugin's limit for one index line
GLOBAL_FILE_BYTES, GLOBAL_FILE_LINES = 4096, 200  # and for one memory file
MEMORY_TYPES = {
    "auto": {"user", "feedback", "project", "reference"},
    "global": {"user", "feedback", "reference"},
}
MANAGED = [
    Path("/etc/claude-code/CLAUDE.md"),
    Path("/Library/Application Support/ClaudeCode/CLAUDE.md"),
]
OTHER_TOOLS = [
    ".cursorrules",
    ".cursor/rules",
    ".github/copilot-instructions.md",
    ".windsurfrules",
    ".windsurf/rules",
    ".clinerules",
    ".devin/rules",
]
SKIP_DIRS = {
    "node_modules",
    "vendor",
    "dist",
    "build",
    "target",
    "out",
    "coverage",
    "venv",
}
PATH_NAMES = {"Makefile", "Dockerfile", "Justfile", "Rakefile", "Gemfile", "Procfile"}
# Extensions that make a code span such as `setup.cfg` read as a file name.
PATH_EXTS = {
    *(
        "md",
        "mdx",
        "txt",
        "json",
        "jsonc",
        "toml",
        "yaml",
        "yml",
        "ini",
        "cfg",
        "conf",
        "env",
    ),
    *(
        "lock",
        "py",
        "pyi",
        "ipynb",
        "js",
        "jsx",
        "mjs",
        "cjs",
        "ts",
        "tsx",
        "mts",
        "cts",
    ),
    *(
        "vue",
        "svelte",
        "go",
        "mod",
        "sum",
        "rs",
        "java",
        "kt",
        "kts",
        "gradle",
        "scala",
    ),
    *(
        "rb",
        "php",
        "cs",
        "swift",
        "c",
        "h",
        "cc",
        "cpp",
        "hpp",
        "zig",
        "lua",
        "sh",
        "bash",
    ),
    *("zsh", "fish", "ps1", "sql", "prisma", "graphql", "proto", "html", "css", "scss"),
    *("sass", "less", "xml", "csv", "tf", "nix", "gd", "tscn", "tres"),
}

FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
SPAN = re.compile(r"(`+)(.+?)\1")
IMPORT = re.compile(r'(?<!\S)@("[^"\n]*"?|(?:\\ |\S)+)')
INDEX_LINK = re.compile(r"\]\(<?([^)>]+)>?\)")
KEY = re.compile(r"([A-Za-z_][\w-]*):(?:\s+(.*))?$")


@dataclass
class Report:
    wd: Path
    config: Path
    problems: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    unfound: list[str] = field(default_factory=list)
    imported: set[Path] = field(default_factory=set)

    def show(self, path: Path) -> str:
        for base, prefix in [(self.wd, ""), (Path.home(), "~/")]:
            if path.is_relative_to(base) and path != base:
                return prefix + path.relative_to(base).as_posix()
        return str(path)

    def at(self, path: Path, line: int | None) -> str:
        return self.show(path) + (f":{line}" if line else "")

    def problem(self, path: Path, line: int | None, text: str) -> None:
        self.problems.append(f"{self.at(path, line)}  {text}")

    def note(self, path: Path, line: int | None, text: str) -> None:
        self.notes.append(f"{self.at(path, line)}  {text}")


def read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def git(wd: Path, *args: str) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(
            ["git", "-C", str(wd), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def git_root(wd: Path) -> Path | None:
    done = git(wd, "rev-parse", "--show-toplevel")
    return Path(done.stdout.strip()) if done and done.returncode == 0 else None


def config_dir() -> Path:
    return Path(
        os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude"
    ).expanduser()


def same(a: Path, b: Path) -> bool:
    try:
        return a.resolve() == b.resolve()
    except OSError:
        return False


# Markdown: the lines Claude Code reads imports from


def prose(text: str, keep_spans: bool = False):
    """Yield (line number, line) outside fenced code blocks and block-level HTML comments.
    Code spans are blanked out unless keep_spans is set."""
    fence, in_comment = None, False
    for n, line in enumerate(text.splitlines(), 1):
        if in_comment:
            if "-->" not in line:
                continue
            in_comment, line = False, line.split("-->", 1)[1]
        mark = FENCE.match(line)
        if fence:
            if (
                mark
                and mark.group(1)[0] == fence[0]
                and len(mark.group(1)) >= len(fence)
            ):
                fence = None
            continue
        if mark:
            fence = mark.group(1)
            continue
        if line.lstrip().startswith("<!--"):
            rest = line.split("<!--", 1)[1]
            if "-->" not in rest:
                in_comment = True
                continue
            line = rest.split("-->", 1)[1]
        yield n, line if keep_spans else SPAN.sub(" ", line)


def imports(text: str):
    """Yield (line number, token) for each @ import, as written, without trailing punctuation."""
    for n, line in prose(text):
        for match in IMPORT.finditer(line):
            token = match.group(1)
            if not token.startswith('"'):
                token = token.rstrip(".,;:!?)")
            if token:
                yield n, token


def resolve(token: str, base: Path) -> Path:
    token = token.replace("\\ ", " ")
    if token == "~" or token.startswith("~/"):
        return Path.home() / token[2:]
    path = Path(token)
    return path if path.is_absolute() else base / path


def follow_imports(
    r: Report, path: Path, text: str, scope: str, hop: int = 1, seen=None
):
    """Check the imports in text and return the files that load through them, at any depth."""
    seen = seen if seen is not None else {path.resolve()}
    loaded: list[Path] = []
    for line, token in imports(text):
        if token.startswith('"'):
            r.problem(
                path,
                line,
                f"@{token} is quoted, so it isn't imported; escape spaces with \\",
            )
            continue
        target = resolve(token, path.parent)
        if not target.exists():
            r.problem(
                path,
                line,
                f"@{token} doesn't exist (if it isn't an import, put it in backticks)",
            )
            continue
        if target.is_dir():
            r.problem(path, line, f"@{token} is a folder; an import must name a file")
            continue
        if hop > IMPORT_HOPS:
            r.problem(
                path,
                line,
                f"@{token} is {hop} imports deep, past the 4 that Claude Code follows",
            )
            continue
        if scope == "project" and not target.resolve().is_relative_to(r.wd.resolve()):
            r.note(
                path,
                line,
                f"@{token} is outside the project: Claude Code asks once to allow it",
            )
        key = target.resolve()
        if key in seen:
            continue
        seen.add(key)
        r.imported.add(key)
        loaded.append(target)
        loaded += follow_imports(r, target, read(target) or "", scope, hop + 1, seen)
    return loaded


def looks_like_path(token: str) -> bool:
    if not token or token[0] in "-$@<#~" and not token.startswith("~/"):
        return False
    if any(c.isspace() for c in token) or any(
        c in token for c in "*?{}[]()<>=|;,'\"!#:"
    ):
        return False
    first, _, rest = token.partition("/")
    if rest and "." in first and not first.startswith("."):
        return False  # a domain, such as github.com/owner
    if token.startswith("/") and "/" not in token[1:] and "." not in token:
        return False  # a slash command, such as /init
    name = token.rstrip("/").rsplit("/", 1)[-1]
    if "/" in token or name in PATH_NAMES or (name.startswith(".") and len(name) > 1):
        return True
    return "." in name and name.rsplit(".", 1)[1].lower() in PATH_EXTS


def check_named_paths(r: Report, path: Path, text: str, bases: list[Path]) -> None:
    """Note each path named in a code span that exists under none of the bases. With no bases,
    only absolute and ~/ paths are checked."""
    for n, line in prose(text, keep_spans=True):
        for _, token in SPAN.findall(line):
            token = re.sub(r":\d+(?::\d+)?$", "", token.strip())
            if not looks_like_path(token):
                continue
            target = Path(token).expanduser()
            if target.is_absolute():
                found = target.exists()
            elif bases:
                found = any((base / token).exists() for base in bases)
            else:
                continue
            if not found:
                r.unfound.append(f"{r.at(path, n)}  `{token}`")


def lines_of(text: str) -> int:
    return len(text.splitlines())


def count(n: int, word: str) -> str:
    return f"{n} {word}" + ("" if n == 1 else "s")


def check_instructions(
    r: Report, path: Path, scope: str, on_demand: bool = False
) -> str:
    """Check one CLAUDE.md, CLAUDE.local.md or AGENTS.md file. Return its size in words."""
    text = read(path)
    if text is None:
        r.problem(path, None, "can't be read")
        return "unreadable"
    if path.stat().st_size > MAX_BYTES:
        r.problem(path, None, "is over 4 MiB, so Claude Code skips all of it")
    loaded = follow_imports(r, path, text, scope)
    texts = [text] + [read(p) or "" for p in loaded]
    own, total = lines_of(text), sum(lines_of(t) for t in texts)
    if total > LINE_TARGET:
        what = "with its imports " if loaded else ""
        r.problem(
            path, None, f"{total} lines {what}(the docs' target is under {LINE_TARGET})"
        )
    chars = sum(len(t) for t in texts)
    if on_demand and chars > ON_DEMAND_CHARS:
        r.problem(
            path, None, f"{chars:,} characters: Claude gets only the first 40,000"
        )
    bases = (
        [] if scope == "user" else unique([path.parent, r.wd, git_root(r.wd) or r.wd])
    )
    check_named_paths(r, path, text, bases)
    return count(own, "line") + (f", {total} with imports" if loaded else "")


def unique(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        if not any(same(p, q) for q in out):
            out.append(p)
    return out


# Frontmatter


def split_frontmatter(text: str) -> tuple[str | None, bool]:
    """Return (frontmatter, closed). Frontmatter is None when the file has none."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, True
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]), True
    return "\n".join(lines[1:]), False


def scalar(value: str):
    """Read one YAML value written on one line. Return (value, error)."""
    value = value.strip()
    if not value:
        return None, None
    if value[0] in "\"'":
        if len(value) < 2 or value[-1] != value[0]:
            return None, "a quote isn't closed"
        return value[1:-1], None
    if value[0] == "[":
        if not value.endswith("]"):
            return None, "a [ isn't closed"
        items = [scalar(part) for part in value[1:-1].split(",") if part.strip()]
        errors = [e for _, e in items if e]
        return ([v for v, _ in items], None) if not errors else (None, errors[0])
    if value[0] in "*&!%@`{]},":
        return (
            None,
            f"a value starts with {value[0]!r}, which YAML reads as syntax: quote it",
        )
    if ": " in value:
        return None, "a value has ': ' in it: quote it"
    return value.split(" #", 1)[0].rstrip(), None


def parse_yaml(front: str):
    """Read the simple YAML that frontmatter holds: keys with values, lists and one level of
    nested keys. Return (fields, error)."""
    data: dict = {}
    key, block = None, False
    for raw in front.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indented, line = raw[0] in " \t", raw.strip()
        if block and indented:
            data[key] = ((data[key] or "") + " " + line).strip()
            continue
        block = False
        if not indented:
            match = KEY.match(line)
            if not match:
                return None, f"can't read the line {line!r}"
            key, value = match.group(1), match.group(2) or ""
            if value.strip() in ("|", ">", "|-", ">-", "|+", ">+"):
                data[key], block = "", True
                continue
            data[key], error = scalar(value)
            if error:
                return None, f"{key}: {error}"
        elif key is None:
            return None, f"the line {line!r} is indented under no field"
        elif line == "-" or line.startswith("- "):
            item, error = scalar(line[1:])
            if error or not isinstance(data[key] or [], list):
                return None, f"{key}: {error or 'mixes a value and a list'}"
            data[key] = (data[key] or []) + [item]
        else:
            match = KEY.match(line)
            if not match or not isinstance(data[key] or {}, dict):
                return None, f"{key}: can't read the line {line!r}"
            sub, error = scalar(match.group(2) or "")
            if error:
                return None, f"{key}.{match.group(1)}: {error}"
            data[key] = {**(data[key] or {}), match.group(1): sub}
    return data, None


# Rules


def expand_braces(pattern: str) -> list[str]:
    match = re.search(r"\{([^{}]*)\}", pattern)
    if not match:
        return [pattern]
    head, tail = pattern[: match.start()], pattern[match.end() :]
    return [
        x for alt in match.group(1).split(",") for x in expand_braces(head + alt + tail)
    ]


def glob_regex(pattern: str):
    """A regex for a paths pattern, matched against paths relative to the rule's base folder. A
    pattern with no / before its end matches at any depth. Return None for a pattern with a [ that
    isn't closed: such a pattern matches nothing."""
    anchored = "/" in pattern.rstrip("/")
    p, out, i = pattern.lstrip("/"), [], 0
    while i < len(p):
        if p.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif p.startswith("**", i):
            out.append(".*")
            i += 2
        elif p[i] == "*":
            out.append("[^/]*")
            i += 1
        elif p[i] == "?":
            out.append("[^/]")
            i += 1
        elif p[i] == "[":
            end = p.find("]", i + 2)
            if end < 0:
                return None
            inner = p[i + 1 : end]
            out.append("[" + ("^" + inner[1:] if inner[0] == "!" else inner) + "]")
            i = end + 1
        else:
            out.append(re.escape(p[i]))
            i += 1
    body = "".join(out) + (".*" if p.endswith("/") else "")
    return re.compile(("" if anchored else "(?:.*/)?") + body + "$")


def project_files(wd: Path) -> list[str]:
    """The project's files relative to wd: git's tracked and unignored files, or a walk."""
    done = git(wd, "ls-files", "-co", "--exclude-standard")
    if done and done.returncode == 0:
        return done.stdout.splitlines()
    files = []
    for folder, dirs, names in os.walk(wd):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and d != ".git"]
        files += [(Path(folder) / n).relative_to(wd).as_posix() for n in names]
    return files


def check_rule(r: Report, path: Path, files: list[str] | None) -> tuple[bool, str]:
    """Check one rule file. Return (loads at launch, what it says about paths). With files, also
    report each pattern that matches none of them."""
    text = read(path)
    if text is None:
        r.problem(path, None, "can't be read")
        return True, "unreadable"
    front, closed = split_frontmatter(text)
    if front is None:
        return True, "no paths, so it loads in every session"
    if not closed:
        r.problem(path, 1, "frontmatter has no closing ---")
    data, error = parse_yaml(front)
    if error:
        r.problem(
            path,
            1,
            f"frontmatter doesn't parse ({error}), so the rule loads everywhere",
        )
        return True, "frontmatter doesn't parse"
    for key in data:
        if key != "paths":
            r.problem(
                path, None, f"`{key}:` is ignored: `paths` is the only field rules have"
            )
    paths = data.get("paths")
    if paths is None:
        return True, "no paths, so it loads in every session"
    if isinstance(paths, str):
        patterns = [p.strip() for p in paths.split(",") if p.strip()]
    elif isinstance(paths, list) and all(isinstance(p, str) for p in paths):
        patterns = [p for p in paths if p]
    else:
        r.problem(path, None, "`paths` must be a list or a comma-separated string")
        return True, "paths can't be read"
    for pattern in patterns:
        regexes = [glob_regex(p) for p in expand_braces(pattern)[:1000]]
        if None in regexes:
            r.problem(
                path, None, f"`{pattern}` has a [ with no ], so it matches nothing"
            )
        elif files is not None and not any(x.match(f) for x in regexes for f in files):
            r.note(path, None, f"`{pattern}` matches no file in the project")
    return False, "paths: " + ", ".join(patterns)


# Memory


def check_memory(r: Report, folder: Path, kind: str) -> str:
    """Check a memory folder: its MEMORY.md index and each memory file. Return a summary."""
    index = folder / "MEMORY.md"
    files = sorted(p for p in folder.rglob("*.md") if p != index)
    listed: dict[str, int] = {}
    summary = f"{len(files)} memor{'y' if len(files) == 1 else 'ies'}"
    if not index.is_file():
        if files:
            r.problem(
                index, None, "doesn't exist, so none of these memories load at startup"
            )
        return summary + ", no MEMORY.md"
    text = read(index) or ""
    size = len(text.encode())
    used = 0
    for n, line in enumerate(text.splitlines(), 1):
        used += len(line.encode()) + 1
        for target in INDEX_LINK.findall(line):
            target = target.split("#", 1)[0]
            if target in listed:
                r.problem(
                    index, n, f"lists {target} again (first on line {listed[target]})"
                )
                continue
            listed[target] = n
            if not (folder / target).is_file():
                r.problem(index, n, f"links to {target}, which doesn't exist")
            if n > INDEX_LINES or used > INDEX_BYTES:
                r.problem(
                    index,
                    n,
                    f"{target} is past the first 200 lines or 25 KB, so it never loads",
                )
        if kind == "global" and len(line) > GLOBAL_LINE_CHARS:
            r.problem(
                index,
                n,
                f"is {len(line)} characters, over global-memory's {GLOBAL_LINE_CHARS}",
            )
    lines = lines_of(text)
    summary += (
        f"; MEMORY.md {count(lines, 'line')} and {size / 1000:.1f} KB, of 200 and 25 KB"
    )
    if lines > INDEX_LINES or size > INDEX_BYTES:
        r.problem(
            index,
            None,
            f"is {lines} lines, {size:,} bytes: only the first 200 lines or 25 KB load",
        )
    names = {(folder / t).resolve() for t in listed}
    root = git_root(r.wd) or r.wd
    for path in files:
        if path.resolve() not in names:
            r.problem(path, None, "isn't in MEMORY.md, so it never loads at startup")
        check_memory_file(r, path, kind, [r.wd, root] if kind == "auto" else [])
    return summary


def check_memory_file(r: Report, path: Path, kind: str, bases: list[Path]) -> None:
    text = read(path)
    if text is None:
        r.problem(path, None, "can't be read")
        return
    front, closed = split_frontmatter(text)
    if front is None or not closed:
        r.problem(path, 1, "has no frontmatter (name, description and type)")
        return
    data, error = parse_yaml(front)
    if error:
        r.problem(path, 1, f"frontmatter doesn't parse ({error})")
        return
    for key in ("name", "description"):
        if not data.get(key):
            r.problem(path, 1, f"frontmatter has no {key}")
    meta = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    kind_of = data.get("type") or meta.get("type")
    allowed = MEMORY_TYPES[kind]
    if kind_of not in allowed:
        r.problem(
            path,
            1,
            f"type is {kind_of or 'missing'}; it must be one of {', '.join(sorted(allowed))}",
        )
    if kind == "global":
        if data.get("name") and data["name"] != path.stem:
            r.problem(
                path, 1, f"name {data['name']} isn't the file's name, {path.stem}"
            )
        size, lines = len(text.encode()), lines_of(text)
        if size > GLOBAL_FILE_BYTES or lines > GLOBAL_FILE_LINES:
            r.problem(
                path,
                None,
                f"is {size:,} bytes, {lines} lines: over global-memory's 4,096 and 200",
            )
    if bases:
        check_named_paths(r, path, text, unique(bases))


def guess_memory_dir(r: Report) -> Path | None:
    root = git_root(r.wd) or r.wd
    folder = r.config / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(root)) / "memory"
    return folder if folder.is_dir() else None


# The whole survey


def survey(r: Report, memory_dir: Path | None) -> list[str]:
    out: list[str] = []
    launch: list[tuple[str, Path, str]] = []
    demand: list[tuple[str, Path, str]] = []
    unloaded: list[tuple[str, Path, str]] = []
    repo = git_root(r.wd)
    user_md = r.config / "CLAUDE.md"

    for path in MANAGED:
        if path.is_file():
            launch.append(("managed", path, check_instructions(r, path, "managed")))
    if user_md.is_file():
        launch.append(("user", user_md, check_instructions(r, user_md, "user")))
    for path in sorted((r.config / "rules").rglob("*.md")):
        at_launch, info = check_rule(r, path, None)
        (launch if at_launch else demand).append(("user rule", path, info))

    claude_files, agents = [], []
    for folder in [r.wd, *r.wd.parents]:
        for rel, kind in [
            ("CLAUDE.md", "project"),
            (".claude/CLAUDE.md", "project"),
            ("CLAUDE.local.md", "local"),
        ]:
            path = folder / rel
            if not path.is_file() or same(path, user_md):
                continue
            claude_files.append(path)
            label = kind if folder == r.wd else "parent folder"
            launch.append((label, path, check_instructions(r, path, "project")))
            if kind == "local" and folder == r.wd and repo:
                done = git(r.wd, "check-ignore", "-q", str(path))
                if done and done.returncode == 1:
                    r.problem(path, None, "isn't gitignored, so it can be committed")
        agents += [
            folder / rel
            for rel in ("AGENTS.md", ".claude/AGENTS.md")
            if (folder / rel).is_file()
        ]
    if (r.wd / "CLAUDE.md").is_file() and (r.wd / ".claude/CLAUDE.md").is_file():
        r.note(
            r.wd / "CLAUDE.md",
            None,
            "and .claude/CLAUDE.md both load: treat them as one file",
        )

    files = project_files(r.wd)
    for path in sorted((r.wd / ".claude" / "rules").rglob("*.md")):
        at_launch, info = check_rule(r, path, files)
        (launch if at_launch else demand).append(("rule", path, info))

    for folder in subfolders(r.wd):
        for rel in ("CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md"):
            if (folder / rel).is_file():
                path = folder / rel
                demand.append(
                    ("subfolder", path, check_instructions(r, path, "project", True))
                )
        for path in sorted((folder / ".claude" / "rules").rglob("*.md")):
            demand.append(("subfolder rule", path, check_rule(r, path, None)[1]))
        own = [
            folder / n for n in ("CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md")
        ]
        if (folder / "AGENTS.md").is_file() and not any(p.is_file() for p in own):
            path = folder / "AGENTS.md"
            demand.append(
                ("subfolder", path, check_instructions(r, path, "project", True))
            )

    for path in agents:
        if path.resolve() in r.imported:
            unloaded.append(("AGENTS.md", path, "loads through an @ import"))
        elif claude_files:
            unloaded.append(
                ("AGENTS.md", path, "not read, because a CLAUDE.md file exists")
            )
        else:
            launch.append(("AGENTS.md", path, check_instructions(r, path, "project")))
    for rel in OTHER_TOOLS:
        if (r.wd / rel).exists():
            unloaded.append(("other tool", r.wd / rel, "Claude Code doesn't read it"))

    if repo:
        out.append(
            f"Project: {r.wd} (git repo {r.show(repo) if repo != r.wd else 'root'})"
        )
    else:
        out.append(
            f"Project: {r.wd} (not a git repo: a CLAUDE.md here loads in every folder below)"
        )
    out.append(f"Config folder: {r.show(r.config)}")
    for title, rows in [
        ("Load at launch", launch),
        ("Load when Claude works with matching files", demand),
        ("Present but not loaded directly", unloaded),
    ]:
        if rows:
            out += ["", f"{title}:"] + [
                f"  {k:<14} {r.show(p):<44} {i}" for k, p, i in rows
            ]

    memory = []
    memory_dir = memory_dir or guess_memory_dir(r)
    if memory_dir and memory_dir.is_dir():
        memory.append(("auto", memory_dir, check_memory(r, memory_dir, "auto")))
    if (r.config / "memory").is_dir():
        memory.append(
            (
                "global",
                r.config / "memory",
                check_memory(r, r.config / "memory", "global"),
            )
        )
    if memory:
        out += ["", "Memory:"] + [
            f"  {k:<14} {r.show(p):<44} {i}" for k, p, i in memory
        ]

    absent = [
        name
        for name, present in [
            (
                "project CLAUDE.md",
                any(
                    p.parent in (r.wd, r.wd / ".claude") and p.name == "CLAUDE.md"
                    for p in claude_files
                ),
            ),
            ("CLAUDE.local.md", (r.wd / "CLAUDE.local.md").is_file()),
            (r.show(user_md), user_md.is_file()),
            ("auto memory", any(k == "auto" for k, _, _ in memory)),
            ("global memory", any(k == "global" for k, _, _ in memory)),
        ]
        if not present
    ]
    if absent:
        out += ["", "Not present: " + ", ".join(absent)]
    return out


def subfolders(wd: Path):
    """Folders below wd that may hold instruction files, skipping hidden and generated ones."""
    for folder, dirs, _ in os.walk(wd):
        dirs[:] = sorted(
            d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")
        )
        if Path(folder) != wd:
            yield Path(folder)


def check_paths(r: Report, paths: list[Path]) -> list[str]:
    out = []
    files = None
    for path in paths:
        path = path.expanduser().absolute()
        if path.is_dir() or path.name == "MEMORY.md":
            folder = path if path.is_dir() else path.parent
            kind = "global" if same(folder, r.config / "memory") else "auto"
            out.append(
                f"  {kind + ' memory':<14} {r.show(folder):<44} {check_memory(r, folder, kind)}"
            )
        elif not path.is_file():
            r.problem(path, None, "doesn't exist")
        elif (
            "rules" in path.parts
            and ".claude" in path.parts
            or path.is_relative_to(r.config / "rules")
        ):
            user = path.is_relative_to(r.config)
            if files is None and not user:
                files = project_files(r.wd)
            out.append(
                f"  {'rule':<14} {r.show(path):<44} {check_rule(r, path, None if user else files)[1]}"
            )
        else:
            scope = "user" if path.is_relative_to(r.config) else "project"
            demand = scope == "project" and path.parent not in (
                r.wd,
                r.wd / ".claude",
                *r.wd.parents,
            )
            out.append(
                f"  {'file':<14} {r.show(path):<44} {check_instructions(r, path, scope, demand)}"
            )
    return out


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--root", type=Path, default=Path.cwd(), help="the project folder"
    )
    parser.add_argument(
        "--memory-dir", type=Path, help="the project's auto memory folder"
    )
    parser.add_argument(
        "paths", nargs="*", type=Path, help="files or memory folders to check"
    )
    args = parser.parse_args(argv)
    r = Report(wd=args.root.expanduser().absolute(), config=config_dir())
    memory_dir = args.memory_dir.expanduser().absolute() if args.memory_dir else None
    out = check_paths(r, args.paths) if args.paths else survey(r, memory_dir)
    for title, rows in [
        (f"Problems ({len(r.problems)})", r.problems),
        ("Notes", r.notes),
        (
            "Paths named in code spans that don't exist (some may be examples)",
            r.unfound,
        ),
    ]:
        if rows:
            out += ["", f"{title}:"] + [f"  {row}" for row in rows]
    if not r.problems:
        out += ["", "Problems: none found."]
    print("\n".join(out))


if __name__ == "__main__":
    main()
