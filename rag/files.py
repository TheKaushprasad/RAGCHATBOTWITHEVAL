"""Original uploaded files, kept in a private Supabase Storage bucket at <user id>/<file name>.

Keeping the original lets the app open the document at a cited page, re-index files when chunking or
embedding settings change, and accept files larger than Vercel's ~4.5 MB request limit: the browser uploads
those straight to storage with a one-time signed URL, then asks the API to index them.

The server makes every storage call with the service key and decides every path, so the bucket needs no
client-side policies. Storage problems never fail an upload that has already been indexed.
"""

import sys

from rag import store

BUCKET = "documents"
CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".mdx": "text/markdown",
    ".txt": "text/plain",
}


def _bucket():
    return store.client().storage.from_(BUCKET)


def path(user_id: str, source: str) -> str:
    return f"{user_id}/{source}"


def content_type(source: str) -> str:
    return CONTENT_TYPES.get("." + source.rsplit(".", 1)[-1].lower(), "application/octet-stream")


def ensure_bucket(max_bytes: int) -> None:
    """Create the private bucket if it doesn't exist (idempotent)."""
    names = {b.name for b in store.client().storage.list_buckets()}
    if BUCKET not in names:
        store.client().storage.create_bucket(BUCKET, options={"public": False, "file_size_limit": max_bytes})


def save(user_id: str, source: str, data: bytes) -> bool:
    try:
        _bucket().upload(path(user_id, source), data,
                         file_options={"content-type": content_type(source), "upsert": "true"})
        return True
    except Exception as e:  # noqa: BLE001 - the file is already indexed; the original is a convenience
        print(f"[queryva] couldn't store original {source}: {type(e).__name__}: {e}", file=sys.stderr)
        return False


def signed_upload(user_id: str, source: str) -> dict:
    """One-time URL the browser can PUT the file to. Returns {"url", "path", "token"}."""
    res = _bucket().create_signed_upload_url(path(user_id, source))
    return {"url": res["signed_url"], "path": res["path"], "token": res["token"]}


def download(user_id: str, source: str) -> bytes:
    return _bucket().download(path(user_id, source))


def signed_url(user_id: str, source: str, seconds: int = 600) -> str:
    res = _bucket().create_signed_url(path(user_id, source), seconds)
    return res.get("signedURL") or res.get("signedUrl") or res["signed_url"]


def exists(user_id: str, source: str) -> bool:
    try:
        return any(f["name"] == source for f in _bucket().list(user_id, {"search": source}))
    except Exception:  # noqa: BLE001
        return False


def remove(user_id: str, sources: list[str]) -> None:
    try:
        if sources:
            _bucket().remove([path(user_id, s) for s in sources])
    except Exception as e:  # noqa: BLE001 - deleting the index entry matters more than the stored copy
        print(f"[queryva] couldn't remove stored files: {type(e).__name__}: {e}", file=sys.stderr)


def remove_all(user_id: str) -> None:
    try:
        names = [f["name"] for f in _bucket().list(user_id, {"limit": 1000})]
        remove(user_id, names)
    except Exception as e:  # noqa: BLE001
        print(f"[queryva] couldn't list stored files: {type(e).__name__}: {e}", file=sys.stderr)
