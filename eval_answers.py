"""End-to-end answer-quality eval: runs every question through the real pipeline, then grades it
against the reference ("golden") answer.

    python eval_answers.py                                       # AI PM golden dataset (evals_golden.json)
    python eval_answers.py --limit 10                            # quick smoke run
    python eval_answers.py --file examples/tidepool/evals.json   # archived Tidepool case study
    TOP_K=5 python eval_answers.py --out results/golden-k5       # experiment without overwriting the baseline
    python eval_answers.py --report-only                         # rebuild the report from saved answers
    python eval_answers.py --file evals_followup.json            # follow-up questions (rewritten using history)
    python eval_answers.py --file evals_followup.json --no-rewrite --out results/followup-norewrite  # baseline

Each question is graded by an LLM judge that sees the question, the golden answer, the bot's answer
and the passages the bot retrieved. It returns three grades:

  correctness     does the bot's answer convey the facts in the golden answer?   yes / partial / no
  faithfulness    is every claim in the bot's answer supported by the retrieved passages? (no hallucination)
  context recall  do the retrieved passages contain the facts needed for the golden answer?   yes / partial / no

plus deterministic checks: refusals ("I don't know"), whether the answer cites anything, citation
accuracy (when the case has an expected_substring), semantic similarity between the bot's answer and the
golden answer (embedding cosine), and latency.

Context recall vs correctness splits every failure into a cause:
  retrieval miss        the passages didn't contain the answer            → fix chunking / search
  incomplete retrieval  the passages held only part of the answer         → retrieve more (k) / bigger chunks
  generation miss       the passages had it all, the answer didn't use it → fix the prompt / model
  false refusal     said "I don't know" although the docs answer it
Out-of-scope questions (answerable: false) are graded on whether the bot followed the expected behaviour
in the golden answer (decline without inventing facts).

Results go to results/<eval set>/ (e.g. results/golden/), or examples/<x>/results/ for archived sets:
answers.jsonl (per question) and answer_eval.md (summary, breakdowns by topic/type/difficulty, failures).
The judge is JUDGE_MODEL (defaults to CHAT_MODEL); a stronger judge grades more strictly.
"""

import argparse
import json
import math
import statistics
import time
from collections import defaultdict
from pathlib import Path

from rag import config, followup, llm
from rag.embeddings import embed_documents
from rag.evalset import DEFAULT_EVALS, is_hit, load_cases, md_table, results_dir, utf8_stdout
from rag.pipeline import answer_question, is_refusal

SCORE = {"yes": 1.0, "partial": 0.5, "no": 0.0}

JUDGE_ANSWERABLE = """You grade a documentation chatbot against a golden answer. Reply with JSON only:
{"correct": "yes"|"partial"|"no", "faithful": true|false, "context_recall": "yes"|"partial"|"no", "reason": "<one sentence>"}

- correct: does the ANSWER convey the key facts of the GOLDEN ANSWER? Wording can differ; extra correct
  detail is fine. "partial" if some key facts are missing or slightly off; "no" if wrong, missing or a refusal.
- faithful: is every factual claim in the ANSWER supported by the PASSAGES? Ignore citation markers like [1].
  A refusal counts as faithful.
- context_recall: do the PASSAGES (not the answer) contain the information needed to write the GOLDEN ANSWER?
  "partial" if only some of it is there."""

JUDGE_OUT_OF_SCOPE = """You grade a documentation chatbot on a question its knowledge base does NOT cover.
The EXPECTED BEHAVIOUR says how it should respond (typically: say the information isn't available rather
than guess; it may briefly mention related facts that ARE in the passages). Reply with JSON only:
{"correct": "yes"|"partial"|"no", "faithful": true|false, "reason": "<one sentence>"}

- correct: "yes" if the ANSWER follows the expected behaviour; "partial" if it declines but also adds
  unsupported claims; "no" if it answers the question with information not in the passages.
- faithful: is every factual claim in the ANSWER supported by the PASSAGES? Ignore citation markers like [1]."""


def judge(case: dict, answer: str, passages: list[dict]) -> dict:
    ctx = "\n\n".join(f"[{p['n']}] {p['snippet']}" for p in passages) or "(none)"
    if case["answerable"]:
        system, label = JUDGE_ANSWERABLE, "GOLDEN ANSWER"
    else:
        system, label = JUDGE_OUT_OF_SCOPE, "EXPECTED BEHAVIOUR"
    user = f"QUESTION: {case['question']}\n\n{label}: {case['answer']}\n\nANSWER: {answer}\n\nPASSAGES:\n{ctx}"
    raw = llm.complete(system, user, model=config.JUDGE_MODEL, json_mode=True)
    try:
        out = json.loads(raw[raw.find("{") : raw.rfind("}") + 1])
    except json.JSONDecodeError:
        return {"correct": "no", "faithful": False, "context_recall": "no", "reason": f"unparseable judge output: {raw[:120]}"}
    grade = {
        "correct": str(out.get("correct", "no")).lower(),
        "faithful": bool(out.get("faithful")),
        "reason": out.get("reason", ""),
    }
    if case["answerable"]:
        grade["context_recall"] = str(out.get("context_recall", "no")).lower()
    return grade


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))  # embeddings are already unit-normalised


