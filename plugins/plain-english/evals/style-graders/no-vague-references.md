---
type: llm
---
Check every sentence of the reply for a vague reference: a pronoun or general noun standing for a specific task, PR, test, file, change or step that isn't named in the same sentence or the one before.

FAIL if any sentence has one, such as "it", "this", "that", "the work", "the rest", "the remaining work", "the next task", "the change", "the fix" or "the blocker" with what it means not named in that sentence or the one before.

PASS if every pronoun and general noun has what it means named in the same sentence or the one before. "It" right after the PR it means is named passes. "The release" passes when only one release is discussed.
