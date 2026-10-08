"""Conversation-aware helpers: rewrite follow-ups into standalone questions, and suggest next questions.

Retrieval works on a single query, so "what about part-timers?" would search for the wrong thing.
`rewrite()` turns it into "What is the remote work policy for part-time employees?" using recent turns.
"""

import json
import re

from rag import config, llm

REWRITE_SYSTEM = """You rewrite a user's latest message in a chat about their documents into a standalone question.

- Use the conversation only to resolve references (it, that, they, "the second one", "what about X", "and how?").
- Name the topic explicitly when the message only implies it ("the server" in a chat about MCP → "the MCP server").
- Keep the user's intent, wording and language. Don't answer it, don't add facts, don't make it broader.
- If the message is already understandable on its own, return it unchanged.
- Output only the question, nothing else."""

SUGGEST_SYSTEM = """You suggest follow-up questions for a documentation chatbot. Reply with JSON only:
{"questions": ["...", "...", "..."]}

- Exactly 3 short questions (max 12 words each) the user is likely to ask next.
- Each must be answerable from the PASSAGES, and different from the question already asked.
- Write them the way a user would type them. No numbering, no quotes inside."""

MAX_TURNS = 3  # recent exchanges used to resolve a follow-up


def _transcript(turns: list[tuple[str, str]]) -> str:
    lines = []
    for q, a in turns[-MAX_TURNS:]:
        a = re.sub(r"\[\d+\]", "", a)  # citation markers add nothing here
        lines.append(f"User: {q}\nAssistant: {a[:600]}")
    return "\n\n".join(lines)


def rewrite(question: str, turns: list[tuple[str, str]]) -> str:
    """Standalone version of `question` given earlier (question, answer) turns. No-op without history."""
    if not turns:
        return question
    user = f"Conversation:\n{_transcript(turns)}\n\nLatest message: {question}\n\nStandalone question:"
    try:
        out = llm.complete(REWRITE_SYSTEM, user).strip().strip('"').strip()
    except Exception:
        return question  # never block an answer because the rewrite failed
    return out if 0 < len(out) <= 500 else question


def suggest(question: str, answer: str, passages: list[str]) -> list[str]:
    if not passages:
        return []
    ctx = "\n\n---\n\n".join(p[:1500] for p in passages[:5])
    user = f"QUESTION ASKED: {question}\n\nANSWER GIVEN: {answer[:1500]}\n\nPASSAGES:\n{ctx}"
    raw = llm.complete(SUGGEST_SYSTEM, user, json_mode=True)
    try:
        qs = json.loads(raw[raw.find("{") : raw.rfind("}") + 1]).get("questions", [])
    except json.JSONDecodeError:
        return []
    seen, out = {question.strip().lower()}, []
    for q in qs:
        q = str(q).strip().strip('"')
        if 3 <= len(q) <= 120 and q.lower() not in seen:
            seen.add(q.lower())
            out.append(q)
    return out[:3]
