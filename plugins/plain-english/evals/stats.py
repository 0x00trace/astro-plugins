"""Count words, hedges, filler and bold in each reply of a `claude plugin eval` run.

The eval's regex graders pass or fail a reply on one match. This counts the matches, which shows a
difference between two runs that both pass every grader. It reads the replies from each run's
trace.jsonl, which the eval keeps only with --keep-temp.

    python3 evals/stats.py evals/results/<name>.json
"""

import json
import re
import sys
from pathlib import Path
from statistics import mean

# The list evals/style-graders/no-hedges.md checks: the style's own, plus "I believe", "I suspect",
# "seems to", "appears to", "possibly" and "presumably".
HEDGES = re.compile(
    r"\b(I think|I believe|I suspect|it seems|seems to|it appears|appears to|probably|likely|might"
    r"|perhaps|arguably|possibly|presumably|should work)\b",
    re.IGNORECASE,
)
# Words that hedge in some sentences and not in others, such as "should" in "10 items should
# qualify". Compare this count between runs rather than reading each match as a hedge.
HEDGE_LIKE = re.compile(
    r"\b(I'd expect|I would expect|for sure|I can't say|should|may|could|generally|typically)\b",
    re.IGNORECASE,
)
FILLER = re.compile(
    r"\b(just|simply|actually|basically|really|very|quite|honestly|genuinely|essentially)\b",
    re.IGNORECASE,
)
COLUMNS = ("runs", "words", "hedges", "hedge-like", "filler", "bold")


def final_reply(trace_path):
    """Return the run's final reply, or None when its trace wasn't kept."""
    if not trace_path or not Path(trace_path).exists():
        return None
    reply = ""
    for line in Path(trace_path).read_text(encoding="utf-8").splitlines():
        try:
            message = json.loads(line)
        except ValueError:
            continue
        if message.get("type") == "result" and message.get("result"):
            reply = message["result"]
    return reply


def counts(replies):
    return (
        len(replies),
        round(mean(len(r.split()) for r in replies)),
        sum(len(HEDGES.findall(r)) for r in replies),
        sum(len(HEDGE_LIKE.findall(r)) for r in replies),
        sum(len(FILLER.findall(r)) for r in replies),
        sum(r.count("**") // 2 for r in replies),
    )


def main(path):
    result = json.loads(Path(path).read_text(encoding="utf-8"))
    rows, every, missing = [], {}, 0
    for case in result["cases"]:
        if case["name"] == "style-loads":
            continue
        for arm, runs in case["arms"].items():
            replies = [final_reply(run["tracePath"]) for run in runs]
            missing += replies.count(None)
            replies = [r for r in replies if r is not None]
            if replies:
                rows.append((case["name"], arm, counts(replies)))
                every.setdefault(arm, []).extend(replies)
    rows += [("all", arm, counts(replies)) for arm, replies in every.items()]
    print(f"{'case':16}{'arm':9}" + "".join(f"{c:>11}" for c in COLUMNS))
    for name, arm, row in rows:
        print(f"{name:16}{arm:9}" + "".join(f"{v:>11}" for v in row))
    print("\nwords is the mean per reply; the other counts are totals over the runs.")
    if missing:
        print(
            f"{missing} runs had no trace. Run the eval with --keep-temp to keep them."
        )


if __name__ == "__main__":
    main(sys.argv[1])
