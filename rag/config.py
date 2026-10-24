import json
import os

try:  # python-dotenv is a dev dependency; on Vercel env vars come from the dashboard.
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


# "openai" or "gemini". Switching provider means re-running ingest.py (embeddings aren't comparable).
PROVIDER = os.environ.get("PROVIDER", "openai").lower()

_DEFAULTS = {
    "openai": {"chat": "gpt-4.1-mini", "embed": "text-embedding-3-small"},
    "gemini": {"chat": "gemini-2.5-flash", "embed": "gemini-embedding-001"},
}
if PROVIDER not in _DEFAULTS:
    raise RuntimeError(f"PROVIDER must be one of {sorted(_DEFAULTS)}, got {PROVIDER!r}")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
# Public (anon / publishable) key, sent to the browser for Supabase Auth only. Safe to expose: RLS blocks data access.
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

CHAT_MODEL = os.environ.get("CHAT_MODEL", _DEFAULTS[PROVIDER]["chat"])
EMBED_MODEL = os.environ.get("EMBED_MODEL", _DEFAULTS[PROVIDER]["embed"])
# Evals only. A judge from another provider (e.g. JUDGE_PROVIDER=gemini) avoids grading a model with its own family.
REASONING_EFFORT = os.environ.get("REASONING_EFFORT", "none")  # for GPT-5-family models (rag/llm.py)
JUDGE_PROVIDER = os.environ.get("JUDGE_PROVIDER", PROVIDER)
if JUDGE_PROVIDER not in _DEFAULTS:
    raise RuntimeError(f"JUDGE_PROVIDER must be one of {sorted(_DEFAULTS)}, got {JUDGE_PROVIDER!r}")
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", CHAT_MODEL if JUDGE_PROVIDER == PROVIDER else _DEFAULTS[JUDGE_PROVIDER]["chat"])
EMBED_DIM = int(os.environ.get("EMBED_DIM", "768"))  # must match vector(768) in schema.sql

# Retrieval / chunking knobs. tune.py searches over these; copy its winners into .env.
RETRIEVAL_MODE = os.environ.get("RETRIEVAL_MODE", "vector")  # "vector" or "hybrid"
TOP_K = int(os.environ.get("TOP_K", "5"))
MIN_SIMILARITY = float(os.environ.get("MIN_SIMILARITY", "0.224"))
# Reranking (rag/rerank.py): fetch RERANK_CANDIDATES by vector search, keep the TOP_K the reranker likes best.
RERANKER = os.environ.get("RERANKER", "none")  # "none", "llm", "cohere" or "bge" (local; not on Vercel)
if RERANKER not in ("none", "llm", "cohere", "bge"):
    raise RuntimeError(f"RERANKER must be none, llm, cohere or bge, got {RERANKER!r}")
RERANK_CANDIDATES = int(os.environ.get("RERANK_CANDIDATES", "20"))
DOC_ORDER = os.environ.get("DOC_ORDER", "on").lower() not in ("0", "off", "false", "no")  # LLM reads passages in document order
# One model setting per reranker, so the evals can compare several in one run.
RERANK_MODEL = os.environ.get("RERANK_MODEL", CHAT_MODEL)  # RERANKER=llm
COHERE_RERANK_MODEL = os.environ.get("COHERE_RERANK_MODEL", "rerank-v3.5")
BGE_RERANK_MODEL = os.environ.get("BGE_RERANK_MODEL", "BAAI/bge-reranker-base")

# Provider calls: attempts per call and per-request timeout. On Vercel (30 s function limit) a failing
# provider must give up fast enough for the fallback to answer; evals and ingestion can wait longer.
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3" if os.environ.get("VERCEL") else "6"))
LLM_TIMEOUT_S = float(os.environ.get("LLM_TIMEOUT_S", "20"))

# Fallback provider for chat calls (rewrite, rerank, answer) when the primary one fails. Embeddings can't fall
# back: the index is built with one provider's embeddings. Defaults to Gemini when a Gemini key is present.
FALLBACK_PROVIDER = os.environ.get("FALLBACK_PROVIDER", "gemini" if GEMINI_API_KEY and PROVIDER != "gemini" else "")
if FALLBACK_PROVIDER and FALLBACK_PROVIDER not in _DEFAULTS:
    raise RuntimeError(f"FALLBACK_PROVIDER must be one of {sorted(_DEFAULTS)}, got {FALLBACK_PROVIDER!r}")


