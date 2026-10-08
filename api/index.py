import os
import sys
import uuid
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # make `rag` importable on Vercel and under uvicorn

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from rag import auth, config, followup, history, pipeline, store  # noqa: E402
from rag.uploads import UploadError, ingest_upload, user_namespace  # noqa: E402

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
        "min_similarity": config.MIN_SIMILARITY,
    }


@app.get("/api/public-config")
def public_config() -> dict:
    """What the browser needs to talk to Supabase Auth. The anon key is public by design."""
    if not (config.SUPABASE_URL and config.SUPABASE_ANON_KEY):
        raise HTTPException(status_code=500, detail="Auth isn't configured (SUPABASE_URL / SUPABASE_ANON_KEY).")
    return {"supabase_url": config.SUPABASE_URL, "supabase_anon_key": config.SUPABASE_ANON_KEY}


# --- chat + history ---------------------------------------------------------------------

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user: dict = Depends(current_user)) -> ChatResponse:
    question = req.message.strip()
    try:
        standalone = question
        conv_id = str(req.conversation_id) if req.conversation_id else None
        if conv_id:
            if not history.owns(user["id"], conv_id):
                raise HTTPException(status_code=404, detail="Conversation not found.")
            # Follow-ups like "and how do you fix it?" are rewritten into a standalone question
            # so retrieval searches for the right thing.
            standalone = followup.rewrite(question, history.recent_turns(user["id"], conv_id))
        # Users search only their own uploads; the shared AI PM notes are for the evals and demo numbers.
        result = pipeline.answer_question(standalone, session_ns=user_namespace(user["id"]), include_public=False)
        answer_id = str(uuid.uuid4())
        # Create the conversation only once there's an answer, so failures don't leave empty chats.
        if not conv_id:
            conv_id = history.create_conversation(user["id"], question)["id"]
        try:
            history.add_exchange(user["id"], conv_id, question, result, answer_id)
        except Exception:
            if not req.conversation_id:
                history.delete_conversation(user["id"], conv_id)
            raise
    except HTTPException:
        raise
    except Exception as e:  # quota errors, paused Supabase project
        raise upstream(e) from e
    searched_for = standalone if standalone.strip().lower() != question.lower() else None
    return ChatResponse(**result, conversation_id=conv_id, answer_id=answer_id, searched_for=searched_for)


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
                    "top_k": config.TOP_K, "min_similarity": config.MIN_SIMILARITY,
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
