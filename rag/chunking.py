"""Token-bounded chunking that prefers paragraph/sentence boundaries.

Input is a list of (text, meta) segments, e.g. one per PDF page or markdown section.
Segments are split into sentence-ish units, then greedily packed into chunks of at most
`max_tokens`. Each new chunk starts with the trailing units of the previous one (up to
`overlap` tokens). A chunk's metadata comes from the first unit it contains.
"""

import re
from dataclasses import dataclass, field
from functools import lru_cache

from rag import config


@lru_cache(maxsize=1)
def _enc():
    # Lazy: on Vercel the tokenizer file is downloaded on first use, so chat-only requests never pay for it.
    import tiktoken

    return tiktoken.get_encoding("cl100k_base")  # approximates the embedding models' tokenizers; fine for sizing
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")


def count_tokens(text: str) -> int:
    return len(_enc().encode(text))


@dataclass
class Unit:
    text: str
    tokens: int
    meta: dict


@dataclass
class Chunk:
    text: str
    meta: dict = field(default_factory=dict)


def _split_units(text: str, meta: dict, max_tokens: int, overlap: int) -> list[Unit]:
    # Hard cuts leave room for the overlap carried in from the previous chunk (+2 for the separator).
    hard_cut = max_tokens - overlap - 2
    units: list[Unit] = []
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para:
            continue
        # Keep short paragraphs, lists and code blocks whole; split long prose into sentences.
        pieces = [para] if count_tokens(para) <= max_tokens // 2 else _SENTENCE_END.split(para)
        for piece in pieces:
            toks = _enc().encode(piece)
            # A single sentence longer than a whole chunk: hard cut on token boundaries.
            for i in range(0, len(toks), hard_cut):
                part = toks[i : i + hard_cut]
                units.append(Unit(_enc().decode(part), len(part), meta))
    return units


def chunk_segments(
    segments: list[tuple[str, dict]],
    max_tokens: int = config.CHUNK_TOKENS,
    overlap: int = config.CHUNK_OVERLAP,
) -> list[Chunk]:
    units = [u for text, meta in segments for u in _split_units(text, meta, max_tokens, overlap)]
    chunks: list[Chunk] = []
    current: list[Unit] = []
    size = 0
    fresh = 0  # units in `current` that weren't carried over as overlap

    def emit() -> None:
        chunks.append(Chunk("\n\n".join(u.text for u in current), dict(current[0].meta)))

    for unit in units:
        # +2 approximates the "\n\n" separator between units.
        if current and size + unit.tokens + 2 > max_tokens:
            emit()
            tail: list[Unit] = []
            tail_size = 0
            for u in reversed(current):
                if tail_size + u.tokens > overlap:
                    break
                tail.insert(0, u)
                tail_size += u.tokens
            if not tail:
                # Last unit alone exceeds the overlap budget: carry its final `overlap` tokens.
                last = current[-1]
                toks = _enc().encode(last.text)[-overlap:]
                tail = [Unit(_enc().decode(toks), len(toks), last.meta)]
                tail_size = len(toks)
            # Drop overlap that would leave no room for the incoming unit.
            while tail and tail_size + unit.tokens + 2 > max_tokens:
                tail_size -= tail.pop(0).tokens
            current, size, fresh = tail, tail_size, 0
        current.append(unit)
        size += unit.tokens + 2
        fresh += 1

    if current and fresh:
        emit()
    return chunks
