from functools import lru_cache

from supabase import Client, create_client

from rag import config

TABLE = "documents"


@lru_cache(maxsize=1)
def client() -> Client:
    return create_client(config._require("SUPABASE_URL"), config._require("SUPABASE_SERVICE_KEY"))


def existing_hashes(source: str) -> dict[int, str]:
    rows = client().table(TABLE).select("chunk_index,content_hash").eq("source", source).execute().data
    return {r["chunk_index"]: r["content_hash"] for r in rows}


def upsert_chunks(rows: list[dict], batch_size: int = 100) -> None:
    for i in range(0, len(rows), batch_size):
        client().table(TABLE).upsert(rows[i : i + batch_size], on_conflict="source,chunk_index").execute()


def delete_stale(source: str, keep_count: int) -> None:
    """Remove chunks past the new end of a source (the file got shorter)."""
    client().table(TABLE).delete().eq("source", source).gte("chunk_index", keep_count).execute()


def delete_sources_except(sources: set[str]) -> list[str]:
    """Remove every chunk whose source file no longer exists in docs/."""
    rows = client().table(TABLE).select("source").execute().data
    gone = sorted({r["source"] for r in rows} - sources)
    for s in gone:
        client().table(TABLE).delete().eq("source", s).execute()
    return gone


def reset() -> None:
    client().table(TABLE).delete().gte("id", 0).execute()


def match(query_embedding: list[float], k: int, query_text: str | None = None, mode: str = "vector") -> list[dict]:
    if mode == "hybrid":
        if not query_text:
            raise ValueError("hybrid search needs query_text")
        res = client().rpc("hybrid_search", {
            "query_text": query_text, "query_embedding": query_embedding, "match_count": k,
        }).execute()
    else:
        res = client().rpc("match_documents", {"query_embedding": query_embedding, "match_count": k}).execute()
    return res.data or []
