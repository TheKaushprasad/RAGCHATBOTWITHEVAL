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

CHAT_MODEL = os.environ.get("CHAT_MODEL", _DEFAULTS[PROVIDER]["chat"])
EMBED_MODEL = os.environ.get("EMBED_MODEL", _DEFAULTS[PROVIDER]["embed"])
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", CHAT_MODEL)  # used by eval_answers.py only
EMBED_DIM = int(os.environ.get("EMBED_DIM", "768"))  # must match vector(768) in schema.sql

# Retrieval / chunking knobs. tune.py searches over these; copy its winners into .env.
RETRIEVAL_MODE = os.environ.get("RETRIEVAL_MODE", "vector")  # "vector" or "hybrid"
TOP_K = int(os.environ.get("TOP_K", "5"))
MIN_SIMILARITY = float(os.environ.get("MIN_SIMILARITY", "0.30"))
CHUNK_TOKENS = int(os.environ.get("CHUNK_TOKENS", "500"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "50"))

IDK = "I don't know"