def fallback_model(provider: str) -> str:
    return os.environ.get("FALLBACK_MODEL", _DEFAULTS[provider]["chat"])


# Follow-up rewriting (rag/followup.py) can use a different provider than the answers, e.g. REWRITE_PROVIDER=gemini.
REWRITE_PROVIDER = os.environ.get("REWRITE_PROVIDER", PROVIDER)
if REWRITE_PROVIDER not in _DEFAULTS:
    raise RuntimeError(f"REWRITE_PROVIDER must be one of {sorted(_DEFAULTS)}, got {REWRITE_PROVIDER!r}")
REWRITE_MODEL = os.environ.get("REWRITE_MODEL", CHAT_MODEL if REWRITE_PROVIDER == PROVIDER else _DEFAULTS[REWRITE_PROVIDER]["chat"])
REWRITE_TURNS = int(os.environ.get("REWRITE_TURNS", "3"))
COHERE_API_KEY = os.environ.get("COHERE_API_KEY", "")
# Contextual retrieval (rag/context.py): embed a one-sentence situating context with each chunk.
# Off by default: on the golden set it didn't beat rewriting + reranking (results/*/retrieval_compare.md history)
# and it adds ~12 s to an upload. Worth re-testing on documents whose chunks lack local context.
CONTEXTUAL = os.environ.get("CONTEXTUAL", "off").lower() not in ("0", "off", "false", "no")
CONTEXT_BATCH = int(os.environ.get("CONTEXT_BATCH", "10"))
UPLOAD_CONTEXT_BUDGET_S = float(os.environ.get("UPLOAD_CONTEXT_BUDGET_S", "12"))
CHUNK_TOKENS = int(os.environ.get("CHUNK_TOKENS", "350"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "50"))

IDK = "I don't know"

# Estimated cost: USD per million tokens (input, output). Check the provider's pricing page and override with
# PRICES_JSON='{"model": [in, out], ...}' when prices change.
PRICES = {
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1-nano": (0.10, 0.40),
    "text-embedding-3-small": (0.02, 0.0),
    **json.loads(os.environ.get("PRICES_JSON", "{}")),
}

# Admin dashboard (/admin/) and health check (/api/health/check, called by .github/workflows/health.yml).
ADMIN_EMAILS = {e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()}
HEALTH_CHECK_TOKEN = os.environ.get("HEALTH_CHECK_TOKEN", "")
ALERT_P95_S = float(os.environ.get("ALERT_P95_S", "12"))
ALERT_ERROR_RATE = float(os.environ.get("ALERT_ERROR_RATE", "0.05"))
ALERT_MIN_QUESTIONS = int(os.environ.get("ALERT_MIN_QUESTIONS", "5"))  # don't alert on a tiny sample

# Per-user question limits: every answer costs several model calls (rewrite, rerank, answer).
CHAT_LIMIT_PER_HOUR = int(os.environ.get("CHAT_LIMIT_PER_HOUR", "60"))
CHAT_LIMIT_PER_DAY = int(os.environ.get("CHAT_LIMIT_PER_DAY", "300"))

# Answer cache (rag/cache.py).
CACHE_ENABLED = os.environ.get("CACHE", "on").lower() not in ("0", "off", "false", "no")
CACHE_TTL_HOURS = float(os.environ.get("CACHE_TTL_HOURS", "168"))

# User uploads (private to the account, kept until deleted).
UPLOAD_MAX_BYTES = int(os.environ.get("UPLOAD_MAX_BYTES", str(4 * 1024 * 1024)))  # Vercel caps request bodies at 4.5 MB
# Larger files go straight from the browser to Supabase Storage (rag/files.py), so they skip Vercel's body limit.
FILE_MAX_BYTES = int(os.environ.get("FILE_MAX_BYTES", str(20 * 1024 * 1024)))
UPLOAD_MAX_FILES = int(os.environ.get("UPLOAD_MAX_FILES", "5"))  # per user
UPLOAD_MAX_CHUNKS = int(os.environ.get("UPLOAD_MAX_CHUNKS", "150"))  # per file (~50k tokens) - bounds embedding cost
UPLOAD_GLOBAL_MAX_CHUNKS = int(os.environ.get("UPLOAD_GLOBAL_MAX_CHUNKS", "5000"))  # all users combined
