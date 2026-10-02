import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # make `rag` importable on Vercel and under uvicorn

from fastapi import FastAPI, File, Header, HTTPException, UploadFile  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from rag import config, pipeline, store  # noqa: E402
from rag.uploads import UploadError, ingest_upload, session_namespace  # noqa: E402

app = FastAPI(title="Queryva")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class Citation(BaseModel):
    n: int
    source: str
    chunk_index: int
    page: int | None = None
    heading: str | None = None
    snippet: str
    similarity: float
    uploaded: bool = False  # True when the chunk comes from the visitor's own upload


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]  # only the chunks the answer cites
    retrieved: list[Citation]  # everything retrieved, for debugging
    grounded: bool  # False when we answered "I don't know"


def _namespace(session_id: str | None, required: bool = False) -> str | None:
    try:
        ns = session_namespace(session_id)
    except UploadError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if required and not ns:
        raise HTTPException(status_code=400, detail="Missing X-Session-Id header.")
    return ns


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "provider": config.PROVIDER,
        "chat_model": config.CHAT_MODEL,
        "embed_model": config.EMBED_MODEL,
        "retrieval_mode": config.RETRIEVAL_MODE,
        "top_k": config.TOP_K,
        "min_similarity": config.MIN_SIMILARITY,
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest, x_session_id: str | None = Header(default=None)) -> ChatResponse:
    ns = _namespace(x_session_id)
    try:
        return ChatResponse(**pipeline.answer_question(req.message.strip(), session_ns=ns))
    except Exception as e:  # quota errors, paused Supabase project, missing env vars
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}") from e


@app.get("/api/documents")
def documents(x_session_id: str | None = Header(default=None)) -> dict:
    ns = _namespace(x_session_id)
    try:
        return {
            "sample": store.list_sources(store.PUBLIC),
            "uploads": store.list_sources(ns) if ns else [],
            "limits": {
                "max_mb": config.UPLOAD_MAX_BYTES // (1024 * 1024),
                "max_files": config.UPLOAD_MAX_FILES,
                "ttl_hours": config.UPLOAD_TTL_HOURS,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}") from e


@app.post("/api/upload")
def upload(file: UploadFile = File(...), x_session_id: str | None = Header(default=None)) -> dict:
    ns = _namespace(x_session_id, required=True)
    data = file.file.read(config.UPLOAD_MAX_BYTES + 1)
    try:
        return ingest_upload(file.filename or "upload", data, ns)
    except UploadError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}") from e


@app.delete("/api/documents/{source}")
def delete_document(source: str, x_session_id: str | None = Header(default=None)) -> dict:
    ns = _namespace(x_session_id, required=True)
    store.delete_source(source, ns)  # scoped to the caller's namespace; public docs can't be deleted
    return {"deleted": source}


# Local dev: serve the frontend from the same origin. On Vercel, public/ is served by the CDN.
if not os.environ.get("VERCEL"):
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=ROOT / "public", html=True), name="static")
