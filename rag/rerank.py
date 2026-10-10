"""Second-stage reranking: retrieve a wide candidate set cheaply, then reorder it with a model that reads
the question and each passage together, and keep the best few.

Embedding search scores the question and a chunk separately, so a chunk that merely shares vocabulary can
outrank the one that actually answers. A reranker judges the pair, which fixes most of those misses.

    RERANKER=none    off (default)
    RERANKER=llm     the configured chat model scores every candidate in one call (no extra account)
    RERANKER=cohere  Cohere Rerank (needs COHERE_API_KEY)

A failing reranker never breaks an answer: it falls back to the original vector order.
"""

import json
import sys

from rag import config, llm

LLM_SYSTEM = """You judge how well passages answer a question. Reply with JSON only:
{"scores": {"<passage id>": <0-10>, ...}}

Score every passage id given:
- 10: directly and fully answers the question
- 6-9: answers part of it, or contains facts the answer needs
- 1-5: same topic, but doesn't help answer it
- 0: unrelated
Judge only what the passage says, not what you know."""

MAX_PASSAGE_CHARS = 1800  # ~450 tokens; chunks are 350, so this only trims outliers


def _llm_scores(question: str, chunks: list[dict]) -> list[float]:
    passages = "\n\n".join(f"<passage id=\"{i}\">\n{c['content'][:MAX_PASSAGE_CHARS]}\n</passage>"
                           for i, c in enumerate(chunks, start=1))
    raw = llm.complete(LLM_SYSTEM, f"Question: {question}\n\n{passages}", model=config.RERANK_MODEL, json_mode=True)
    scores = json.loads(raw).get("scores", {})
    return [float(scores.get(str(i), 0)) for i in range(1, len(chunks) + 1)]


def _cohere_scores(question: str, chunks: list[dict]) -> list[float]:
    import httpx

    if not config.COHERE_API_KEY:
        raise RuntimeError("RERANKER=cohere needs COHERE_API_KEY")
    res = httpx.post(
        "https://api.cohere.com/v2/rerank",
        headers={"Authorization": f"Bearer {config.COHERE_API_KEY}"},
        json={"model": config.RERANK_MODEL, "query": question, "documents": [c["content"] for c in chunks]},
        timeout=20,
    )
    res.raise_for_status()
    scores = [0.0] * len(chunks)
    for r in res.json()["results"]:
        scores[r["index"]] = float(r["relevance_score"])
    return scores


def rerank(question: str, chunks: list[dict], k: int) -> list[dict]:
    """The k best chunks for the question. Each keeps its vector `similarity` and gains `rerank_score`."""
    if config.RERANKER == "none" or len(chunks) <= 1:
        return chunks[:k]
    try:
        scores = (_cohere_scores if config.RERANKER == "cohere" else _llm_scores)(question, chunks)
    except Exception as e:  # noqa: BLE001 - reranking is an optimisation, never a reason to fail the answer
        print(f"rerank failed, using vector order: {e}", file=sys.stderr)
        return chunks[:k]
    # Stable sort: ties keep their vector-search order.
    order = sorted(range(len(chunks)), key=lambda i: -scores[i])
    return [{**chunks[i], "rerank_score": scores[i]} for i in order[:k]]
