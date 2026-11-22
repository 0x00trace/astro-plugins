"""Checks on the plugin's test files themselves."""

import ast
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent


def is_main_block(node):
    return (
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "__name__"
    )


class TestFilesTest(unittest.TestCase):
    def test_each_ends_with_its_main_block(self):
        # `python3 FILE` runs unittest.main() when Python reaches the block, so a test class
        # defined after it never runs, and the run still says OK (#170).
        for path in sorted(TESTS.glob("test_*.py")):
            with self.subTest(path.name):
                body = ast.parse(path.read_text()).body
                blocks = [i for i, node in enumerate(body) if is_main_block(node)]
                self.assertEqual(blocks, [len(body) - 1])


if __name__ == "__main__":
    unittest.main()
