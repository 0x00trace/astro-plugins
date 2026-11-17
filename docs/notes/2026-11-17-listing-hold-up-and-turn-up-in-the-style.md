# Listing hold up and turn up in the style

On 0.2.0, "hold up" is the most common dead metaphor left in status and plan replies. AP-32 listed it, but AP-32 was reverted because its lines on vague phrases didn't cut vague references on Opus 5.5, and the author is fine with vague references: the target is metaphors such as "lands". Does listing "hold up" and "turn up" on their own cut them? (AP-33)

## Found

The Name things list gained two lines: "hold up" (wait on, or keep from starting) and "turn up" (find or show). The release cases (`release-status`, `next-step`, `merge-today`) ran 6 times each with the plugin, on Claude Code 2.1.326 with Sonnet 5.5 judging. The 0.2.0 columns are the release-case replies from the AP-30 and AP-32 runs, 9 per case.

| Release cases, with the plugin | Opus 0.2.0 | Opus 0.2.1 | Fable 0.2.0 | Fable 0.2.1 |
| --- | --- | --- | --- | --- |
| Replies | 27 | 18 | 27 | 18 |
| "hold up", "holding back" | 11 | 2 | 7 | 0 |
| "turn up" | 1 | 0 | 2 | 0 |
| "settle", "bottleneck", "make the date", "land", "carry", "unblock", "pick up" | 4 | 2 | 1 | 0 |
| No metaphor verbs (grader) | 13 | 9 | 16 | 13 |
| No cleft sentences (grader) | 17 | 8 | 16 | 17 |
| Right answer (grader) | 24 | 17 | 27 | 18 |

- The two listed phrases fell on both models. Opus still wrote "holding up" and "holds up" once each in 18 replies.
- No other counted metaphor rose. The metaphor-verb grader stayed level on Opus (13 of 27, then 9 of 18) and rose on Fable. The Opus replies it still fails use milder ones, such as "if #33 slips past today" and "the receipt check was added on the side".
- On Opus, fewer replies passed the cleft-sentence grader. Most of the sentences it failed use plain verbs and name the PR: "PR #33 is the item everything else waits on" and "PR #33 is the only thing keeping T-13 and T-14 from finishing". Two kept the "X is what Y" form the style already lists, such as "a failing macOS test on PR #33 is what keeps the rest from moving". AP-32's run, which also listed "hold up", showed the same drop, to 9 of 27.
- One Opus reply hedged with "should work".
- The runs cost $8.55: $3.26 on Opus and $5.29 on Fable.

## What came of it

- The two lines ship in plain-english 0.2.1. PROJECT.md's Decisions records it.
- The eval suite dropped its vague-reference grader, and its stand-in regex and `stats.py` count "hold up" and "turn up".
