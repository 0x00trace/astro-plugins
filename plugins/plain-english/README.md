# plain-english

Makes Claude write in plain English, the way good technical docs read: the answer first, short sentences, common words, and the actual file, command or number named. It leaves out hedging ("I think", "probably", "should work"), filler ("just", "really", "it's worth noting"), openers and closers ("Great question", "Hope this helps"), buzzwords and em dashes. The rules apply to everything Claude writes: replies, plans, code comments, commit messages, docs and subagent reports. They're in [`output-styles/plain-english.md`](output-styles/plain-english.md), which ends with passages from a Go blog post and a crates.io postmortem as examples of the writing it asks for.

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

`evals/` holds seven [`claude plugin eval`](https://code.claude.com/docs/en/plugin-evals) cases, and each runs with and without the plugin. `style-loads` checks that an eval run gets the output style. The other six copy `evals/fixtures/shop` into an empty folder and ask a question about it. The fixture is a small Python cart with one planted bug: the bulk discount starts at 11 items, while its docstring and test say 10.

| Case | Prompt | The answer is right when it |
| --- | --- | --- |
| `style-loads` | Quote the style's first sentence | quotes it (only with the plugin) |
| `failing-test` | Why does `test_ten_items_get_bulk_discount` fail? | names the `qty > BULK_QTY` comparison |
| `review-diff` | Will `rename.diff` break anything? | names `shop/receipt.py`, which still imports `line_total` |
| `pick-one` | JSON or pickle for saving carts? | picks one and says why |
| `windows` | Does this work on Windows? | says what it checked, that nobody has run it on Windows, and how to find out |
| `commit-message` | Write a commit message for `fix.diff` | says the discount now starts at 10 items |
| `status` | Where does this project stand? | names the failing test and the two open TODO items |

Each of the six has an `llm` grader for the right answer and five `regex` graders, one for each word list in the style: hedges, filler, buzzwords, openers and closers, and em dashes. A `regex` grader fails a run on one match in Claude's last message. The five live in `evals/style-graders/`, and each case links to them.

```
mkdir -p "$HOME/.cache/claude-plugin-eval"
TMPDIR="$HOME/.cache/claude-plugin-eval" claude plugin eval plugins/plain-english --scaffold --allow-tools Bash --judge-model claude-sonnet-5-5 --keep-temp -j 4 --threshold 0 --json plugins/plain-english/evals/results/run.json
python3 plugins/plain-english/evals/stats.py plugins/plain-english/evals/results/run.json
```

- `--scaffold` lets each case copy the fixture into its folder, and `--allow-tools Bash` lets Claude run the fixture's tests.
- `TMPDIR` moves the run folders out of `/tmp`, where the eval sandbox denies Bash writes.
- `--keep-temp` keeps each run's `trace.jsonl` under `$TMPDIR/claude-eval-*/out/`. The results JSON has the grader verdicts but not Claude's replies, and `stats.py` reads the replies from the traces.
- `--threshold 0` keeps the exit code at 0, since the run is a measurement, not a gate.
- `stats.py` counts words, hedges, filler and bold in each reply. With the plugin, every grader passes in all 18 writing runs, so the counts show differences the pass/fail graders can't.
- On Claude Opus 5.5 with Claude Code 2.1.326, a run of the whole suite costs about $5.50 and takes about 3 minutes.
- Results go to `evals/results/`, which git ignores.

## Credits

The style's examples quote two posts, unchanged apart from the cuts:

- "[Fixing For Loops in Go 1.22](https://go.dev/blog/loopvar-preview)" by David Chase and Russ Cox, on the Go blog, under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- "[crates.io Postmortem: Broken Crate Downloads](https://blog.rust-lang.org/inside-rust/2023/07/21/crates-io-postmortem/)" by Tobias Bieniek, on the Rust blog, under the [MIT](https://github.com/rust-lang/blog.rust-lang.org/blob/main/LICENSE-MIT) or [Apache-2.0](https://github.com/rust-lang/blog.rust-lang.org/blob/main/LICENSE-APACHE) license.
