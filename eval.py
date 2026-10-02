"""Retrieval eval against the live Supabase index (the same retrieval code the API uses).

    python eval.py                     # hit rate@k + MRR with the .env config
    python eval.py --mode hybrid --k 3 # override retrieval settings
    python eval.py --min 0.8           # exit 1 if hit rate < 80% (for CI)
    python eval.py --verbose           # print retrieved chunks for every question

Answerable questions count toward hit rate / MRR. Unanswerable ones (answerable: false) are used
to check the "I don't know" threshold: their top similarity should fall below MIN_SIMILARITY.
Writes results/retrieval_eval.md.
"""

import argparse
import time

from rag import config
from rag.evalset import RESULTS, best_threshold, first_hit_rank, load_cases, utf8_stdout
from rag.pipeline import retrieve


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="evals.json")
    ap.add_argument("--k", type=int, default=config.TOP_K)
    ap.add_argument("--mode", choices=["vector", "hybrid"], default=config.RETRIEVAL_MODE)
    ap.add_argument("--min", type=float, default=None, help="fail (exit 1) if hit rate is below this, 0-1")
    ap.add_argument("--delay", type=float, default=0.0, help="seconds between queries (rate limits)")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    cases = load_cases(args.file)
    hits, rr_sum, n_pos = 0, 0.0, 0
    pos_sims, neg_sims, lines = [], [], []

    print(f"Retrieval: mode={args.mode}, k={args.k}, MIN_SIMILARITY={config.MIN_SIMILARITY}\n")
    print(f"{'#':>3}  {'res':<4} {'rank':>4}  {'top sim':>7}  question")
    print("-" * 84)
    for i, case in enumerate(cases, start=1):
        chunks = retrieve(case["question"], args.k, args.mode)
        top = max((c["similarity"] for c in chunks), default=0.0)
        if case["answerable"]:
            n_pos += 1
            pos_sims.append(top)
            rank = first_hit_rank(chunks, case)
            if rank:
                hits += 1
                rr_sum += 1 / rank
            mark, rank_s = ("✓" if rank else "✗"), str(rank or "-")
        else:
            neg_sims.append(top)
            refused = top < config.MIN_SIMILARITY
            mark, rank_s = ("IDK" if refused else "LEAK"), "n/a"
        line = f"{i:>3}  {mark:<4} {rank_s:>4}  {top:>7.3f}  {case['question'][:60]}"
        print(line)
        lines.append(line)
        if args.verbose or mark in ("✗", "LEAK"):
            for r, c in enumerate(chunks, start=1):
                print(f"{'':>22}{r}. {c['source']}#{c['chunk_index']}  sim={c['similarity']:.3f}")
        time.sleep(args.delay)

    rate = hits / n_pos if n_pos else 0.0
    mrr = rr_sum / n_pos if n_pos else 0.0
    thr, thr_acc = best_threshold(pos_sims, neg_sims)
    summary = [
        f"Hit rate@{args.k}: {hits}/{n_pos} = {rate:.0%}",
        f"MRR@{args.k}:      {mrr:.3f}",
    ]
    if pos_sims:
        summary.append(f"Top-1 similarity, answerable:   min {min(pos_sims):.3f}  avg {sum(pos_sims) / len(pos_sims):.3f}")
    if neg_sims:
        refused = sum(s < config.MIN_SIMILARITY for s in neg_sims)
        summary += [
            f"Top-1 similarity, unanswerable: max {max(neg_sims):.3f}  avg {sum(neg_sims) / len(neg_sims):.3f}",
            f"Unanswerable refused by threshold {config.MIN_SIMILARITY}: {refused}/{len(neg_sims)} "
            f"(the LLM prompt is a second guard; see eval_answers.py)",
            f"Best separating threshold on this data: {thr:.3f} ({thr_acc:.0%} accuracy)",
        ]
    print("-" * 84)
    print("\n".join(summary))

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "retrieval_eval.md").write_text(
        f"# Retrieval eval\n\nmode=`{args.mode}` · k={args.k} · MIN_SIMILARITY={config.MIN_SIMILARITY} · "
        f"chunks {config.CHUNK_TOKENS}/{config.CHUNK_OVERLAP} · `{config.PROVIDER}:{config.EMBED_MODEL}`\n\n"
        + "\n".join(f"- {s}" for s in summary)
        + "\n\n```\n" + "\n".join(lines) + "\n```\n",
        encoding="utf-8",
    )

    if args.min is not None and rate < args.min:
        print(f"FAIL: hit rate {rate:.0%} < required {args.min:.0%}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
