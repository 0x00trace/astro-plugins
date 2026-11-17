# What the Plain English style changes

Does plain-english change how Claude writes, and do passages from professional writers, added to the style as examples, make it better? (AP-21, AP-22)

## Found

The plugin's eval suite (`plugins/plain-english/evals/`, PR #123) ran twice: once on 0.1.0 and once with the passages added (commit 39836e6). Each run had 6 writing cases, with 3 runs per case with the plugin and 3 without. Claude Opus 5.5 wrote the replies on Claude Code 2.1.326, and Sonnet 5.5 judged them. The counts come from `evals/stats.py` over the 18 replies in each arm. In the no-plugin column, the first number is from the 0.1.0 run and the second from the passages run.

| Over 18 replies | No plugin | 0.1.0 | 0.1.0 with the passages |
| --- | --- | --- | --- |
| Mean words per reply | 195, 191 | 143 | 159 |
| Hedges on the style's list | 3, 5 | 0 | 0 |
| Hedge-like words ("should", "may", "I'd expect") | 20, 16 | 8 | 5 |
| Filler words | 3, 3 | 0 | 0 |
| Bold spans | 54, 51 | 12 | 21 |
| Right answers | 18, 16 | 18 | 18 |
| Em dashes, buzzwords, openers and closers | 0, 0 | 0 | 0 |

- 0.1.0 changes the writing. Asked "Does this work on Windows?" without the plugin, Claude opened with "Probably yes, but nobody has tested it there", "I can't say for sure" and "I don't know for sure", then wrote "I'd expect it to work". With the plugin, all three runs opened with "Nobody has run it on Windows yet". Each said once that it couldn't run Windows there, and gave the command that would settle it.
- Without the plugin, Opus 5.5 already wrote no em dashes, buzzwords, openers or closers in these cases.
- The passages were three from "Fixing For Loops in Go 1.22" (David Chase and Russ Cox) and four from "crates.io Postmortem: Broken Crate Downloads" (Tobias Bieniek). They made replies 11% longer and raised bold from 12 to 21 spans. Between its two runs, the no-plugin arm moved by 4 words and 3 bold spans, so both changes are larger than run-to-run noise. Hedge-like words fell from 8 to 5, which is within the no-plugin arm's spread of 4.
- Of the 8 hedge-like words with 0.1.0, 5 are "should" meaning "ought to" ("10 items should qualify"). One is a hedge: "That should make the test pass."
- The cases are one-turn questions about a small Python fixture, graded on Claude's final reply. They don't cover long sessions, subagent reports or thinking text.

## What came of it

- The passages came back out of the style (AP-26), and plain-english stays at 0.1.0 (AP-27 cancelled). PROJECT.md's Decisions records this.
- To test another change to the style, run the suite as the plugin's README says and compare `evals/stats.py`'s counts with this table.
