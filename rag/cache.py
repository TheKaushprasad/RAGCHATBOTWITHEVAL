"""Answer cache: the same standalone question over the same documents returns the stored answer.

Keyed per user by the normalised standalone question, the document filter, and every setting that changes
answers (models, retrieval, prompt). A user's entries are cleared whenever they upload or remove a file, and
expire after CACHE_TTL_HOURS. Needs the answer_cache table from supabase/schema.sql; until it exists (or on any
error) caching is skipped, never failing a question.
"""

import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone

from rag import config, llm, store

TABLE = "answer_cache"
_disabled = False  # set after the table turns out to be missing, to stop retrying every request


def _settings_fingerprint() -> str:
    parts = [config.PROVIDER, config.CHAT_MODEL, config.EMBED_MODEL, config.RETRIEVAL_MODE, config.TOP_K,
             config.RERANKER, config.RERANK_MODEL, config.RERANK_CANDIDATES, config.MIN_SIMILARITY,
             config.DOC_ORDER, llm.SYSTEM_PROMPT]
    return hashlib.sha256(json.dumps(parts, default=str).encode()).hexdigest()[:16]


def key(question: str, sources: list[str] | None) -> str:
    normalised = " ".join(question.lower().split()).rstrip("?.! ")
    payload = json.dumps([normalised, sorted(sources or []), _settings_fingerprint()])
    return hashlib.sha256(payload.encode()).hexdigest()


def _off(e: Exception) -> None:
    global _disabled
    if "PGRST205" in str(e) or TABLE in str(e):  # table not created yet
        _disabled = True
    print(f"answer cache skipped: {type(e).__name__}: {e}", file=sys.stderr)


def get(user_id: str, cache_key: str) -> dict | None:
    if not config.CACHE_ENABLED or _disabled:
        return None
    try:
        since = (datetime.now(timezone.utc) - timedelta(hours=config.CACHE_TTL_HOURS)).isoformat()
        rows = (store.client().table(TABLE).select("result").eq("user_id", user_id).eq("key", cache_key)
                .gte("created_at", since).limit(1).execute().data)
        return rows[0]["result"] if rows else None
    except Exception as e:  # noqa: BLE001
        _off(e)
        return None


def put(user_id: str, cache_key: str, result: dict) -> None:
    if not config.CACHE_ENABLED or _disabled:
        return
    try:
        store.client().table(TABLE).upsert(
            {"user_id": user_id, "key": cache_key, "result": result,
             "created_at": datetime.now(timezone.utc).isoformat()},
            on_conflict="user_id,key").execute()
    except Exception as e:  # noqa: BLE001
        _off(e)


def clear(user_id: str) -> None:
    """Forget a user's cached answers (their documents changed)."""
    if _disabled:
        return
    try:
        store.client().table(TABLE).delete().eq("user_id", user_id).execute()
    except Exception as e:  # noqa: BLE001
        _off(e)
