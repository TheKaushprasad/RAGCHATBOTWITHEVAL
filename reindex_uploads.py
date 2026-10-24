"""Re-index users' uploaded files from their stored originals (after changing chunking, embeddings or context).

    python reindex_uploads.py --dry-run   # list what would be re-indexed
    python reindex_uploads.py

Files uploaded before originals were kept have no stored copy; they're listed and left as they are.
"""

import argparse

from rag import files, store
from rag.uploads import UploadError, ingest_upload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = store.client().table(store.TABLE).select("namespace,source").like("namespace", "user:%").execute().data
    docs = sorted({(r["namespace"], r["source"]) for r in rows})
    done = missing = failed = 0
    for namespace, source in docs:
        user_id = namespace.removeprefix("user:")
        if not files.exists(user_id, source):
            missing += 1
            print(f"  no original: {namespace} {source}")
            continue
        if args.dry_run:
            print(f"  would re-index: {namespace} {source}")
            continue
        try:
            r = ingest_upload(source, files.download(user_id, source), namespace, max_bytes=10**9)
            done += 1
            print(f"  re-indexed: {namespace} {source} ({r['chunks']} chunks)")
        except UploadError as e:
            failed += 1
            print(f"  failed: {namespace} {source}: {e}")
    print(f"\n{len(docs)} uploaded files: {done} re-indexed, {missing} without an original, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
