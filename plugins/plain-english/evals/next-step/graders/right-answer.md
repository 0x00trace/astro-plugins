---
type: llm
---
PASS if the first thing the reply recommends is fixing the `test-macos` failure in PR #33 (`test_write_receipt` compares `/private/var/...` with `/var/...`), and it says T-14 waits on PR #33 being merged. FAIL if it recommends something else first.
