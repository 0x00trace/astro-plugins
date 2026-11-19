# Basing the style on ISO 24495-1

The author wants Claude's prose in a professional, neutral tone, and replaced plain-english's rules with a definition of plain language from ISO 24495-1:2023 (commit f56ed8a). The definition says what plain language is but doesn't tell Claude to write it. Does a style built on the standard change how Claude writes, and does turning the definition into instructions do more? (#163)

## Found

The 0.3.0 text turns the definition into instructions. It says who the readers are, asks for a professional, neutral tone, and gives the standard's four principles with guidelines adapted from its clauses, such as "Project a respectful tone" (5.3.7). A new `professional-tone` grader fails a reply for slang, jokes, exclamation marks, emoji, flattery, colloquial idioms or alarm.

The nine writing cases ran twice each on Claude Code 2.1.327 and Opus 5.5, with Sonnet 5.5 judging. The 0.2.0 column is the AP-30 run on 2.1.326, three runs each, which had no tone grader.

| | No plugin | f56ed8a text | 0.3.0 text | 0.2.0 rules |
| --- | --- | --- | --- | --- |
| Replies | 18 | 18 | 18 | 27 |
| Right answer (grader) | 18 | 18 | 18 | 27 |
| Professional tone (grader) | 16 | 18 | 18 | not run |
| Contractions per 1,000 words | 18.0 | 10.7 | 2.8 | 12.1 |
| Markdown headings | 0 | 24 | 23 | 0 |
| Mean words per reply | 231 | 233 | 242 | 192 |
| Hedges | 8 | 5 | 4 | 0 |
| No metaphor verbs (grader) | 8 | 8 | 10 | 17 |
| No cleft sentences (grader) | 13 | 14 | 17 | 21 |
| Stand-in words | 7 | 4 | 3 | 2 |

- Opus 5.5 already writes in a mostly professional tone. The tone grader failed 2 of 18 replies without the plugin. The judge gave no reason, and the two replies use idioms such as "slip the date" and "tick off".
- The clearest change is register. Contractions fell by 40% with the f56ed8a text and by 85% with the 0.3.0 text, which wrote "do not" or "cannot" 38 times against 2 without the plugin. Offers such as "Want me to do that?" fell from 3 to 0.
- Both ISO texts add `##` headings and tables to the status, release-status, next-step and merge-today replies, of about 300 words each. The 0.3.0 line "Use headings and lists only when they help the reader scan a longer text" didn't reduce them.
- Neither ISO text shortens replies, removes hedges or cuts dead metaphors as the 0.2.0 rules did. The metaphor-verb grader stayed at the level with no plugin.
- With 18 replies a column, a difference of 1 to 3 replies is within noise. The changes in contractions and headings are large enough to count.
- The runs cost $11.95: $8.09 for no plugin and the f56ed8a text, and $3.86 for the 0.3.0 text.

## What came of it

- The 0.3.0 text ships in plain-english 0.3.0, and PROJECT.md's Decisions records it. The eval suite keeps the `professional-tone` grader, and `stats.py` counts contractions and headings.
- PROJECT.md's Open questions holds two questions: whether to bring back the 0.2.0 list of stand-ins, which cut dead metaphors, and whether to rule out headings in short replies.
