"""End-to-end answer-quality eval: runs every question through the real pipeline, then scores it.

    python eval_answers.py               # all questions
    python eval_answers.py --limit 10    # quick smoke run

Metrics
  Answerable questions
    accuracy          LLM judge: answer matches the reference answer (yes=1, partial=0.5, no=0)
    faithfulness      LLM judge: every claim is supported by the retrieved passages (no hallucination)
    citation accuracy deterministic: at least one cited chunk is the expected source + contains the expected text
    false refusals    answered "I don't know" although the docs contain the answer
  Unanswerable questions
    correct refusals  answered "I don't know" (anything else is a hallucination)
  Latency             p50 / p95 of the full pipeline per question

The judge model is JUDGE_MODEL (defaults to CHAT_MODEL). Judging with the same model that answered
can be lenient; set JUDGE_MODEL to a stronger model for a stricter grade.
Writes results/answers.jsonl and results/answer_eval.md.
"""

import argparse
import json
import math
import statistics
import time

from rag import config, llm
from rag.evalset import RESULTS, is_hit, load_cases, md_table, utf8_stdout
from rag.pipeline import answer_question, is_refusal

JUDGE_SYSTEM = """You grade answers from a documentation chatbot. Reply with JSON only:
{"correct": "yes" | "partial" | "no", "faithful": true | false, "reason": "<one sentence>"}

- correct: does the ANSWER convey the same facts as the REFERENCE? Extra correct detail is fine.
  "partial" if some key facts are missing or slightly off; "no" if wrong, missing, or a refusal.
- faithful: is every factual claim in the ANSWER supported by the PASSAGES? Ignore citation markers
  like [1]. A refusal ("I don't know") counts as faithful."""


def judge(question: str, reference: str, answer: str, passages: list[dict]) -> dict:
    ctx = "\n\n".join(f"[{p['n']}] {p['snippet']}" for p in passages) or "(none)"
    user = f"QUESTION: {question}\n\nREFERENCE: {reference}\n\nANSWER: {answer}\n\nPASSAGES:\n{ctx}"
    raw = llm.complete(JUDGE_SYSTEM, user, model=config.JUDGE_MODEL, json_mode=True)
    try:
        out = json.loads(raw[raw.find("{") : raw.rfind("}") + 1])
        return {"correct": str(out.get("correct", "no")).lower(), "faithful": bool(out.get("faithful")),
                "reason": out.get("reason", "")}
    except json.JSONDecodeError:
        return {"correct": "no", "faithful": False, "reason": f"unparseable judge output: {raw[:120]}"}


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="evals.json")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--delay", type=float, default=0.0, help="seconds between questions (rate limits)")
    args = ap.parse_args()

    cases = load_cases(args.file)[: args.limit]
    RESULTS.mkdir(exist_ok=True)
    records = []
    score = {"yes": 1.0, "partial": 0.5, "no": 0.0}

    print(f"{'#':>3}  {'type':<5} {'result':<18} {'sec':>5}  question")
    print("-" * 90)
    for i, case in enumerate(cases, start=1):
        t0 = time.perf_counter()
        res = answer_question(case["question"])
        latency = time.perf_counter() - t0
        refused = is_refusal(res["answer"])
        rec = {"question": case["question"], "answerable": case["answerable"], "answer": res["answer"],
               "refused": refused, "latency_s": round(latency, 2),
               "cited": [f"{c['source']}#{c['chunk_index']}" for c in res["citations"]]}

        if case["answerable"]:
            rec["citation_ok"] = any(is_hit({"source": c["source"], "content": c["snippet"]}, case)
                                     for c in res["citations"])
            if refused:
                # A refusal on an answerable question is wrong but not a hallucination; no judge call needed.
                rec.update({"correct": "no", "faithful": True, "reason": "refused although the docs contain the answer"})
            else:
                # Judge faithfulness against everything the model saw, not just what it cited.
                rec.update(judge(case["question"], case["answer"], res["answer"], res["retrieved"]))
            result = "REFUSED" if refused else f"{rec['correct']}{'' if rec['faithful'] else ' UNFAITHFUL'}"
            kind = "ans"
        else:
            result = "correct IDK" if refused else "HALLUCINATED"
            kind = "unans"
        records.append(rec)
        print(f"{i:>3}  {kind:<5} {result:<18} {latency:>5.1f}  {case['question'][:55]}")
        time.sleep(args.delay)

    with open(RESULTS / "answers.jsonl", "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    pos = [r for r in records if r["answerable"]]
    neg = [r for r in records if not r["answerable"]]
    lat = sorted(r["latency_s"] for r in records)
    metrics = []
    if pos:
        metrics += [
            {"metric": "Answer accuracy (judge)", "value": f"{sum(score.get(r['correct'], 0) for r in pos) / len(pos):.0%}", "n": len(pos)},
            {"metric": "Faithfulness (judge)", "value": f"{sum(r['faithful'] for r in pos) / len(pos):.0%}", "n": len(pos)},
            {"metric": "Citation accuracy", "value": f"{sum(r['citation_ok'] for r in pos) / len(pos):.0%}", "n": len(pos)},
            {"metric": "False refusals", "value": f"{sum(r['refused'] for r in pos) / len(pos):.0%}", "n": len(pos)},
        ]
    if neg:
        metrics.append({"metric": "Correct refusals on unanswerable", "value": f"{sum(r['refused'] for r in neg) / len(neg):.0%}", "n": len(neg)})
    if lat:
        p95 = lat[min(len(lat) - 1, math.ceil(0.95 * len(lat)) - 1)]
        metrics.append({"metric": "Latency p50 / p95", "value": f"{statistics.median(lat):.1f}s / {p95:.1f}s", "n": len(lat)})

    table = md_table(metrics, ["metric", "value", "n"])
    print("-" * 90)
    print(table)

    failures = [r for r in records if (r["answerable"] and (r["correct"] != "yes" or not r["faithful"]))
                or (not r["answerable"] and not r["refused"])]
    fail_md = "\n".join(
        f"- **{r['question']}**: {'refused' if r['refused'] else r.get('correct', 'hallucinated')}"
        f"{'' if r.get('faithful', True) else ', unfaithful'}. {r.get('reason', '')}\n  > {r['answer'][:300]}"
        for r in failures) or "None."

    (RESULTS / "answer_eval.md").write_text(
        f"# Answer-quality eval\n\nProvider `{config.PROVIDER}` · chat `{config.CHAT_MODEL}` · judge `{config.JUDGE_MODEL}` · "
        f"retrieval `{config.RETRIEVAL_MODE}` k={config.TOP_K} · MIN_SIMILARITY={config.MIN_SIMILARITY} · "
        f"chunks {config.CHUNK_TOKENS}/{config.CHUNK_OVERLAP}\n\n{table}\n\n## Failures\n\n{fail_md}\n\n"
        f"Per-question detail: `results/answers.jsonl`.\n",
        encoding="utf-8",
    )
    print("\nReport: results/answer_eval.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
