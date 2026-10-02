import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # make `rag` importable on Vercel and under uvicorn

from fastapi import FastAPI, HTTPException  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from rag import config, pipeline  # noqa: E402

app = FastAPI(title="RAG chatbot")


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


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]  # only the chunks the answer cites
    retrieved: list[Citation]  # everything retrieved, for debugging
    grounded: bool  # False when we answered "I don't know"


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
def chat(req: ChatRequest) -> ChatResponse:
    try:
        return ChatResponse(**pipeline.answer_question(req.message.strip()))
    except Exception as e:  # quota errors, paused Supabase project, missing env vars
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}") from e


# Local dev: serve the frontend from the same origin. On Vercel, public/ is served by the CDN.
if not os.environ.get("VERCEL"):
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=ROOT / "public", html=True), name="static")
