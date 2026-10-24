import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # make `rag` importable on Vercel and under uvicorn

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile  # noqa: E402
from fastapi.responses import StreamingResponse  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from rag import auth, config, followup, history, llm, pipeline, store  # noqa: E402
from rag.uploads import UploadError, ingest_upload, user_namespace  # noqa: E402

# INFO logs go to stdout, which Vercel keeps in the deployment's runtime logs.
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("queryva.chat")
for noisy in ("httpx", "httpx2", "httpcore", "hpack"):  # per-request client logs would bury ours
    logging.getLogger(noisy).setLevel(logging.WARNING)

app = FastAPI(title="Queryva")


# --- auth -------------------------------------------------------------------------------

def current_user(authorization: str | None = Header(default=None)) -> dict:
    """Every data endpoint requires a valid Supabase access token."""
    try:
        return auth.verify(auth.bearer(authorization))
    except auth.AuthError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


def upstream(e: Exception) -> HTTPException:
    """Log the real error server-side; show the user a plain message (no database internals)."""
    print(f"[queryva] upstream error: {type(e).__name__}: {e}", file=sys.stderr)
    return HTTPException(status_code=502, detail="Something went wrong on our side. Please try again in a moment.")


# --- models -----------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: uuid.UUID | None = None  # omit to start a new conversation


class Citation(BaseModel):
    n: int
    source: str
    chunk_index: int
    page: int | None = None
    heading: str | None = None
    snippet: str
    similarity: float
    uploaded: bool = False  # True when the chunk comes from the user's own upload


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]  # only the chunks the answer cites
    retrieved: list[Citation]  # everything retrieved, for debugging
    grounded: bool  # False when we answered "I don't know"
    conversation_id: str
    answer_id: str  # pass back with /api/feedback
    searched_for: str | None = None  # the standalone question used, when a follow-up was rewritten


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


class RenameRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)


# --- public -----------------------------------------------------------------------------

@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "provider": config.PROVIDER,
        "chat_model": config.CHAT_MODEL,
        "embed_model": config.EMBED_MODEL,
        "retrieval_mode": config.RETRIEVAL_MODE,
        "top_k": config.TOP_K,
        "reranker": config.RERANKER,
        "rerank_candidates": config.RERANK_CANDIDATES,
        "min_similarity": config.MIN_SIMILARITY,
    }


@app.get("/api/public-config")
def public_config() -> dict:
    """What the browser needs to talk to Supabase Auth. The anon key is public by design."""
    if not (config.SUPABASE_URL and config.SUPABASE_ANON_KEY):
        raise HTTPException(status_code=500, detail="Auth isn't configured (SUPABASE_URL / SUPABASE_ANON_KEY).")
    return {"supabase_url": config.SUPABASE_URL, "supabase_anon_key": config.SUPABASE_ANON_KEY}


# --- chat + history ---------------------------------------------------------------------

def _begin(req: ChatRequest, user: dict, timings: dict) -> tuple[str, str, str | None]:
    """Check ownership and rewrite a follow-up into a standalone query. Returns (question, standalone, conv_id)."""
    question = req.message.strip()
    standalone, turns = question, []
    conv_id = str(req.conversation_id) if req.conversation_id else None
    if conv_id:
        if not history.owns(user["id"], conv_id):
            raise HTTPException(status_code=404, detail="Conversation not found.")
        # Follow-ups like "and how do you fix it?" are rewritten into a standalone question
        # so retrieval searches for the right thing.
        t = time.perf_counter()
        turns = history.recent_turns(user["id"], conv_id, n=config.REWRITE_TURNS)
        standalone = followup.rewrite(question, turns)
        timings["rewrite"] = time.perf_counter() - t
    log.info("query original=%r rewritten=%r turns=%d conversation=%s", question, standalone,
             len(turns), conv_id or "new")
    return question, standalone, conv_id


