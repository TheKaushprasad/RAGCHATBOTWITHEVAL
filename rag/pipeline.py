"""The full question → answer path, shared by the API and the evals so they test the same thing."""

from rag import config, llm, store
from rag.embeddings import embed_query


def retrieve(question: str, k: int | None = None, mode: str | None = None) -> list[dict]:
    mode = mode or config.RETRIEVAL_MODE
    return store.match(embed_query(question), k or config.TOP_K, query_text=question, mode=mode)


def citation(n: int, c: dict) -> dict:
    return {
        "n": n,
        "source": c["source"],
        "chunk_index": c["chunk_index"],
        "page": c.get("page"),
        "heading": (c.get("metadata") or {}).get("heading"),
        "snippet": c["content"],
        "similarity": round(float(c["similarity"]), 4),
    }


def is_refusal(text: str) -> bool:
    return text.strip().lower().startswith(config.IDK.lower())


def answer_question(question: str) -> dict:
    """Returns {answer, citations, retrieved, grounded}. Raises on upstream (retrieval) failures."""
    chunks = retrieve(question)
    retrieved = [citation(n, c) for n, c in enumerate(chunks, start=1)]

    # Guard 1: nothing similar enough → refuse without calling the LLM.
    best = max((c["similarity"] for c in chunks), default=0.0)
    if best < config.MIN_SIMILARITY:
        return {"answer": f"{config.IDK}.", "citations": [], "retrieved": retrieved, "grounded": False}

    # Guard 2: the prompt makes the model refuse when the passages don't answer the question.
    text = llm.answer(question, chunks)
    cited = llm.cited_numbers(text, len(chunks))
    grounded = bool(cited) and not is_refusal(text)
    return {
        "answer": text,
        "citations": [retrieved[n - 1] for n in cited] if grounded else [],
        "retrieved": retrieved,
        "grounded": grounded,
    }
