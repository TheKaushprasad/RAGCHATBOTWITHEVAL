import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # make `rag` importable on Vercel and under uvicorn

from fastapi import BackgroundTasks, Depends, FastAPI, File, Header, HTTPException, UploadFile  # noqa: E402
from fastapi.responses import StreamingResponse  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from rag import auth, cache, config, files, followup, history, llm, metrics, pii, pipeline, store, usage  # noqa: E402
from rag.uploads import UploadError, check_new_upload, ingest_upload, user_namespace  # noqa: E402

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
    sources: list[str] | None = Field(default=None, max_length=20)  # search only these files (default: all)


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

_io = ThreadPoolExecutor(max_workers=8)  # independent database reads run side by side


def _check_rate_limit(times: list[datetime]) -> None:
    """429 once a user exceeds the hourly or daily question limit. `times`: their recent questions, newest first."""
    now = datetime.now(timezone.utc)
    for seconds, limit, period in ((3600, config.CHAT_LIMIT_PER_HOUR, "hour"), (86400, config.CHAT_LIMIT_PER_DAY, "day")):
        window = [t for t in times if (now - t).total_seconds() < seconds]
        if len(window) >= limit:
            wait = max(60, seconds - (now - window[limit - 1]).total_seconds())  # until the oldest counted one ages out
            n, unit = (round(wait / 60), "minute") if wait < 5400 else (round(wait / 3600), "hour")
            when = f"{n} {unit}{'' if n == 1 else 's'}"
            raise HTTPException(status_code=429, headers={"Retry-After": str(int(wait))},
                                detail=f"You've reached the limit of {limit} questions per {period}. Try again in about {when}.")


def _begin(req: ChatRequest, user: dict, timings: dict) -> tuple[str, str, str | None]:
    """Rate limit, ownership and a standalone rewrite of follow-ups. Returns (question, standalone, conv_id)."""
    t = time.perf_counter()
    question = req.message.strip()
    conv_id = str(req.conversation_id) if req.conversation_id else None
    # The three reads don't depend on each other, so they run in parallel (each is a round trip to Supabase).
    times = _io.submit(history.question_times, user["id"], 86400, max(config.CHAT_LIMIT_PER_DAY, config.CHAT_LIMIT_PER_HOUR))
    owned = _io.submit(history.owns, user["id"], conv_id) if conv_id else None
    recent = _io.submit(history.recent_turns, user["id"], conv_id, config.REWRITE_TURNS) if conv_id else None
    _check_rate_limit(times.result())
    if owned and not owned.result():
        raise HTTPException(status_code=404, detail="Conversation not found.")
    turns = recent.result() if recent else []
    timings["setup"] = time.perf_counter() - t
    standalone = question
    if turns:
        # Follow-ups like "and how do you fix it?" are rewritten into a standalone question
        # so retrieval searches for the right thing.
        t = time.perf_counter()
        standalone = followup.rewrite(question, turns)
        timings["rewrite"] = time.perf_counter() - t
    log.info("query original=%r rewritten=%r turns=%d conversation=%s", pii.redact(question), pii.redact(standalone),
             len(turns), conv_id or "new")
    return question, standalone, conv_id


def _save(user: dict, conv_id: str | None, question: str, result: dict, timings: dict,
          new_conv_id: str | None = None, answer_id: str | None = None) -> tuple[str, str]:
    """Store the exchange; creates the conversation (with `new_conv_id` if given) for a first message.
    Returns (conv_id, answer_id)."""
    t = time.perf_counter()
    answer_id = answer_id or str(uuid.uuid4())
    is_new = not conv_id
    # Create the conversation only once there's an answer, so failures don't leave empty chats.
    if is_new:
        conv_id = history.create_conversation(user["id"], question, new_conv_id)["id"]
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
def chat(req: ChatRequest, background: BackgroundTasks, user: dict = Depends(current_user)) -> ChatResponse:
    started, timings, totals = time.perf_counter(), {}, usage.new()
    try:
        with usage.track(totals):
            question, standalone, conv_id = _begin(req, user, timings)
            cache_key = cache.key(standalone, req.sources)
            result = _cached(user["id"], cache_key, timings)
            if result is None:
                # Users search only their own uploads; the shared AI PM notes are for the evals and demo numbers.
                result = pipeline.answer_question(standalone, session_ns=user_namespace(user["id"]),
                                                  include_public=False, timings=timings, sources=req.sources or None)
                cache.put(user["id"], cache_key, result)
            conv_id, answer_id = _save(user, conv_id, question, result, timings)
    except HTTPException:
        raise
    except Exception as e:  # quota errors, paused Supabase project
        timings["total"] = time.perf_counter() - started
        metrics.save(user["id"], timings, totals, streamed=False, grounded=None, error=type(e).__name__)
        raise upstream(e) from e
    _log_timings(timings, started, streamed=False)
    # Recorded after the response is sent, so the metrics write doesn't add latency.
    background.add_task(metrics.save, user["id"], timings, totals, streamed=False, grounded=result["grounded"])
    searched_for = standalone if standalone.strip().lower() != question.lower() else None
    return ChatResponse(**result, conversation_id=conv_id, answer_id=answer_id, searched_for=searched_for)


