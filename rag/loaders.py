"""Turn documents into (text, meta) segments for the chunker.

Shared by ingest.py (files on disk) and the upload API (bytes from the browser).
Markdown and DOCX keep their section heading in meta; PDFs keep the page number.
"""

import io
import re
from pathlib import Path

from rag.chunking import Chunk

SUPPORTED = {".pdf", ".docx", ".md", ".markdown", ".mdx", ".txt"}

Segments = list[tuple[str, dict]]


def load_pdf(data: bytes) -> Segments:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    segments = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if _one_word_per_line(text):
            # Some exporters (e.g. Google Docs) place every word separately, so plain extraction
            # yields "What\n \nis\n \nan". Layout mode reassembles real lines.
            text = page.extract_text(extraction_mode="layout") or ""
            text = "\n".join(re.sub(r" {2,}", " ", ln).strip() for ln in text.splitlines())
            text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()
        if text:
            segments.append((text, {"page": i}))
    return segments


def _one_word_per_line(text: str) -> bool:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return len(lines) > 20 and sum(len(ln.split()) for ln in lines) / len(lines) < 1.5


def load_markdown(text: str) -> Segments:
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)  # strip YAML front matter
    segments: Segments = []
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


def load_docx(data: bytes) -> Segments:
    """Word → markdown-style text (headings as #, tables as | rows |), then split like markdown."""
    from docx import Document
    from docx.table import Table

    doc = Document(io.BytesIO(data))
    lines: list[str] = []
    for block in doc.iter_inner_content():  # paragraphs and tables in document order
        if isinstance(block, Table):
            for row in block.rows:
                cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                # Merged cells repeat across a row; drop consecutive duplicates.
                cells = [c for i, c in enumerate(cells) if i == 0 or c != cells[i - 1]]
                if any(cells):
                    lines.append("| " + " | ".join(cells) + " |")
            lines.append("")
            continue
        text = block.text.strip()
        if not text:
            lines.append("")
            continue
        style = (block.style.name if block.style is not None else "").lower()
        m = re.match(r"heading (\d)", style)
        if m or style == "title":
            level = int(m.group(1)) if m else 1
            lines += ["", "#" * min(level, 6) + " " + text, ""]
        elif "list" in style:
            lines.append(f"- {text}")
        else:
            lines += [text, ""]
    return load_markdown("\n".join(lines))


def load_bytes(filename: str, data: bytes) -> Segments:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return load_pdf(data)
    if ext == ".docx":
        return load_docx(data)
    if ext in SUPPORTED:
        return load_markdown(data.decode("utf-8", errors="replace"))
    raise ValueError(f"Unsupported file type {ext!r}. Supported: {', '.join(sorted(SUPPORTED))}")


def load(path: Path) -> Segments:
    return load_bytes(path.name, path.read_bytes())


def embed_text(source: str, chunk: Chunk) -> str:
    # Prefixing the file name and section gives the embedding context the chunk text may lack.
    header = source + (f" — {chunk.meta['heading']}" if chunk.meta.get("heading") else "")
    return f"{header}\n\n{chunk.text}"
