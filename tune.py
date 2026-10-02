"""Hyperparameter sweep for the RAG pipeline, scored by the retrieval evals.

Grid: chunk size × overlap × retrieval mode (vector / keyword BM25 / hybrid RRF) × top-k.
Runs fully in memory (no Supabase), so trying a new config costs only embedding calls, and
embeddings are cached on disk in .cache/, so re-runs are nearly free.

    python tune.py                                  # default grid
    python tune.py --sizes 300 500 --overlaps 50    # custom grid
    python tune.py --tolerance 0                    # demand the exact best hit rate

Writes tuning.csv, tuning.md and best_config.json to results/<eval set>/, and prints the
.env lines to apply the winner. Re-run ingest.py afterwards if chunk settings changed.

Selection rule: among configs whose hit rate is within --tolerance of the best, pick the one
that sends the fewest context tokens to the LLM (cost + less noise), then the highest MRR.
"""

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

import numpy as np

from rag.chunking import chunk_segments, count_tokens
from rag.embeddings import embed_documents, embed_query, model_id
from rag.evalset import DEFAULT_EVALS, first_hit_rank, load_cases, md_table, results_dir, safe_threshold, utf8_stdout
from rag.loaders import SUPPORTED, embed_text, load

CACHE = Path(".cache")
RRF_K = 60  # same constant as hybrid_search() in schema.sql


# --- embedding cache --------------------------------------------------------------------

class EmbedCache:
    def __init__(self) -> None:
        CACHE.mkdir(exist_ok=True)
        safe = re.sub(r"[^\w.-]", "_", model_id())
        self.path = CACHE / f"embeddings_{safe}.json"
        self.data: dict[str, list[float]] = json.loads(self.path.read_text()) if self.path.exists() else {}
        self.calls = 0

    def _key(self, kind: str, text: str) -> str:
        return hashlib.sha256(f"{kind}\n{text}".encode()).hexdigest()

    def documents(self, texts: list[str]) -> np.ndarray:
        missing = list({t for t in texts if self._key("doc", t) not in self.data})
        if missing:
            self.calls += len(missing)
            for t, v in zip(missing, embed_documents(missing)):
                self.data[self._key("doc", t)] = v
            self.save()
        return np.array([self.data[self._key("doc", t)] for t in texts], dtype=np.float32)

    def query(self, text: str) -> np.ndarray:
        k = self._key("query", text)
        if k not in self.data:
            self.calls += 1
            self.data[k] = embed_query(text)
        return np.array(self.data[k], dtype=np.float32)

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data))


# --- keyword search (BM25), an in-memory stand-in for Postgres full-text search ----------

_STOP = set("a an and are as at be by can do does for from how i if in is it its my of on or so "
            "that the their there this to was what when where which who will with you your".split())


def tokenize(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOP]


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75) -> None:
        self.docs = [Counter(tokenize(d)) for d in docs]
        self.lens = [sum(d.values()) for d in self.docs]
        self.avg = sum(self.lens) / len(self.lens)
        df = Counter(t for d in self.docs for t in d)
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.k1, self.b = k1, b

    def scores(self, query: str) -> np.ndarray:
        q = tokenize(query)
        out = np.zeros(len(self.docs))
        for i, (d, ln) in enumerate(zip(self.docs, self.lens)):
            for t in q:
                if t in d:
                    tf = d[t]
                    out[i] += self.idf[t] * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * ln / self.avg))
        return out


def rrf(rankings: list[list[int]], depth: int) -> list[int]:
    fused: Counter = Counter()
    for ranking in rankings:
        for r, idx in enumerate(ranking[:depth], start=1):
            fused[idx] += 1 / (RRF_K + r)
    return [idx for idx, _ in fused.most_common()]


# --- sweep ------------------------------------------------------------------------------

def load_segments(root: Path) -> dict[str, list]:
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED)
    return {p.relative_to(root).as_posix(): load(p) for p in files}