def _cached(user_id: str, cache_key: str, timings: dict) -> dict | None:
    t = time.perf_counter()
    hit = cache.get(user_id, cache_key)
    timings["cache"] = time.perf_counter() - t
    if hit is not None:
        timings["cache_hit"] = 1.0
    return hit


def _sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest, user: dict = Depends(current_user)) -> StreamingResponse:
    """Same as /api/chat, but streams the answer as server-sent events:
    `token` {"text"} while the answer is written, then `done` with the full ChatResponse, or `error` {"detail"}."""
    started, timings, totals = time.perf_counter(), {}, usage.new()
    try:
        with usage.track(totals):
            question, standalone, conv_id = _begin(req, user, timings)  # errors here are plain HTTP errors
    except HTTPException:
        raise
    except Exception as e:
        raise upstream(e) from e

    def events():
        # Each step of a streaming response runs in a fresh copy of the context, so usage tracking is
        # re-entered around every piece of work rather than held open across yields.
        try:
            with usage.track(totals):
                cache_key = cache.key(standalone, req.sources)
                result = _cached(user["id"], cache_key, timings)
                if result is None:
                    chunks, result = pipeline.prepare(standalone, session_ns=user_namespace(user["id"]),
                                                      include_public=False, timings=timings, sources=req.sources or None)
            if result is not None and timings.get("cache_hit"):
                yield _sse("token", {"text": result["answer"]})
            if result is None:
                t, parts = time.perf_counter(), []
                deltas = llm.stream_answer(standalone, chunks)
                while True:
                    with usage.track(totals):
                        delta = next(deltas, None)
                    if delta is None:
                        break
                    if not parts:
                        timings["first_token"] = time.perf_counter() - started
                    parts.append(delta)
                    yield _sse("token", {"text": delta})
                timings["answer"] = time.perf_counter() - t
                result = pipeline.finish("".join(parts), chunks)
        except Exception as e:  # noqa: BLE001 - reported to the client as an event; the stream has started
            timings["total"] = time.perf_counter() - started
            metrics.save(user["id"], timings, totals, streamed=True, grounded=None, error=type(e).__name__)
            yield _sse("error", {"detail": upstream(e).detail})
            return

        # Ids are chosen here so the client gets the complete answer before anything is written; the
        # conversation, cache entry and metrics are saved after the done event.
        new_conv, answer_id = conv_id or str(uuid.uuid4()), str(uuid.uuid4())
        _log_timings(timings, started, streamed=True)
        searched_for = standalone if standalone.strip().lower() != question.lower() else None
        done = ChatResponse(**result, conversation_id=new_conv, answer_id=answer_id, searched_for=searched_for)
        yield _sse("done", done.model_dump(mode="json"))
        try:
            _save(user, conv_id, question, result, timings, new_conv_id=new_conv, answer_id=answer_id)
        except Exception as e:  # noqa: BLE001 - the client already has the answer; record the failure
            print(f"[queryva] saving the exchange failed after the answer was sent: {type(e).__name__}: {e}", file=sys.stderr)
            metrics.save(user["id"], timings, totals, streamed=True, grounded=result["grounded"], error=f"save:{type(e).__name__}")
            return
        if not timings.get("cache_hit"):
            cache.put(user["id"], cache_key, result)
        metrics.save(user["id"], timings, totals, streamed=True, grounded=result["grounded"])

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
            "limits": {"max_mb": config.FILE_MAX_BYTES // (1024 * 1024), "direct_mb": config.UPLOAD_MAX_BYTES // (1024 * 1024),
                       "max_files": config.UPLOAD_MAX_FILES},
        }
    except Exception as e:
        raise upstream(e) from e


@app.post("/api/upload")
def upload(file: UploadFile = File(...), user: dict = Depends(current_user)) -> dict:
    data = file.file.read(config.UPLOAD_MAX_BYTES + 1)
    try:
        result = ingest_upload(file.filename or "upload", data, user_namespace(user["id"]))
        cache.clear(user["id"])  # answers may change now that the documents have
        files.save(user["id"], result["source"], data)  # keep the original for "Open document" and re-indexing
        return result
    except UploadError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise upstream(e) from e


