"""Build a scratch git repo from one of the review fixtures in fixtures/.

The fixtures keep their instruction files under names that don't load, so a session in this repo
never picks up their deliberately flawed CLAUDE.md as a nested file. The copy gets the real names:
CLAUDE.fixture.md becomes CLAUDE.md, and claude-dir becomes .claude.

    python3 plugins/instructions/tests/fixture_repo.py review-me /path/to/scratch/review-me
"""

import shutil
import subprocess
import sys
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
REAL_NAMES = {"CLAUDE.fixture.md": "CLAUDE.md", "claude-dir": ".claude"}


def build(name, dest):
    """Copy fixture `name` to `dest` (which must not exist) as a git repo with one commit."""
    dest = Path(dest)
    shutil.copytree(FIXTURES / name, dest)
    # Files before folders, so renaming claude-dir doesn't move a file still to be renamed.
    for stored, real in REAL_NAMES.items():
        for path in list(dest.rglob(stored)):
            path.rename(path.with_name(real))
    git = ["git", "-C", str(dest)]
    subprocess.run([*git, "init", "-q", "-b", "main"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run(
        [
            *git,
            "-c",
            "user.name=fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-q",
            "-m",
            "Initial commit",
        ],
        check=True,
    )
    return dest


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(
            f"usage: {sys.argv[0]} <{'|'.join(sorted(p.name for p in FIXTURES.iterdir() if p.is_dir()))}> <dest>"
        )
    print(build(sys.argv[1], sys.argv[2]))
