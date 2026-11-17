---
type: llm
---
Check every sentence of the reply for a cleft sentence that puts an abstraction first, such as "The next task is what carries the rest of the work", "Merging #33 is what lets T-14 start" or "What matters here is the macOS job".

FAIL if any sentence is built this way.

PASS if each sentence says who or what does what directly, such as "T-14 can start after #33 merges" or "The macOS job fails".
