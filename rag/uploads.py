"""Visitor uploads: parse → chunk → embed → store in the visitor's private namespace."""

import hashlib
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from rag import config, store
from rag.chunking import chunk_segments
from rag.embeddings import embed_documents, model_id
from rag.loaders import SUPPORTED, embed_text, load_bytes


class UploadError(ValueError):
    """A problem with the upload the visitor can fix (shown to them as-is)."""


def session_namespace(session_id: str | None) -> str | None:
    """Map the browser's session id to a namespace. Only well-formed UUIDs are accepted."""
    if not session_id:
        return None
    try:
        return f"session:{uuid.UUID(session_id)}"
    except ValueError:
        raise UploadError("Invalid session id.") from None


def clean_filename(name: str) -> str:
    name = Path(name or "").name  # drop any client-supplied directories
    name = re.sub(r"[^\w.\- ()]", "_", name).strip() or "upload"
    stem, ext = Path(name).stem[:80], Path(name).suffix.lower()
    return f"{stem}{ext}"


def ingest_upload(filename: str, data: bytes, namespace: str) -> dict:
    source = clean_filename(filename)
    ext = Path(source).suffix.lower()
    if ext not in SUPPORTED:
        raise UploadError(f"Unsupported file type. Upload one of: {', '.join(sorted(SUPPORTED))}")
    if not data:
        raise UploadError("The file is empty.")
    if len(data) > config.UPLOAD_MAX_BYTES:
        raise UploadError(f"File is larger than {config.UPLOAD_MAX_BYTES // (1024 * 1024)} MB.")

    store.purge_expired()
    existing = {d["source"] for d in store.list_sources(namespace)}
    if source not in existing and len(existing) >= config.UPLOAD_MAX_FILES:
        raise UploadError(f"You can have at most {config.UPLOAD_MAX_FILES} uploaded files. Remove one first.")

    try:
        segments = load_bytes(source, data)
    except Exception as e:
        raise UploadError(f"Couldn't read {source}: {e}") from e
    chunks = chunk_segments(segments)
    if not chunks:
        raise UploadError(f"No text found in {source} (scanned PDFs without a text layer aren't supported).")
    if len(chunks) > config.UPLOAD_MAX_CHUNKS:
        raise UploadError(f"{source} is too long for the demo ({len(chunks)} chunks; limit {config.UPLOAD_MAX_CHUNKS}).")
    if store.upload_chunk_count() + len(chunks) > config.UPLOAD_GLOBAL_MAX_CHUNKS:
        raise UploadError("The demo's upload storage is full right now. Please try again later.")

    texts = [embed_text(source, c) for c in chunks]
    vectors = embed_documents(texts)
    expires = datetime.now(timezone.utc) + timedelta(hours=config.UPLOAD_TTL_HOURS)

    store.delete_source(source, namespace)  # re-uploading a file replaces it
    store.upsert_chunks([
        {
            "namespace": namespace,
            "source": source,
            "chunk_index": i,
            "page": c.meta.get("page"),
            "content": c.text,
            "content_hash": hashlib.sha256(f"{model_id()}\n{t}".encode()).hexdigest(),
            "metadata": c.meta,
            "embedding": v,
            "expires_at": expires.isoformat(),
        }
        for i, (c, t, v) in enumerate(zip(chunks, texts, vectors))
    ])
    return {"source": source, "chunks": len(chunks), "expires_at": expires.isoformat()}