def diagnose(r: dict) -> str:
    if not r["answerable"]:
        return "ok" if r["correct"] == "yes" else "out-of-scope: invented an answer"
    if r["correct"] == "yes" and r["faithful"]:
        return "ok"
    if r["refused"]:
        return "false refusal" if r["context_recall"] != "no" else "refusal (retrieval miss)"
    if not r["faithful"]:
        return "hallucination"
    if r["context_recall"] == "no":
        return "retrieval miss"  # the answer wasn't in the retrieved passages at all
    if r["context_recall"] == "partial":
        return "incomplete retrieval"  # only part of the answer was retrieved, so the answer is incomplete
    return "generation miss"  # everything needed was retrieved; the model didn't use it


def pct(xs: list[float]) -> str:
    return f"{sum(xs) / len(xs):.0%}" if xs else "n/a"


def summarize(rows: list[dict]) -> dict:
    pos = [r for r in rows if r["answerable"]]
    return {
        "n": len(rows),
        "correctness": pct([SCORE.get(r["correct"], 0) for r in rows]),
        "faithfulness": pct([r["faithful"] for r in rows]),
        "context recall": pct([SCORE.get(r["context_recall"], 0) for r in pos]),
        "similarity": f"{statistics.mean(r['similarity'] for r in rows):.2f}" if rows else "n/a",
    }


