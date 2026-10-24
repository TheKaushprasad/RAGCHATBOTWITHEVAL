"""Retrieval eval against the live Supabase index (the same retrieval code the API uses).

    python eval.py                     # hit rate@k + MRR with the .env config
    python eval.py --mode hybrid --k 3 # override retrieval settings
    python eval.py --min 0.8           # exit 1 if hit rate < 80% (for CI)
    python eval.py --verbose           # print retrieved chunks for every question

    # Compare query rewriting and rerankers on passage-level hit rate (see rag/qrels.py):
    python eval.py --compare --rerankers none,llm,bge
    python eval.py --compare --file evals_followup.json   # follow-ups: original vs rewritten query

Answerable questions count toward hit rate / MRR. Unanswerable ones (answerable: false) are used
to check the "I don't know" threshold: their top similarity should fall below MIN_SIMILARITY.
Writes retrieval_eval.md to results/<eval set>/ (or examples/<x>/results/).
"""

import argparse
import time

from rag import config, followup, qrels, rerank
from rag.evalset import DEFAULT_EVALS, best_threshold, first_hit_rank, load_cases, results_dir, utf8_stdout
from rag.pipeline import search


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=DEFAULT_EVALS)
    ap.add_argument("--k", type=int, default=config.TOP_K)
    ap.add_argument("--mode", choices=["vector", "hybrid"], default=config.RETRIEVAL_MODE)
    ap.add_argument("--min", type=float, default=None, help="fail (exit 1) if hit rate is below this, 0-1")
    ap.add_argument("--delay", type=float, default=0.0, help="seconds between queries (rate limits)")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--compare", action="store_true",
                    help="compare query rewriting x rerankers on passage-level hit rate, using judged labels")
    ap.add_argument("--rerankers", default="none,llm",
                    help="with --compare: comma-separated rerankers to compare (none, llm, cohere, bge)")
    args = ap.parse_args()
    if args.compare:
        return compare(args)

    cases = load_cases(args.file)
    hits, rr_sum, n_pos = 0, 0.0, 0
    pos_sims, neg_sims, lines = [], [], []

    print(f"Retrieval: mode={args.mode}, k={args.k}, reranker={config.RERANKER}, MIN_SIMILARITY={config.MIN_SIMILARITY}\n")
    print(f"{'#':>3}  {'res':<4} {'rank':>4}  {'top sim':>7}  question")
    print("-" * 84)
    for i, case in enumerate(cases, start=1):
        candidates = search(case["question"], args.k, args.mode)
        top = max((c["similarity"] for c in candidates), default=0.0)  # the refusal guard sees pre-rerank scores
        chunks = rerank.rerank(case["question"], candidates, args.k)
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

    out_dir = results_dir(args.file)
    (out_dir / ("retrieval_eval.md" if config.RERANKER == "none" else f"retrieval_eval_rerank-{config.RERANKER}.md")).write_text(
        f"# Retrieval eval\n\nmode=`{args.mode}` · k={args.k} · reranker `{config.RERANKER}` · MIN_SIMILARITY={config.MIN_SIMILARITY} · "
        f"chunks {config.CHUNK_TOKENS}/{config.CHUNK_OVERLAP} · `{config.PROVIDER}:{config.EMBED_MODEL}`\n\n"
        + "\n".join(f"- {s}" for s in summary)
        + "\n\n```\n" + "\n".join(lines) + "\n```\n",
        encoding="utf-8",
    )

    if args.min is not None and rate < args.min:
        print(f"FAIL: hit rate {rate:.0%} < required {args.min:.0%}")
        return 1
    return 0


