"""Contextual retrieval: one sentence per chunk saying where it sits in its document, prepended before embedding.

A chunk like "It works by splitting the document into pieces…" doesn't say what "it" is, so its embedding misses
questions that name the topic. An LLM writes a short situating sentence per chunk (using a summary of the whole
document), and that sentence is embedded together with the chunk. The stored passage and its citations are
unchanged; the sentence is kept in metadata["context"].

Batched (CONTEXT_BATCH chunks per call) and parallel so a 150-chunk upload stays within the API time limit.
Any failure leaves the chunks without context rather than failing the ingest.
"""

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from rag import config, llm

SUMMARY_SYSTEM = """Summarise this document in at most two sentences: what it is and the main topics it covers.
Output only the summary."""

CONTEXT_SYSTEM = """You help a search engine understand document chunks. Reply with JSON only:
{"contexts": {"<chunk id>": "<one sentence>", ...}}

For every chunk id, write one sentence (max 30 words) that situates the chunk within the document: which
section or topic it belongs to and what it is about, naming the subject explicitly where the chunk only
implies it (e.g. "it" → "retrieval-augmented generation"). Use only the document summary and the chunk.
Don't add facts that aren't there."""


def _summary(source: str, full_text: str) -> str:
    return llm.complete(SUMMARY_SYSTEM, f"Document: {source}\n\n{full_text[:24000]}").strip()


def _batch(source: str, summary: str, texts: list[str], offset: int) -> dict[int, str]:
    chunks = "\n\n".join(f'<chunk id="{offset + i}">\n{t[:1500]}\n</chunk>' for i, t in enumerate(texts))
    user = f"Document: {source}\nSummary: {summary}\n\n{chunks}"
    raw = json.loads(llm.complete(CONTEXT_SYSTEM, user, json_mode=True)).get("contexts", {})
    return {int(k): " ".join(str(v).split())[:300] for k, v in raw.items() if str(k).isdigit()}


def contextualize(source: str, texts: list[str], budget_s: float | None = None) -> list[str]:
    """One situating sentence per chunk text ("" where unavailable). Stops waiting after `budget_s` seconds."""
    out = [""] * len(texts)
    if not config.CONTEXTUAL or not texts:
        return out
    started = time.monotonic()
    try:
        summary = _summary(source, "\n\n".join(texts))
        size = config.CONTEXT_BATCH
        pool = ThreadPoolExecutor(max_workers=6)
        try:
            jobs = [pool.submit(_batch, source, summary, texts[i:i + size], i) for i in range(0, len(texts), size)]
            remaining = None if budget_s is None else max(1.0, budget_s - (time.monotonic() - started))
            for job in as_completed(jobs, timeout=remaining):
                for i, sentence in job.result().items():
                    if 0 <= i < len(out):
                        out[i] = sentence
        finally:
            pool.shutdown(wait=False, cancel_futures=True)  # don't wait past the budget for stragglers
    except Exception as e:  # noqa: BLE001 - context improves search; it's never a reason to fail an ingest
        print(f"contextualize({source}) incomplete, continuing: {type(e).__name__}: {e}", file=sys.stderr)
    return out


def add_context(source: str, chunks: list, known: dict[str, str] | None = None, budget_s: float | None = None) -> int:
    """Set chunk.meta["context"] on each chunk, reusing `known` contexts (keyed by chunk text) where possible.
    Returns how many chunks got a newly generated context. Does nothing when CONTEXTUAL is off."""
    if not config.CONTEXTUAL:
        return 0
    known = known or {}
    todo = [i for i, c in enumerate(chunks) if not known.get(c.text)]
    fresh = contextualize(source, [chunks[i].text for i in todo], budget_s) if todo else []
    for c in chunks:
        if known.get(c.text):
            c.meta["context"] = known[c.text]
    for i, sentence in zip(todo, fresh):
        if sentence:
            chunks[i].meta["context"] = sentence
    return sum(1 for s in fresh if s)
