# plain-english

Makes Claude write plain language as [ISO 24495-1:2023](https://www.iso.org/standard/78907.html) defines it, in a professional, neutral tone: text whose readers can easily find what they need, understand what they find and use that information. The style names Claude's readers, asks for the tone of good technical documentation (courteous and matter-of-fact, with no slang, jokes, exclamation marks, emoji or flattery), and gives the standard's four principles with their guidelines: relevant, findable, understandable and usable. That means the most important message first, familiar and literal words ("merge", not "land"), each thing called by its name, and short sentences and paragraphs. It applies to everything Claude writes: replies, plans, code comments, commit messages, docs and subagent reports. The text is in [`output-styles/plain-english.md`](output-styles/plain-english.md).

```
/plugin install plain-english --marketplace astrosteveo/astro-plugins
```

## Where the instructions reach

| Where Claude writes | How it gets the instructions |
| --- | --- |
| The main conversation, including `claude -p` and a session resumed with `--fork-session` | The Plain English output style, which turns itself on (`force-for-plugin`) |
| A fork (`subagent_type: fork`) | The output style, in the system prompt the fork inherits |
| Every other subagent: Explore, Plan, general-purpose, a plugin's agents, workflow agents | The same text as `SubagentStart` context, from the hooks module |
| An agent-team teammate | Both: its lead's system prompt and `SubagentStart` context |

A subagent other than a fork runs on its own system prompt, which leaves out the output style. That's why the hook hands it the text. A teammate gets it twice, because the hook names a teammate by the name it was given and can't tell it apart from a subagent.

## What it changes

While the plugin is enabled, Plain English replaces any output style you pick in `/config` or with `/output-style`. To go back to another style, disable the plugin. The style keeps Claude Code's software engineering instructions (`keep-coding-instructions: true`).

Claude Code reads output style files when it starts, so after editing `plain-english.md`, restart Claude Code. Subagents read the file each time one starts.

## Check it

In a session with the plugin enabled, ask:

```
Use no tools. Quote the first sentence of the Writing style section of your system prompt exactly, or reply: none.
```

Claude answers with the first sentence of the style. Ask a subagent the same thing, such as "Spawn an Explore subagent with this task: …", and it gives the same answer. Each subagent's transcript in `~/.claude/projects/<project>/<session>/subagents/` holds the text as a `hook_additional_context` row from `SubagentStart`.

```
claude plugin validate plugins/plain-english
claude plugin test plugins/plain-english
python3 -m unittest discover -s plugins/plain-english/tests
```

### Evals

`evals/` holds ten [`claude plugin eval`](https://code.claude.com/docs/en/plugin-evals) cases, and each runs with and without the plugin. `style-loads` checks that an eval run gets the output style. The other nine copy a fixture into an empty folder and ask a question about it:

- `evals/fixtures/shop` is a small Python cart with one planted bug: the bulk discount starts at 11 items, while its docstring and test say 10.
- `evals/fixtures/release` describes a release in progress: a task list, two open pull requests and the CI log of a test that fails on macOS. Its questions ask for status and next steps, where stand-ins such as "the work" or "once it lands" show up.

| Case | Prompt | The answer is right when it |
| --- | --- | --- |
| `style-loads` | Quote the style's first sentence | quotes it (only with the plugin) |
| `failing-test` | Why does `test_ten_items_get_bulk_discount` fail? | names the `qty > BULK_QTY` comparison |
| `review-diff` | Will `rename.diff` break anything? | names `shop/receipt.py`, which still imports `line_total` |
| `pick-one` | JSON or pickle for saving carts? | picks one and says why |
| `windows` | Does this work on Windows? | says what it checked, that nobody has run it on Windows, and how to find out |
| `commit-message` | Write a commit message for `fix.diff` | says the discount now starts at 10 items |
| `status` | Where does this project stand? | names the failing test and the two open TODO items |
| `release-status` | Where does the 1.4 release stand? | names each task and PR and what each waits on |
| `next-step` | What should I do next to get 1.4 out? | starts with the macOS test failure in PR #33 |
| `merge-today` | Can we merge #33 today? | says no, names `test_write_receipt` and its cause, and says how to fix it |

Each of the nine has an `llm` grader for the right answer, plus eight graders for the style. They live in `evals/style-graders/`, and each case links to them:

- Six `regex` graders, one for each word list: hedges, filler, buzzwords, openers and closers, em dashes, and stand-in words such as "land", "carry", "hold up" and "the work". A `regex` grader fails a run on one match in Claude's last message.
- Two `llm` graders, one for each kind of stand-in the word lists can't catch: a metaphor verb ("goes green" for passes) and a cleft sentence ("The next task is what carries the rest of the work").

```
mkdir -p "$HOME/.cache/claude-plugin-eval"
TMPDIR="$HOME/.cache/claude-plugin-eval" claude plugin eval plugins/plain-english --scaffold --allow-tools Bash --judge-model claude-sonnet-5-5 --keep-temp -j 4 --threshold 0 --json plugins/plain-english/evals/results/run.json
python3 plugins/plain-english/evals/stats.py plugins/plain-english/evals/results/run.json
```

- `--scaffold` lets each case copy the fixture into its folder, and `--allow-tools Bash` lets Claude run the fixture's tests.
- `TMPDIR` moves the run folders out of `/tmp`, where the eval sandbox denies Bash writes.
- `--keep-temp` keeps each run's `trace.jsonl` under `$TMPDIR/claude-eval-*/out/`. The results JSON has the grader verdicts but not Claude's replies, and `stats.py` reads the replies from the traces.
- `--threshold 0` keeps the exit code at 0, since the run is a measurement, not a gate.
- `stats.py` counts words, hedges, filler, bold and stand-in words in each reply. A grader passes or fails a whole reply, so the counts show differences between two runs that the graders can't.
- Add `--model claude-fable-5-2` or another model ID to test the style on that model.
- With Claude Code 2.1.326, a run of the whole suite costs about $10 on Claude Opus 5.5 and about $20 on Claude Fable 5.2, and takes about 7 minutes on either.
- Results go to `evals/results/`, which git ignores.
