"""Per-user chat history: conversations and their messages. Every call is scoped to user_id."""

from datetime import datetime, timezone

from rag import store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _db():
    return store.client()


def create_conversation(user_id: str, first_message: str) -> dict:
    title = " ".join(first_message.split())
    title = title if len(title) <= 60 else title[:57].rstrip() + "…"
    return _db().table("conversations").insert({"user_id": user_id, "title": title}).execute().data[0]


def owns(user_id: str, conversation_id: str) -> bool:
    rows = (_db().table("conversations").select("id")
            .eq("id", conversation_id).eq("user_id", user_id).limit(1).execute().data)
    return bool(rows)


def list_conversations(user_id: str, limit: int = 100) -> list[dict]:
    return (_db().table("conversations").select("id,title,updated_at")
            .eq("user_id", user_id).order("updated_at", desc=True).limit(limit).execute().data)


def get_messages(user_id: str, conversation_id: str) -> list[dict]:
    msgs = (_db().table("messages").select("role,content,citations,grounded,answer_id,created_at")
            .eq("conversation_id", conversation_id).eq("user_id", user_id).order("id").execute().data)
    # Attach the user's earlier thumbs up/down so reopened chats show them.
    ids = [m["answer_id"] for m in msgs if m.get("answer_id")]
    ratings = {}
    if ids:
        rows = (_db().table("feedback").select("answer_id,rating,comment")
                .in_("answer_id", ids).eq("user_id", user_id).execute().data)
        ratings = {r["answer_id"]: r for r in rows}
    for m in msgs:
        fb = ratings.get(m.get("answer_id"))
        m["rating"] = fb["rating"] if fb else 0
    return msgs


def add_exchange(user_id: str, conversation_id: str, question: str, result: dict, answer_id: str) -> None:
    # Both rows list every column: in a bulk insert PostgREST sends null (not the column default)
    # for keys missing from a row, which would violate citations' NOT NULL.
    _db().table("messages").insert([
        {"conversation_id": conversation_id, "user_id": user_id, "role": "user", "content": question,
         "citations": [], "grounded": None, "answer_id": None},
        {"conversation_id": conversation_id, "user_id": user_id, "role": "assistant",
         "content": result["answer"], "citations": result["citations"], "grounded": result["grounded"],
         "answer_id": answer_id},
    ]).execute()
    _db().table("conversations").update({"updated_at": _now()}).eq("id", conversation_id).eq("user_id", user_id).execute()


def rename_conversation(user_id: str, conversation_id: str, title: str) -> None:
    (_db().table("conversations").update({"title": title.strip()[:120] or "Untitled"})
     .eq("id", conversation_id).eq("user_id", user_id).execute())


def delete_conversation(user_id: str, conversation_id: str) -> None:
    _db().table("conversations").delete().eq("id", conversation_id).eq("user_id", user_id).execute()


def recent_turns(user_id: str, conversation_id: str, n: int = 3) -> list[tuple[str, str]]:
    """Last n (question, answer) pairs, oldest first, for resolving follow-up questions."""
    rows = (_db().table("messages").select("role,content")
            .eq("conversation_id", conversation_id).eq("user_id", user_id)
            .order("id", desc=True).limit(n * 2).execute().data)[::-1]
    turns, question = [], None
    for r in rows:
        if r["role"] == "user":
            question = r["content"]
        elif question is not None:
            turns.append((question, r["content"]))
            question = None
    return turns


def last_exchange(user_id: str, conversation_id: str) -> dict | None:
    """The latest question + answer (with its cited passages), for suggesting follow-ups."""
    rows = (_db().table("messages").select("role,content,citations,grounded")
            .eq("conversation_id", conversation_id).eq("user_id", user_id)
            .order("id", desc=True).limit(2).execute().data)
    if len(rows) < 2 or rows[0]["role"] != "assistant" or rows[1]["role"] != "user":
        return None
    return {"question": rows[1]["content"], "answer": rows[0]["content"],
            "citations": rows[0]["citations"] or [], "grounded": rows[0]["grounded"]}


def delete_all(user_id: str) -> None:
    _db().table("conversations").delete().eq("user_id", user_id).execute()