def breakdown(records: list[dict], key: str) -> str:
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        groups[r.get(key) or "-"].append(r)
    rows = [{key: g, **summarize(rs)} for g, rs in sorted(groups.items(), key=lambda kv: -len(kv[1]))]
    return md_table(rows, [key, "n", "correctness", "faithfulness", "context recall", "similarity"])


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=DEFAULT_EVALS)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--delay", type=float, default=0.0, help="seconds between questions (rate limits)")
    ap.add_argument("--out", default=None, help="results folder (default: results/<eval set>/)")
    ap.add_argument("--no-rewrite", action="store_true",
                    help="for follow-up cases (with \"history\"), skip rewriting into a standalone question (baseline)")
    ap.add_argument("--report-only", action="store_true",
                    help="rebuild answer_eval.md from the saved answers.jsonl without re-running questions")
    args = ap.parse_args()

    out_dir = Path(args.out) if args.out else results_dir(args.file)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.report_only:
        records = [json.loads(line) for line in open(out_dir / "answers.jsonl", encoding="utf-8")]
        for r in records:
            r["diagnosis"] = diagnose(r)
        write_report(records, args, out_dir)
        return 0

    cases = load_cases(args.file)[: args.limit]
    records = []

    print(f"{'id':>5}  {'result':<26} {'sec':>5}  question")
    print("-" * 96)
    for i, case in enumerate(cases, start=1):
        t0 = time.perf_counter()
        # Follow-up cases carry earlier turns; rewrite them into a standalone question like the API does.
        turns = [tuple(t) for t in case.get("history", [])]
        asked = case["question"] if args.no_rewrite or not turns else followup.rewrite(case["question"], turns)
        res = answer_question(asked)
        latency = time.perf_counter() - t0
        refused = is_refusal(res["answer"])
        rec = {
            "id": case.get("id", str(i)), "question": case["question"], "golden": case["answer"],
            "answerable": case["answerable"], "topic": case.get("topic"), "type": case.get("type"),
            "difficulty": case.get("difficulty"), "answer": res["answer"], "refused": refused,
            "has_citation": bool(res["citations"]), "latency_s": round(latency, 2),
            "cited": [f"{c['source']}#{c['chunk_index']}" for c in res["citations"]],
        }
        if case.get("expected_substring"):
            rec["citation_ok"] = any(is_hit({"source": c["source"], "content": c["snippet"]}, case)
                                     for c in res["citations"])
        if turns:
            rec["searched_for"] = asked
        # The judge sees the intended standalone question, so "it"/"that" doesn't confuse the grading.
        rec.update(judge({**case, "question": case.get("golden_standalone", case["question"])},
                         res["answer"], res["retrieved"]))
        if case["answerable"] and refused:
            rec["correct"] = "no"  # a refusal never counts as a correct answer, however lenient the judge
        rec["diagnosis"] = diagnose(rec)
        records.append(rec)
        print(f"{rec['id']:>5}  {rec['diagnosis'] if rec['diagnosis'] != 'ok' else '✓ ' + rec['correct']:<26} "
              f"{latency:>5.1f}  {case['question'][:55]}")
        time.sleep(args.delay)

    # Semantic similarity between each bot answer and its golden answer (one batched embedding call).
    vecs = embed_documents([r["answer"] for r in records] + [r["golden"] for r in records])
    n = len(records)
    for r, a, g in zip(records, vecs[:n], vecs[n:]):
        r["similarity"] = round(cosine(a, g), 3)

    with open(out_dir / "answers.jsonl", "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    write_report(records, args, out_dir)
    return 0


def write_report(records: list[dict], args, out_dir: Path) -> None:

    pos = [r for r in records if r["answerable"]]
    neg = [r for r in records if not r["answerable"]]
    lat = sorted(r["latency_s"] for r in records)
    metrics = []
    if pos:
        metrics += [
            {"metric": "Correctness vs golden answer (judge)", "value": pct([SCORE.get(r["correct"], 0) for r in pos]), "n": len(pos)},
            {"metric": "Fully correct answers (judge = yes)", "value": pct([r["correct"] == "yes" for r in pos]), "n": len(pos)},
            {"metric": "Faithfulness / no hallucination (judge)", "value": pct([r["faithful"] for r in pos]), "n": len(pos)},
            {"metric": "Context recall (judge)", "value": pct([SCORE.get(r["context_recall"], 0) for r in pos]), "n": len(pos)},
            {"metric": "Answers with a citation", "value": pct([r["has_citation"] for r in pos]), "n": len(pos)},
            {"metric": "False refusals", "value": pct([r["refused"] for r in pos]), "n": len(pos)},
            {"metric": "Semantic similarity to golden (cosine)", "value": f"{statistics.mean(r['similarity'] for r in pos):.2f}", "n": len(pos)},
        ]
        cit = [r["citation_ok"] for r in pos if "citation_ok" in r]
        if cit:
            metrics.append({"metric": "Citation accuracy (expected text cited)", "value": pct(cit), "n": len(cit)})
    if neg:
        metrics += [
            {"metric": "Out-of-scope handled correctly (judge)", "value": pct([r["correct"] == "yes" for r in neg]), "n": len(neg)},
            {"metric": "Out-of-scope: said \"I don't know\"", "value": pct([r["refused"] for r in neg]), "n": len(neg)},
        ]
    if lat:
        p95 = lat[min(len(lat) - 1, math.ceil(0.95 * len(lat)) - 1)]
        metrics.append({"metric": "Latency p50 / p95", "value": f"{statistics.median(lat):.1f}s / {p95:.1f}s", "n": len(lat)})
    table = md_table(metrics, ["metric", "value", "n"])

    diag: dict[str, int] = defaultdict(int)
    for r in records:
        diag[r["diagnosis"]] += 1
    diag_table = md_table([{"outcome": k, "questions": v} for k, v in sorted(diag.items(), key=lambda kv: -kv[1])],
                          ["outcome", "questions"])

    sections = [f"## Summary\n\n{table}", f"## Outcome diagnosis\n\n{diag_table}"]
    for key in ("topic", "type", "difficulty"):
        if any(r.get(key) for r in records):
            sections.append(f"## By {key}\n\n{breakdown(records, key)}")

    failures = [r for r in records if r["diagnosis"] != "ok"]
    fail_md = "\n".join(
        f"- **{r['id']} · {r['diagnosis']}**: {r['question']}\n"
        f"  - Judge: correct={r['correct']}, faithful={r['faithful']}"
        f"{', context recall=' + r['context_recall'] if 'context_recall' in r else ''}. {r['reason']}\n"
        f"  - Bot: {r['answer'][:300]}\n  - Golden: {r['golden'][:300]}"
        for r in failures) or "None."
    sections.append(f"## Failures ({len(failures)})\n\n{fail_md}")

    header = (f"# Answer-quality eval: `{args.file}`\n\nProvider `{config.PROVIDER}` · chat `{config.CHAT_MODEL}` · "
              f"judge `{config.JUDGE_MODEL}` · retrieval `{config.RETRIEVAL_MODE}` k={config.TOP_K} · reranker `{config.RERANKER}` · "
              f"MIN_SIMILARITY={config.MIN_SIMILARITY} · chunks {config.CHUNK_TOKENS}/{config.CHUNK_OVERLAP}\n")
    (out_dir / "answer_eval.md").write_text(
        header + "\n" + "\n\n".join(sections) + f"\n\nPer-question detail: `{(out_dir / 'answers.jsonl').as_posix()}`.\n",
        encoding="utf-8")

    print("-" * 96)
    print(table)
    print("\n" + diag_table)
    print(f"\nReport: {(out_dir / 'answer_eval.md').as_posix()}")


if __name__ == "__main__":
    raise SystemExit(main())
