"""The full question → answer path, shared by the API and the evals so they test the same thing."""

import time

from rag import config, llm, rerank, store
from rag.embeddings import embed_query


def search(question: str, k: int | None = None, mode: str | None = None,
           session_ns: str | None = None, include_public: bool = True) -> list[dict]:
    """First stage: vector (or hybrid) search. Returns the reranker's candidate pool when one is on."""
    mode = mode or config.RETRIEVAL_MODE
    k = k or config.TOP_K
    fetch = max(k, config.RERANK_CANDIDATES) if config.RERANKER != "none" else k
    return store.match(embed_query(question), fetch, query_text=question, mode=mode,
                       session_ns=session_ns, include_public=include_public)


def retrieve(question: str, k: int | None = None, mode: str | None = None,
             session_ns: str | None = None, include_public: bool = True) -> list[dict]:
    """Search one user's uploads (session_ns) and, if include_public, the shared docs (used by the evals),
    then rerank to the best k."""
    return rerank.rerank(question, search(question, k, mode, session_ns, include_public), k or config.TOP_K)


def citation(n: int, c: dict) -> dict:
    return {
        "n": n,
        "source": c["source"],
        "chunk_index": c["chunk_index"],
        "page": c.get("page"),
        "heading": (c.get("metadata") or {}).get("heading"),
        "snippet": c["content"],
        "similarity": round(float(c["similarity"]), 4),
        "rerank_score": c.get("rerank_score"),
        "uploaded": c.get("namespace", store.PUBLIC) != store.PUBLIC,
    }


def is_refusal(text: str) -> bool:
    return text.strip().lower().startswith(config.IDK.lower())


def prepare(question: str, session_ns: str | None = None, include_public: bool = True,
            timings: dict | None = None) -> tuple[list[dict], dict | None]:
    """Search and rerank. Returns (chunks for the LLM, None), or ([], final refusal result) when guard 1 trips.

    `timings`, if given, receives seconds per stage ("search", "rerank") for latency logging."""
    t = time.perf_counter()
    candidates = search(question, session_ns=session_ns, include_public=include_public)
    if timings is not None:
        timings["search"] = time.perf_counter() - t

    # Guard 1: nothing similar enough → refuse without calling the LLM (or the reranker). Checked on the
    # vector scores before reranking, so MIN_SIMILARITY means the same thing with or without a reranker.
    best = max((c["similarity"] for c in candidates), default=0.0)
    if best < config.MIN_SIMILARITY:
        retrieved = [citation(n, c) for n, c in enumerate(candidates[:config.TOP_K], start=1)]
        return [], {"answer": f"{config.IDK}.", "citations": [], "retrieved": retrieved, "grounded": False}

    t = time.perf_counter()
    chunks = rerank.rerank(question, candidates, config.TOP_K)
    if timings is not None:
        timings["rerank"] = time.perf_counter() - t
    return chunks, None


def finish(text: str, chunks: list[dict]) -> dict:
    """Turn the model's answer into {answer, citations, retrieved, grounded}."""
    text = text.strip() or f"{config.IDK}."
    retrieved = [citation(n, c) for n, c in enumerate(chunks, start=1)]
    # Guard 2: the prompt makes the model refuse when the passages don't answer the question.
    cited = llm.cited_numbers(text, len(chunks))
    grounded = bool(cited) and not is_refusal(text)
    return {
        "answer": text,
        "citations": [retrieved[n - 1] for n in cited] if grounded else [],
        "retrieved": retrieved,
        "grounded": grounded,
    }


def answer_question(question: str, session_ns: str | None = None, include_public: bool = True,
                    timings: dict | None = None) -> dict:
    """Returns {answer, citations, retrieved, grounded}. Raises on upstream (retrieval) failures."""
    chunks, refusal = prepare(question, session_ns, include_public, timings)
    if refusal:
        return refusal
    t = time.perf_counter()
    text = llm.answer(question, chunks)
    if timings is not None:
        timings["answer"] = time.perf_counter() - t
    return finish(text, chunks)
