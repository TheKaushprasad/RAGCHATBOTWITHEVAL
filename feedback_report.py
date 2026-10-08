"""Summarise thumbs up / down feedback from the chat, and turn bad answers into eval cases.

    python feedback_report.py                                   # summary + every thumbs-down
    python feedback_report.py --export golden_candidates.json   # thumbs-downs as golden-dataset drafts

Exported entries match evals_golden.json, with an empty "answer" for you to write the correct
golden answer (the bot's reply and the user's comment are included for reference). Review them,
then append the good ones to evals_golden.json so the next eval run covers real user failures.
"""

import argparse
import json
from collections import Counter

from rag import store
from rag.evalset import md_table, utf8_stdout


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", metavar="FILE", help="write thumbs-down answers as golden-dataset candidates")
    ap.add_argument("--limit", type=int, default=1000)
    args = ap.parse_args()

    rows = store.list_feedback(limit=args.limit)
    if not rows:
        print("No feedback yet.")
        return 0

    votes = Counter(r["rating"] for r in rows)
    up, down = votes.get(1, 0), votes.get(-1, 0)
    refusals = [r for r in rows if r["grounded"] is False]
    print(f"Feedback: {len(rows)} rated answers · 👍 {up} · 👎 {down} · helpful rate {up / len(rows):.0%}")
    if refusals:
        r_down = sum(r["rating"] == -1 for r in refusals)
        print(f"\"I don't know\" answers: {len(refusals)} rated, {r_down} thumbs-down "
              "(a thumbs-down here usually means the docs should have covered it)")

    configs = Counter(json.dumps({k: r["config"].get(k) for k in ("chat_model", "retrieval_mode", "top_k")},
                                 sort_keys=True) for r in rows)
    if len(configs) > 1:
        print("\nBy config:")
        for cfg, n in configs.most_common():
            sub = [r for r in rows if json.dumps({k: r["config"].get(k) for k in ("chat_model", "retrieval_mode", "top_k")}, sort_keys=True) == cfg]
            print(f"  {cfg}: {n} rated, helpful {sum(r['rating'] == 1 for r in sub) / n:.0%}")

    bad = [r for r in rows if r["rating"] == -1]
    if bad:
        print(f"\nThumbs-down ({len(bad)}):\n")
        print(md_table([{
            "when": r["created_at"][:16].replace("T", " "),
            "question": r["question"][:70],
            "comment": (r["comment"] or "")[:60],
            "cited": ", ".join(f"{s['source']}" + (f" p{s['page']}" if s.get("page") else "") for s in r["sources"])[:40] or "-",
        } for r in bad], ["when", "question", "comment", "cited"]))

    if args.export:
        candidates = [{
            "id": f"FB{i:03d}",
            "topic": "From user feedback",
            "type": "unknown",
            "difficulty": "unknown",
            "question": r["question"],
            "answer": "",
            "answerable": True,
            "expected_sources": [],
            "bot_answer": r["answer"],
            "user_comment": r["comment"],
        } for i, r in enumerate(bad, start=1)]
        with open(args.export, "w", encoding="utf-8") as f:
            json.dump(candidates, f, ensure_ascii=False, indent=1)
        print(f"\nWrote {len(candidates)} candidates to {args.export}. Fill in each \"answer\" (and set "
              "\"answerable\": false where the docs truly don't cover it) before adding them to evals_golden.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