def build_index(segments: dict[str, list], size: int, overlap: int, cache: EmbedCache):
    chunks = []
    for source, segs in segments.items():
        for i, c in enumerate(chunk_segments(segs, max_tokens=size, overlap=overlap)):
            chunks.append({"source": source, "chunk_index": i, "content": c.text,
                           "tokens": count_tokens(c.text), "embed_text": embed_text(source, c)})
    vectors = cache.documents([c["embed_text"] for c in chunks])
    bm25 = BM25([c["embed_text"] for c in chunks])
    return chunks, vectors, bm25


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default="docs")
    ap.add_argument("--file", default=DEFAULT_EVALS)
    ap.add_argument("--sizes", type=int, nargs="+", default=[200, 350, 500, 800])
    ap.add_argument("--overlaps", type=int, nargs="+", default=[0, 50, 100])
    ap.add_argument("--ks", type=int, nargs="+", default=[1, 3, 5, 8])
    ap.add_argument("--modes", nargs="+", default=["vector", "keyword", "hybrid"])
    ap.add_argument("--tolerance", type=float, default=0.025,
                    help="hit-rate slack when preferring cheaper configs (0.025 = 1 question in 40)")
    args = ap.parse_args()

    cases = load_cases(args.file)
    pos_cases = [c for c in cases if c["answerable"]]
    neg_cases = [c for c in cases if not c["answerable"]]
    segments = load_segments(Path(args.docs))
    cache = EmbedCache()
    qvecs = {c["question"]: cache.query(c["question"]) for c in cases}
    cache.save()
    max_k = max(args.ks)

    rows: list[dict] = []
    thresholds: dict[tuple[int, int], tuple[float, int]] = {}  # (min_similarity, unanswerable blocked)
    for size in args.sizes:
        for overlap in args.overlaps:
            if overlap >= size // 2:
                continue
            chunks, vectors, bm25 = build_index(segments, size, overlap, cache)
            print(f"chunks {size}/{overlap}: {len(chunks)} chunks")

            # Refusal threshold: never block an answerable question; count what it filters for free.
            top1 = {c["question"]: float((vectors @ qvecs[c["question"]]).max()) for c in cases}
            thr = safe_threshold([top1[c["question"]] for c in pos_cases])
            thresholds[(size, overlap)] = (thr, sum(top1[c["question"]] < thr for c in neg_cases))

            for mode in args.modes:
                ranks: dict[str, list[int]] = {}
                for c in pos_cases:
                    sims = vectors @ qvecs[c["question"]]
                    vec_rank = list(np.argsort(-sims))
                    kw_scores = bm25.scores(c["question"])
                    kw_rank = [i for i in np.argsort(-kw_scores) if kw_scores[i] > 0]
                    ranks[c["question"]] = {
                        "vector": vec_rank,
                        "keyword": kw_rank,
                        "hybrid": rrf([vec_rank, kw_rank], depth=max_k * 4),
                    }[mode][:max_k]

                for k in args.ks:
                    hits, rr, ctx = 0, 0.0, 0
                    for c in pos_cases:
                        top = [chunks[i] for i in ranks[c["question"]][:k]]
                        r = first_hit_rank(top, c)
                        hits += bool(r)
                        rr += 1 / r if r else 0
                        ctx += sum(ch["tokens"] for ch in top)
                    n = len(pos_cases)
                    rows.append({
                        "chunk_tokens": size, "overlap": overlap, "mode": mode, "k": k,
                        "chunks": len(chunks), "hit_rate": round(hits / n, 4), "mrr": round(rr / n, 4),
                        "avg_context_tokens": round(ctx / n),
                    })

    cache.save()
    best_hit = max(r["hit_rate"] for r in rows)
    eligible = [r for r in rows if r["hit_rate"] >= best_hit - args.tolerance]
    best = min(eligible, key=lambda r: (r["avg_context_tokens"], -r["mrr"], -r["hit_rate"]))
    thr, blocked = thresholds[(best["chunk_tokens"], best["overlap"])]
    best = {**best, "min_similarity": thr, "unanswerable_filtered": blocked, "unanswerable_total": len(neg_cases)}
    # keyword-only isn't served by the API; map it to hybrid, which includes the keyword ranking.
    serve_mode = "hybrid" if best["mode"] == "keyword" else best["mode"]

    out_dir = results_dir(args.file)
    with open(out_dir / "tuning.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (out_dir / "best_config.json").write_text(json.dumps(best, indent=2))

    env = (f"CHUNK_TOKENS={best['chunk_tokens']}\nCHUNK_OVERLAP={best['overlap']}\n"
           f"RETRIEVAL_MODE={serve_mode}\nTOP_K={best['k']}\nMIN_SIMILARITY={best['min_similarity']}")
    write_report(rows, best, env, thresholds, len(pos_cases), len(neg_cases), args, out_dir)

    print(f"\n{len(rows)} configs evaluated on {len(pos_cases)} answerable + {len(neg_cases)} unanswerable "
          f"questions ({cache.calls} new embeddings; rest from cache).")
    print(f"Best hit rate anywhere: {best_hit:.0%}")
    print(f"Chosen: {best['chunk_tokens']}/{best['overlap']} tokens, {best['mode']}, k={best['k']} → "
          f"hit {best['hit_rate']:.0%}, MRR {best['mrr']:.3f}, ~{best['avg_context_tokens']} context tokens")
    print(f"Refusal threshold {best['min_similarity']}: blocks 0 answerable questions and filters "
          f"{blocked}/{len(neg_cases)} unanswerable ones before the LLM (the prompt guard handles the rest)")
    print(f"\nApply in .env, then re-run `python ingest.py`:\n{env}\n\nReport: {(out_dir / 'tuning.md').as_posix()}")
    return 0


def write_report(rows, best, env, thresholds, n_pos, n_neg, args, out_dir) -> None:
    def pct(r):
        return {**r, "hit_rate": f"{r['hit_rate']:.0%}", "mrr": f"{r['mrr']:.3f}"}

    cols = ["chunk_tokens", "overlap", "mode", "k", "hit_rate", "mrr", "avg_context_tokens"]
    top = sorted(rows, key=lambda r: (-r["hit_rate"], -r["mrr"], r["avg_context_tokens"]))[:15]

    by_mode = []
    for mode in args.modes:
        for k in args.ks:
            sub = [r for r in rows if r["mode"] == mode and r["k"] == k]
            if sub:
                b = max(sub, key=lambda r: (r["hit_rate"], r["mrr"]))
                by_mode.append(pct({**b, "config": f"{b['chunk_tokens']}/{b['overlap']}"}))

    by_chunk = []
    k5 = 5 if 5 in args.ks else max(args.ks)
    for (size, overlap), (thr, blocked) in thresholds.items():
        cells = {"chunks": f"{size}/{overlap}"}
        for mode in args.modes:
            r = next(r for r in rows if (r["chunk_tokens"], r["overlap"], r["mode"], r["k"]) == (size, overlap, mode, k5))
            cells[f"{mode} hit@{k5}"] = f"{r['hit_rate']:.0%}"
        cells["min_similarity"] = f"{thr:.3f}"
        cells["off-topic filtered"] = f"{blocked}/{n_neg}"
        by_chunk.append(cells)

    md = f"""# RAG tuning report

Embedding model: `{model_id()}` · eval set: {n_pos} answerable + {n_neg} unanswerable questions
Selection rule: hit rate within {args.tolerance:.1%} of the best, then fewest context tokens, then highest MRR.

## Chosen config

| chunk tokens | overlap | mode | top-k | hit rate | MRR | context tokens / query | min_similarity | unanswerable filtered pre-LLM |
|---|---|---|---|---|---|---|---|---|
| {best['chunk_tokens']} | {best['overlap']} | {best['mode']} | {best['k']} | {best['hit_rate']:.0%} | {best['mrr']:.3f} | {best['avg_context_tokens']} | {best['min_similarity']} | {best['unanswerable_filtered']}/{n_neg} |

```env
{env}
```

## Retrieval mode × chunking (hit@{k5})

{md_table(by_chunk, list(by_chunk[0]))}

"min_similarity" is the highest top-1 cosine cutoff that still answers every answerable question (minus a
0.03 margin). On-topic unanswerable questions score like answerable ones, so the threshold only filters
clearly off-topic queries; the prompt guard catches the rest (measured by eval_answers.py).

## Best config per mode and k

{md_table(by_mode, ["mode", "k", "config", "hit_rate", "mrr", "avg_context_tokens"])}

## Top 15 configs overall

{md_table([pct(r) for r in top], cols)}

Full grid: `tuning.csv` (same folder). Keyword search here is in-memory BM25; production hybrid search uses
Postgres full-text search (`hybrid_search` in `supabase/schema.sql`), so confirm the winner with `python eval.py`.
"""
    (out_dir / "tuning.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