class UploadStart(BaseModel):
    filename: str = Field(min_length=1, max_length=200)
    size: int = Field(ge=1)


class UploadFinish(BaseModel):
    source: str = Field(min_length=1, max_length=200)


@app.post("/api/uploads/start")
def upload_start(req: UploadStart, user: dict = Depends(current_user)) -> dict:
    """For files over the request-size limit: a one-time URL to upload straight to storage, then /finish."""
    try:
        source = check_new_upload(req.filename, user_namespace(user["id"]), req.size, config.FILE_MAX_BYTES)
        return {"source": source, **files.signed_upload(user["id"], source)}
    except UploadError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise upstream(e) from e


@app.post("/api/uploads/finish")
def upload_finish(req: UploadFinish, user: dict = Depends(current_user)) -> dict:
    """Index a file the browser uploaded to storage with /api/uploads/start."""
    try:
        data = files.download(user["id"], req.source)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Uploaded file not found. Please upload it again.") from e
    try:
        result = ingest_upload(req.source, data, user_namespace(user["id"]), max_bytes=config.FILE_MAX_BYTES)
        cache.clear(user["id"])
        return result
    except UploadError as e:
        files.remove(user["id"], [req.source])  # don't keep files that couldn't be indexed
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise upstream(e) from e


@app.get("/api/documents/{source}/open")
def open_document(source: str, user: dict = Depends(current_user)) -> dict:
    """A short-lived link to the user's original file (files uploaded before originals were kept have none)."""
    if not files.exists(user["id"], source):
        raise HTTPException(status_code=404, detail="The original file isn't stored. Upload it again to open it.")
    try:
        return {"url": files.signed_url(user["id"], source), "content_type": files.content_type(source)}
    except Exception as e:
        raise upstream(e) from e


@app.delete("/api/documents/{source}")
def delete_document(source: str, user: dict = Depends(current_user)) -> dict:
    store.delete_source(source, user_namespace(user["id"]))  # scoped to the user; shared docs can't be deleted
    files.remove(user["id"], [source])
    cache.clear(user["id"])
    return {"deleted": source}


# --- admin: metrics dashboard and health check -----------------------------------------

@app.get("/api/admin/metrics")
def admin_metrics(days: int = 7, user: dict = Depends(current_user)) -> dict:
    """Latency, cost, errors and cache hits for the dashboard. Only for emails in ADMIN_EMAILS."""
    if (user.get("email") or "").lower() not in config.ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admins only.")
    try:
        return {"days": days, **metrics.summarize(metrics.recent(max(1, min(days, 90))))}
    except Exception as e:
        raise upstream(e) from e


@app.get("/api/health/check")
def health_check(hours: int = 24, x_check_token: str = Header(default="")) -> dict:
    """503 when the last `hours` breach the alert thresholds; a scheduled workflow turns that into an email."""
    if not config.HEALTH_CHECK_TOKEN or x_check_token != config.HEALTH_CHECK_TOKEN:
        raise HTTPException(status_code=401, detail="Bad token.")
    rows = [r for r in metrics.recent(max(1, -(-hours // 24)))
            if r["created_at"] >= (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()]
    overall = metrics.summarize(rows)["overall"]
    problems = []
    if overall["questions"] >= config.ALERT_MIN_QUESTIONS:
        if overall["p95_s"] and overall["p95_s"] > config.ALERT_P95_S:
            problems.append(f"p95 latency {overall['p95_s']:.1f}s > {config.ALERT_P95_S:.0f}s")
        if overall["error_rate"] > config.ALERT_ERROR_RATE:
            problems.append(f"error rate {overall['error_rate']:.0%} > {config.ALERT_ERROR_RATE:.0%}")
    body = {"ok": not problems, "hours": hours, "problems": problems, **overall}
    if problems:
        raise HTTPException(status_code=503, detail=body)
    return body


# --- account ----------------------------------------------------------------------------

@app.delete("/api/account")
def delete_account(user: dict = Depends(current_user)) -> dict:
    """Delete the user's uploads, then the account itself (chats, messages and feedback cascade)."""
    try:
        store.client().table(store.TABLE).delete().eq("namespace", user_namespace(user["id"])).execute()
        files.remove_all(user["id"])
        store.client().auth.admin.delete_user(user["id"])
    except Exception as e:
        raise upstream(e) from e
    auth.forget(user["id"])
    return {"deleted": True}


# Local dev: serve the frontend from the same origin. On Vercel, public/ is served by the CDN.
if not os.environ.get("VERCEL"):
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=ROOT / "public", html=True), name="static")
