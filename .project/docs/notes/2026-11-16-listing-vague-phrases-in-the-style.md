# Listing vague phrases in the style

After 0.2.0's Name things list, replies still sum items up ("PR #33 is the item everything else waits on") and say "the fix" with two fixes in play. Does adding those phrases to the list cut them? (AP-32)

## Found

The added lines were "hold up" (wait on), "everything left", "everything else", "every other step" and "the other two" (list the items), and "this change" and "the option", with "name the one you mean each time" for a reply that covers more than one. The release cases (`release-status`, `next-step`, `merge-today`) ran 6 times each with the plugin on 0.2.0 and on the added lines, plus the whole suite once on each, on Claude Code 2.1.326 with Sonnet 5.5 judging.

| Release cases, with the plugin | Opus 0.2.0 | Opus added lines | Fable 0.2.0 | Fable added lines |
| --- | --- | --- | --- | --- |
| Replies with no vague reference | 2 of 18 | 2 of 18 | 6 of 18 | 9 of 18 |
| "everything else/left", "every other step" | 2 in 18 | 7 in 27 | 10 in 18 | 4 in 27 |
| "the other option/way" | 1 in 18 | 5 in 27 | 0 in 18 | 0 in 27 |
| "hold(s) up" | 5 in 18 | 3 in 27 | 4 in 18 | 0 in 27 |
| "the fix", "the change", "this change" | 19 in 18 | 25 in 27 | 13 in 18 | 19 in 27 |

- On Opus, the lines didn't cut vague references, and the two phrases they name most directly, "everything else" and "the other option", came up more often. On Fable, "everything else" and "hold up" fell.
- Over the whole suite, with the plugin, replies with no vague reference stayed at 18 of 27 on Opus and went from 21 to 25 on Fable. Nothing else got worse.
- The vague-reference judge fails most long replies. An Opus `next-step` reply of 280 words named PR #33, `tests/test_cart.py` line 44, the symlink and each step in order, and still failed on "The fix is a one-line change to the test", under the paragraph that explains the failure. The eval docs say an `llm` grader gets less reliable the longer the text it reads.
- A correction to [What the Name things rule changes](2026-11-16-what-the-name-things-rule-changes.md): its Opus figure for metaphor verbs, 17 to 22 replies of 27, isn't past noise. A second run of the same 0.2.0 style scored 17. Fable's held: 15 on 0.1.0, then 21 and 23 on two runs of 0.2.0. With 3 runs per case, a grader can move by about 5 of 27 between identical runs.
- The runs cost about $72: $29.83 for the whole suite on 0.2.0, $4.57 for the extra baseline runs, and $38.06 after the change.

## What came of it

- The added lines came back out, and plain-english stays at 0.2.0. PROJECT.md's Decisions records it.
- A claim about a change of a few replies in 27 needs more runs per case than 3, such as the 6 used here.
