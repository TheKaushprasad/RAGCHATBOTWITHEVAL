import math
import time
from functools import lru_cache

from rag import config

BATCH_SIZE = 100


def _normalize(vec: list[float]) -> list[float]:
    # Truncated embeddings aren't guaranteed unit length; normalize for consistent cosine scores.
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _retry(fn, max_retries: int = 6):
    """Call fn(), backing off on rate limits (429), transient 5xx errors and dropped connections."""
    delay = 2.0
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            status = getattr(e, "status_code", None) or getattr(e, "code", None)
            # Connection drops and timeouts have no status code (openai.APIConnectionError, httpx errors).
            dropped = any(t in type(e).__name__ for t in ("Connection", "Timeout"))
            transient = dropped or (isinstance(status, int) and (status == 429 or status >= 500))
            if transient and attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise


# --- OpenAI -----------------------------------------------------------------------------

@lru_cache(maxsize=1)
def openai_client():
    from openai import OpenAI

    return OpenAI(api_key=config._require("OPENAI_API_KEY"), max_retries=0)


def _embed_openai(texts: list[str], task_type: str) -> list[list[float]]:
    # OpenAI embeddings are symmetric, so task_type is unused.
    res = _retry(lambda: openai_client().embeddings.create(
        model=config.EMBED_MODEL, input=texts, dimensions=config.EMBED_DIM))
    return [_normalize(d.embedding) for d in sorted(res.data, key=lambda d: d.index)]


# --- Gemini -----------------------------------------------------------------------------

@lru_cache(maxsize=1)
def gemini_client():
    from google import genai

    return genai.Client(api_key=config._require("GEMINI_API_KEY"))


def _embed_gemini(texts: list[str], task_type: str) -> list[list[float]]:
    from google.genai import types

    cfg = types.EmbedContentConfig(task_type=task_type, output_dimensionality=config.EMBED_DIM)
    res = _retry(lambda: gemini_client().models.embed_content(
        model=config.EMBED_MODEL, contents=texts, config=cfg))
    return [_normalize(e.values) for e in res.embeddings]


# --- public API -------------------------------------------------------------------------

def _embed(texts: list[str], task_type: str) -> list[list[float]]:
    fn = _embed_openai if config.PROVIDER == "openai" else _embed_gemini
    out: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        out.extend(fn(texts[i : i + BATCH_SIZE], task_type))
    return out


def embed_documents(texts: list[str]) -> list[list[float]]:
    return _embed(texts, "RETRIEVAL_DOCUMENT")


def embed_query(text: str) -> list[float]:
    return _embed([text], "RETRIEVAL_QUERY")[0]


def model_id() -> str:
    """Identifies the embedding space; part of each chunk's hash so a model change forces re-embedding."""
    return f"{config.PROVIDER}:{config.EMBED_MODEL}:{config.EMBED_DIM}"