def compare(args) -> int:
    """Hit rate@k and MRR@k for each (query variant, reranker) pair, against judged passage labels.

    Query variants: the question as asked, and, for cases with chat history, the rewritten standalone query.
    Every variant retrieves RERANK_CANDIDATES chunks; each reranker then keeps the top k of those."""
    methods = [m.strip() for m in args.rerankers.split(",") if m.strip()]
    cases = [c for c in load_cases(args.file) if c["answerable"]]
    labels = qrels.load(args.file)
    pool_k = config.RERANK_CANDIDATES
    stats: dict[tuple[str, str], list[int | None]] = {}
    recall_at_pool: dict[str, list[bool]] = {}

    print(f"Compare: {len(cases)} answerable cases, {pool_k} candidates -> top {args.k}, "
          f"rerankers {methods}, mode={args.mode}\n")
    for i, case in enumerate(cases, start=1):
        turns = [tuple(t) for t in case.get("history", [])]
        variants = {"original": case["question"]}
        if turns:
            variants["rewritten"] = followup.rewrite(case["question"], turns)
        candidates = {name: search(q, pool_k, args.mode) for name, q in variants.items()}

        # Label every candidate any variant can see (once; cached in <eval>_qrels.json).
        cid = case.get("id", str(i))
        pool = {qrels.chunk_key(c): c for cands in candidates.values() for c in cands}
        known = labels.get(cid, {"judged": [], "relevant": []})
        unjudged = [c for key, c in pool.items() if key not in known["judged"]]
        if unjudged:
            new = qrels.judge(case, unjudged)
            known = {"judged": known["judged"] + new["judged"], "relevant": known["relevant"] + new["relevant"]}
            labels[cid] = known
            qrels.save(args.file, labels)
        relevant = set(known["relevant"])

        row = []
        for name, q in variants.items():
            recall_at_pool.setdefault(name, []).append(any(qrels.chunk_key(c) in relevant for c in candidates[name]))
            for method in methods:
                top = rerank.rerank(q, candidates[name], args.k, method, strict=True)
                rank = next((r for r, c in enumerate(top, 1) if qrels.chunk_key(c) in relevant), None)
                stats.setdefault((name, method), []).append(rank)
                row.append(f"{name[:4]}/{method}:{rank or '-'}")
        print(f"{cid:>5}  rel={len(relevant):<2} {'  '.join(row)}  {case['question'][:48]}")
        if turns and args.verbose:
            print(f"{'':>7}rewritten: {variants['rewritten']}")
        time.sleep(args.delay)

    n = len(cases)
    no_label = sum(1 for c in cases if not labels.get(c.get("id", ""), {}).get("relevant"))
    lines = [f"| query | reranker | hit rate@{args.k} | MRR@{args.k} |", "|---|---|---|---|"]
    for (name, method), ranks in stats.items():
        hits = sum(r is not None for r in ranks)
        mrr = sum(1 / r for r in ranks if r) / n
        lines.append(f"| {name} | {method} | {hits}/{n} = {hits / n:.0%} | {mrr:.3f} |")
    ceiling = [f"- Relevant passage anywhere in the top {pool_k} ({name} query): "
               f"{sum(v)}/{n} = {sum(v) / n:.0%} (the most any reranker can reach)" for name, v in recall_at_pool.items()]
    notes = ceiling + [f"- Cases where the judge found no relevant passage at all: {no_label}"]
    print("\n" + "\n".join(lines + [""] + notes))

    out = results_dir(args.file) / "retrieval_compare.md"
    out.write_text(
        f"# Retrieval comparison: `{args.file}`\n\n"
        f"{n} answerable cases · `{config.PROVIDER}:{config.EMBED_MODEL}` · mode `{args.mode}` · "
        f"{pool_k} candidates reranked to top {args.k} · rewrite `{config.REWRITE_PROVIDER}:{config.REWRITE_MODEL}` · "
        f"labels judged by `{config.JUDGE_PROVIDER}:{config.JUDGE_MODEL}` ({qrels.qrels_path(args.file).name})\n\n"
        + "\n".join(lines) + "\n\n" + "\n".join(notes) + "\n",
        encoding="utf-8",
    )
    print(f"\nReport: {out.as_posix()}")

    # CI gate: every compared setup must keep its passage-level hit rate above --min.
    failed = [(name, method, sum(r is not None for r in ranks) / n) for (name, method), ranks in stats.items()
              if args.min is not None and sum(r is not None for r in ranks) / n < args.min]
    for name, method, rate in failed:
        print(f"FAIL: {name}/{method} hit rate {rate:.0%} < required {args.min:.0%}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
