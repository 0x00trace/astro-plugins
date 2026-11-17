# What the Name things rule changes

Does a list of stand-ins, each with the plain word to use instead, cut the stand-ins in Claude's status and plan text better than the general rule it replaces? A stand-in is a word that takes the place of the thing or action the reader needs: "the work", "land" for merge, "carry" for include. (AP-28, AP-30)

## Found

The suite ran on 0.1.0 and on the Name things section (AP-30), on Claude Opus 5.5 and Claude Fable 5.2. It had nine writing cases, with 3 runs per case with the plugin and 3 without, on Claude Code 2.1.326, and Sonnet 5.5 judged. Three cases (AP-29) ask for status and next steps on a release described in files. The table counts replies, of 27, that pass each grader with the plugin. The last two rows are totals from `evals/stats.py`.

| With the plugin | Opus 0.1.0 | Opus rewrite | Fable 0.1.0 | Fable rewrite |
| --- | --- | --- | --- | --- |
| No metaphor verbs | 17 | 22 | 15 | 21 |
| No stand-in words (regex) | 26 | 27 | 22 | 27 |
| No cleft sentences | 23 | 25 | 24 | 23 |
| No vague references (first rubric) | 6 | 5 | 8 | 7 |
| No hedges | 26 | 27 | 27 | 27 |
| Right answer | 24 | 26 | 26 | 27 |
| Stand-in words, all replies | 1 | 0 | 5 | 0 |
| Mean words per reply | 189 | 184 | 175 | 179 |

- The list works for what it names. Metaphor verbs fell on both models. Between the same two runs, the no-plugin arm moved by 1 on Opus and 3 on Fable, so the gains of 5 and 6 are larger than run-to-run noise. The listed words dropped to 0 on both models.
- 0.1.0's general rule did little against them. On Opus, 17 of 27 replies had no metaphor verb with 0.1.0, against 13 without the plugin.
- Vague references didn't change, but the first rubric couldn't show a change. It failed any pronoun whose thing wasn't named in the same or the previous sentence, including "Nobody has run it on Windows" in answer to "Does this work on Windows?". AP-30 rewrote the rubric after these runs. The new one fails general phrases and ambiguous nouns, and on three rewrite replies it failed the two that had them and passed the third.
- The rewrite still leaves stand-ins its list doesn't name: "PR #33 holds up everything left", "Everything else for 1.4 waits on PR #33", "The other option is to resolve `folder` when the test creates it", and "push the change" after two changes come up.
- Hedges, filler, length and bold didn't get worse.
- The four runs cost $10.28 and $10.42 on Opus, and $20.02 and $18.97 on Fable.

## What came of it

- The Name things section ships in plain-english 0.2.0 (AP-31). PROJECT.md's Decisions records it.
- AP-32 covers the vague references the list leaves, starting with a baseline under the new rubric, since the numbers above came from the first one.
