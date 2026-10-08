from datetime import datetime, timezone
from functools import lru_cache

from supabase import Client, create_client

from rag import config

TABLE = "documents"
PUBLIC = "public"  # shared docs from ingest.py; uploads live in "session:<uuid>" namespaces


@lru_cache(maxsize=1)
def client() -> Client:
    return create_client(config._require("SUPABASE_URL"), config._require("SUPABASE_SERVICE_KEY"))


def _now() -> str:
    # 'Z' form (no '+00:00') so the value is safe inside PostgREST or=(...) filters.
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _live() -> str:
    """Filter for rows that haven't expired: permanent (null) or expiring in the future."""
    return f"expires_at.is.null,expires_at.gt.{_now()}"


# --- ingestion (public namespace) -------------------------------------------------------

def existing_hashes(source: str, namespace: str = PUBLIC) -> dict[int, str]:
    rows = (client().table(TABLE).select("chunk_index,content_hash")
            .eq("namespace", namespace).eq("source", source).execute().data)
    return {r["chunk_index"]: r["content_hash"] for r in rows}


def upsert_chunks(rows: list[dict], batch_size: int = 100) -> None:
    for i in range(0, len(rows), batch_size):
        client().table(TABLE).upsert(rows[i : i + batch_size], on_conflict="namespace,source,chunk_index").execute()


def delete_stale(source: str, keep_count: int, namespace: str = PUBLIC) -> None:
    """Remove chunks past the new end of a source (the file got shorter)."""
    (client().table(TABLE).delete().eq("namespace", namespace).eq("source", source)
     .gte("chunk_index", keep_count).execute())


def delete_sources_except(sources: set[str]) -> list[str]:
    """Remove public chunks whose source file no longer exists in docs/."""
    rows = client().table(TABLE).select("source").eq("namespace", PUBLIC).execute().data
    gone = sorted({r["source"] for r in rows} - sources)
    for s in gone:
        delete_source(s, PUBLIC)
    return gone


def reset() -> None:
    """Wipe the public docs (visitor uploads are left alone)."""
    client().table(TABLE).delete().eq("namespace", PUBLIC).execute()


# --- uploads (per-user namespaces) ---------------------------------------------------

def delete_source(source: str, namespace: str) -> None:
    client().table(TABLE).delete().eq("namespace", namespace).eq("source", source).execute()


def purge_expired() -> None:
    client().table(TABLE).delete().lt("expires_at", _now()).execute()


def list_sources(namespace: str) -> list[dict]:
    """[{source, chunks, expires_at}] for one namespace, skipping expired rows."""
    q = client().table(TABLE).select("source,expires_at").eq("namespace", namespace)
    if namespace != PUBLIC:
        q = q.or_(_live())
    out: dict[str, dict] = {}
    for r in q.execute().data:
        d = out.setdefault(r["source"], {"source": r["source"], "chunks": 0, "expires_at": r["expires_at"]})
        d["chunks"] += 1
    return sorted(out.values(), key=lambda d: d["source"])


def upload_chunk_count() -> int:
    """Live uploaded chunks across all users (for the global abuse cap)."""
    res = (client().table(TABLE).select("id", count="exact", head=True)
           .neq("namespace", PUBLIC).or_(_live()).execute())
    return res.count or 0


# --- retrieval --------------------------------------------------------------------------

def match(query_embedding: list[float], k: int, query_text: str | None = None, mode: str = "vector",
          session_ns: str | None = None) -> list[dict]:
    """Top-k chunks from the public docs plus (if given) one user's uploads."""
    if mode == "hybrid":
        if not query_text:
            raise ValueError("hybrid search needs query_text")
        res = client().rpc("hybrid_search", {
            "query_text": query_text, "query_embedding": query_embedding, "match_count": k,
            "session_ns": session_ns,
        }).execute()
    else:
        res = client().rpc("match_documents", {
            "query_embedding": query_embedding, "match_count": k, "session_ns": session_ns,
        }).execute()
    return res.data or []


# --- answer feedback --------------------------------------------------------------------

FEEDBACK = "feedback"


def save_feedback(row: dict) -> None:
    """Insert or update the rating for one answer (keyed by answer_id), only if it's the user's own."""
    existing = client().table(FEEDBACK).select("user_id").eq("answer_id", row["answer_id"]).limit(1).execute().data
    if existing and existing[0]["user_id"] not in (None, row["user_id"]):
        raise PermissionError("This answer belongs to another user.")
    client().table(FEEDBACK).upsert({**row, "updated_at": _now()}, on_conflict="answer_id").execute()


def delete_feedback(answer_id: str, user_id: str) -> None:
    client().table(FEEDBACK).delete().eq("answer_id", answer_id).eq("user_id", user_id).execute()


def list_feedback(rating: int | None = None, limit: int = 1000) -> list[dict]:
    q = client().table(FEEDBACK).select("*").order("created_at", desc=True).limit(limit)
    if rating is not None:
        q = q.eq("rating", rating)
    return q.execute().data
