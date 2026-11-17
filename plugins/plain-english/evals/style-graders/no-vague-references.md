---
type: llm
---
Check the reply for a vague reference: a phrase that makes the reader work out which task, PR, test, file or change is meant.

FAIL if the reply has any of these:
- A general phrase in place of specific items that the same sentence doesn't list, such as "the rest", "everything left", "everything else", "the remaining work", "the work" or "the next task".
- "The change", "the fix", "the option" or "the issue" when the reply discusses more than one, so the reader can't tell which one is meant.
- A pronoun such as "it", "this" or "that" whose meaning isn't clear from the sentences just before it.

PASS otherwise. A pronoun whose meaning is clear from the sentences just before it passes. So does "it" for the project the user asked about, and a phrase that the same or the next sentence names, as in "One thing differs on Windows: line endings."
