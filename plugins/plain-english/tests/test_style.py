"""Checks on what Claude Code acts on in the output style: its frontmatter. What the style tells
Claude to do is checked by running it, with the cases in evals/."""

import unittest
from pathlib import Path

STYLE = Path(__file__).resolve().parents[1] / "output-styles" / "plain-english.md"


def style():
    _, front, body = STYLE.read_text().split("---\n", 2)
    return dict(line.split(": ", 1) for line in front.strip().splitlines()), body


class StyleTest(unittest.TestCase):
    def test_the_style_turns_itself_on_and_keeps_the_coding_instructions(self):
        # Claude Code ignores a misspelled field without an error, so a typo here would leave the
        # style off, or drop Claude Code's software engineering instructions.
        front, _ = style()
        self.assertEqual(front["force-for-plugin"], "true")
        self.assertEqual(front["keep-coding-instructions"], "true")
        self.assertEqual(front["name"], "Plain English")


if __name__ == "__main__":
    unittest.main()