def _save(user: dict, conv_id: str | None, question: str, result: dict, timings: dict) -> tuple[str, str]:
    """Store the exchange; creates the conversation for a first message. Returns (conv_id, answer_id)."""
    t = time.perf_counter()
    answer_id = str(uuid.uuid4())
    is_new = not conv_id
    # Create the conversation only once there's an answer, so failures don't leave empty chats.
    if is_new:
        conv_id = history.create_conversation(user["id"], question)["id"]
    try:
        history.add_exchange(user["id"], conv_id, question, result, answer_id)
    except Exception:
        if is_new:
            history.delete_conversation(user["id"], conv_id)
        raise
    timings["save"] = time.perf_counter() - t
    return conv_id, answer_id


def _log_timings(timings: dict, started: float, streamed: bool) -> None:
    """One line per answer with seconds per stage; scripts/latency_report.py turns these into p50/p95."""
    timings["total"] = time.perf_counter() - started
    log.info("timing streamed=%s %s", streamed, " ".join(f"{k}={v:.3f}" for k, v in timings.items()))


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user: dict = Depends(current_user)) -> ChatResponse:
    started, timings = time.perf_counter(), {}
    try:
        question, standalone, conv_id = _begin(req, user, timings)
        # Users search only their own uploads; the shared AI PM notes are for the evals and demo numbers.
        result = pipeline.answer_question(standalone, session_ns=user_namespace(user["id"]), include_public=False,
                                          timings=timings)
        conv_id, answer_id = _save(user, conv_id, question, result, timings)
    except HTTPException:
        raise
    except Exception as e:  # quota errors, paused Supabase project
        raise upstream(e) from e
    _log_timings(timings, started, streamed=False)
    searched_for = standalone if standalone.strip().lower() != question.lower() else None
    return ChatResponse(**result, conversation_id=conv_id, answer_id=answer_id, searched_for=searched_for)


def _sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest, user: dict = Depends(current_user)) -> StreamingResponse:
    """Same as /api/chat, but streams the answer as server-sent events:
    `token` {"text"} while the answer is written, then `done` with the full ChatResponse, or `error` {"detail"}."""
    started, timings = time.perf_counter(), {}
    try:
        question, standalone, conv_id = _begin(req, user, timings)  # errors here are plain HTTP errors
    except HTTPException:
        raise
    except Exception as e:
        raise upstream(e) from e

    def events():
        try:
            chunks, result = pipeline.prepare(standalone, session_ns=user_namespace(user["id"]),
                                              include_public=False, timings=timings)
            if result is None:
                t, parts = time.perf_counter(), []
                for delta in llm.stream_answer(standalone, chunks):
                    if not parts:
                        timings["first_token"] = time.perf_counter() - started
                    parts.append(delta)
                    yield _sse("token", {"text": delta})
                timings["answer"] = time.perf_counter() - t
                result = pipeline.finish("".join(parts), chunks)
            new_conv, answer_id = _save(user, conv_id, question, result, timings)
        except Exception as e:  # noqa: BLE001 - reported to the client as an event; the stream has started
            yield _sse("error", {"detail": upstream(e).detail})
            return
        _log_timings(timings, started, streamed=True)
        searched_for = standalone if standalone.strip().lower() != question.lower() else None
        done = ChatResponse(**result, conversation_id=new_conv, answer_id=answer_id, searched_for=searched_for)
        yield _sse("done", done.model_dump(mode="json"))

    # X-Accel-Buffering stops proxies from holding the stream until it ends.
    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/conversations")
def conversations(user: dict = Depends(current_user)) -> dict:
    try:
        return {"conversations": history.list_conversations(user["id"])}
    except Exception as e:
        raise upstream(e) from e


@app.get("/api/conversations/{conversation_id}")
def conversation(conversation_id: uuid.UUID, user: dict = Depends(current_user)) -> dict:
    try:
        if not history.owns(user["id"], str(conversation_id)):
            raise HTTPException(status_code=404, detail="Conversation not found.")
        return {"id": str(conversation_id), "messages": history.get_messages(user["id"], str(conversation_id))}
    except HTTPException:
        raise
    except Exception as e:
        raise upstream(e) from e


