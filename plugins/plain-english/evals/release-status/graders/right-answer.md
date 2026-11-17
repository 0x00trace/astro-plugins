---
type: llm
---
PASS if the reply says all of these: T-12 is done; PR #33 (T-13) is approved but its `test-macos` job fails; T-14 waits on PR #33 being merged; the release notes in PR #34 (T-15) are a draft. FAIL if it misses the failing `test-macos` job, or says PR #33 is ready to merge.
