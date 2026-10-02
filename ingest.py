"""Load PDFs/markdown from docs/, chunk, embed with Gemini, upsert to Supabase.

    python ingest.py              # incremental: only re-embeds chunks whose text changed
    python ingest.py --reset      # wipe the table first
    python ingest.py --dry-run    # chunk only; print stats, no API calls
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path

from rag import config
from rag.chunking import Chunk, chunk_segments, count_tokens
from rag.embeddings import model_id

SUPPORTED = {".pdf", ".md", ".markdown", ".mdx", ".txt"}


def load_pdf(path: Path) -> list[tuple[str, dict]]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    segments = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            segments.append((text, {"page": i}))
    return segments


def load_markdown(path: Path) -> list[tuple[str, dict]]:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)  # strip YAML front matter
    segments: list[tuple[str, dict]] = []
    heading = ""
    buf: list[str] = []
    in_code = False

    def flush() -> None:
        body = "\n".join(buf).strip()
        if body:
            segments.append((body, {"heading": heading} if heading else {}))
        buf.clear()

    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
        m = None if in_code else re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            flush()
            heading = m.group(2).strip()
        buf.append(line)  # headings stay in the text so chunks carry their section title
    flush()
    return segments


def load(path: Path) -> list[tuple[str, dict]]:
    return load_pdf(path) if path.suffix.lower() == ".pdf" else load_markdown(path)


def embed_text(source: str, chunk: Chunk) -> str:
    # Prefixing the file name and section gives the embedding context the chunk text may lack.
    header = source + (f" — {chunk.meta['heading']}" if chunk.meta.get("heading") else "")
    return f"{header}\n\n{chunk.text}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default="docs", help="folder to ingest (default: docs)")
    ap.add_argument("--reset", action="store_true", help="delete all rows before ingesting")
    ap.add_argument("--dry-run", action="store_true", help="chunk only, no embedding or DB writes")
    args = ap.parse_args()

    root = Path(args.docs)
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED)
    if not files:
        print(f"No supported files in {root}/ ({', '.join(sorted(SUPPORTED))})")
        return 1

    if not args.dry_run:
        from rag import store
        from rag.embeddings import embed_documents

        if args.reset:
            store.reset()
            print("Table reset.")

    total_chunks = total_embedded = 0
    for path in files:
        source = path.relative_to(root).as_posix()
        chunks = chunk_segments(load(path))
        total_chunks += len(chunks)
        if not chunks:
            print(f"  {source}: no extractable text, skipped")
            continue

        texts = [embed_text(source, c) for c in chunks]
        # Hash includes the embedding model so switching provider/model re-embeds everything.
        hashes = [hashlib.sha256(f"{model_id()}\n{t}".encode()).hexdigest() for t in texts]

        if args.dry_run:
            sizes = [count_tokens(c.text) for c in chunks]
            print(f"  {source}: {len(chunks)} chunks, tokens min/avg/max = "
                  f"{min(sizes)}/{sum(sizes) // len(sizes)}/{max(sizes)}")
            continue

        old = store.existing_hashes(source)
        todo = [i for i, h in enumerate(hashes) if old.get(i) != h]
        if todo:
            vectors = embed_documents([texts[i] for i in todo])
            rows = [
                {
                    "source": source,
                    "chunk_index": i,
                    "page": chunks[i].meta.get("page"),
                    "content": chunks[i].text,
                    "content_hash": hashes[i],
                    "metadata": chunks[i].meta,
                    "embedding": vec,
                }
                for i, vec in zip(todo, vectors)
            ]
            store.upsert_chunks(rows)
        store.delete_stale(source, len(chunks))
        total_embedded += len(todo)
        print(f"  {source}: {len(chunks)} chunks ({len(todo)} embedded, {len(chunks) - len(todo)} unchanged)")

    if not args.dry_run:
        gone = store.delete_sources_except({p.relative_to(root).as_posix() for p in files})
        for s in gone:
            print(f"  {s}: removed (file no longer in {root}/)")

    print(f"Done: {len(files)} files, {total_chunks} chunks, {total_embedded} embedded "
          f"({model_id()}, chunks {config.CHUNK_TOKENS}/{config.CHUNK_OVERLAP} tokens).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