@app.post("/api/conversations/{conversation_id}/suggestions")
def suggestions(conversation_id: uuid.UUID, user: dict = Depends(current_user)) -> dict:
    """Three follow-up questions answerable from the passages the latest answer used."""
    try:
        last = history.last_exchange(user["id"], str(conversation_id))
        if not last or not last["grounded"]:
            return {"questions": []}
        passages = [c.get("snippet", "") for c in last["citations"]]
        return {"questions": followup.suggest(last["question"], last["answer"], passages)}
    except Exception as e:
        raise upstream(e) from e


@app.delete("/api/conversations")
def delete_all_conversations(user: dict = Depends(current_user)) -> dict:
    history.delete_all(user["id"])
    return {"ok": True}


@app.patch("/api/conversations/{conversation_id}")
def rename(conversation_id: uuid.UUID, req: RenameRequest, user: dict = Depends(current_user)) -> dict:
    history.rename_conversation(user["id"], str(conversation_id), req.title)
    return {"ok": True}


@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: uuid.UUID, user: dict = Depends(current_user)) -> dict:
    history.delete_conversation(user["id"], str(conversation_id))  # scoped to the user: others' ids are a no-op
    return {"deleted": str(conversation_id)}


# --- feedback ---------------------------------------------------------------------------

@app.post("/api/feedback")
def feedback(req: FeedbackRequest, user: dict = Depends(current_user)) -> dict:
    try:
        if req.rating == 0:
            store.delete_feedback(str(req.answer_id), user["id"])
        else:
            store.save_feedback({
                "answer_id": str(req.answer_id),
                "user_id": user["id"],
                "rating": req.rating,
                "comment": (req.comment or "").strip() or None,
                "question": req.question,
                "answer": req.answer,
                "sources": [s.model_dump() for s in req.sources],
                "grounded": req.grounded,
                "config": {
                    "provider": config.PROVIDER, "chat_model": config.CHAT_MODEL,
                    "embed_model": config.EMBED_MODEL, "retrieval_mode": config.RETRIEVAL_MODE,
                    "top_k": config.TOP_K,
        "reranker": config.RERANKER,
        "rerank_candidates": config.RERANK_CANDIDATES, "min_similarity": config.MIN_SIMILARITY,
                    "chunk_tokens": config.CHUNK_TOKENS, "chunk_overlap": config.CHUNK_OVERLAP,
                },
            })
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except Exception as e:
        raise upstream(e) from e
    return {"ok": True, "rating": req.rating}


# --- documents --------------------------------------------------------------------------

@app.get("/api/documents")
def documents(user: dict = Depends(current_user)) -> dict:
    try:
        return {
            "uploads": store.list_sources(user_namespace(user["id"])),
            "limits": {"max_mb": config.UPLOAD_MAX_BYTES // (1024 * 1024), "max_files": config.UPLOAD_MAX_FILES},
        }
    except Exception as e:
        raise upstream(e) from e


@app.post("/api/upload")
def upload(file: UploadFile = File(...), user: dict = Depends(current_user)) -> dict:
    data = file.file.read(config.UPLOAD_MAX_BYTES + 1)
    try:
        return ingest_upload(file.filename or "upload", data, user_namespace(user["id"]))
    except UploadError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise upstream(e) from e


@app.delete("/api/documents/{source}")
def delete_document(source: str, user: dict = Depends(current_user)) -> dict:
    store.delete_source(source, user_namespace(user["id"]))  # scoped to the user; shared docs can't be deleted
    return {"deleted": source}


# --- account ----------------------------------------------------------------------------

@app.delete("/api/account")
def delete_account(user: dict = Depends(current_user)) -> dict:
    """Delete the user's uploads, then the account itself (chats, messages and feedback cascade)."""
    try:
        store.client().table(store.TABLE).delete().eq("namespace", user_namespace(user["id"])).execute()
        store.client().auth.admin.delete_user(user["id"])
    except Exception as e:
        raise upstream(e) from e
    auth.forget(user["id"])
    return {"deleted": True}


# Local dev: serve the frontend from the same origin. On Vercel, public/ is served by the CDN.
if not os.environ.get("VERCEL"):
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=ROOT / "public", html=True), name="static")
