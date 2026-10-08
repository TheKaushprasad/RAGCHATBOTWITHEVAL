import os
import sys
import uuid
from pathlib import Path
from typing import Literal

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


class FeedbackSource(BaseModel):
    source: str = Field(max_length=200)
    chunk_index: int
    page: int | None = None


class FeedbackRequest(BaseModel):
    answer_id: uuid.UUID
    rating: Literal[-1, 0, 1]  # 0 removes a previous vote
    comment: str | None = Field(default=None, max_length=1000)
    question: str = Field(min_length=1, max_length=2000)
    answer: str = Field(min_length=1, max_length=8000)
    sources: list[FeedbackSource] = Field(default_factory=list, max_length=20)
    grounded: bool | None = None


@app.post("/api/feedback")
def feedback(req: FeedbackRequest) -> dict:
    try:
        if req.rating == 0:
            store.delete_feedback(str(req.answer_id))
        else:
            store.save_feedback({
                "answer_id": str(req.answer_id),
                "rating": req.rating,
                "comment": (req.comment or "").strip() or None,
                "question": req.question,
                "answer": req.answer,
                "sources": [s.model_dump() for s in req.sources],
                "grounded": req.grounded,
                "config": {
                    "provider": config.PROVIDER, "chat_model": config.CHAT_MODEL,
                    "embed_model": config.EMBED_MODEL, "retrieval_mode": config.RETRIEVAL_MODE,
                    "top_k": config.TOP_K, "min_similarity": config.MIN_SIMILARITY,
                    "chunk_tokens": config.CHUNK_TOKENS, "chunk_overlap": config.CHUNK_OVERLAP,
                },
            })
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}") from e
    return {"ok": True, "rating": req.rating}


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
