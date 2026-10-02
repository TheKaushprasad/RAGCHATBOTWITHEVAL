import re

from rag import config
from rag.embeddings import _retry, gemini_client, openai_client

SYSTEM_PROMPT = f"""You answer questions using ONLY the numbered context passages provided.

Rules:
- Every factual sentence must cite the passage(s) it comes from, like [1] or [2][4].
- Do not use outside knowledge. Do not guess.
- If the passages do not contain enough information to answer, reply exactly: "{config.IDK}."
  You may add one short sentence saying what is missing, but no citations and no guesses.
- Be concise."""


def build_prompt(question: str, chunks: list[dict]) -> str:
    parts = []
    for n, c in enumerate(chunks, start=1):
        loc = f"{c['source']}" + (f", page {c['page']}" if c.get("page") else "")
        parts.append(f"[{n}] ({loc})\n{c['content']}")
    context = "\n\n---\n\n".join(parts)
    return f"Context passages:\n\n{context}\n\nQuestion: {question}"


def complete(system: str, user: str, model: str | None = None, json_mode: bool = False) -> str:
    """One chat completion against the configured provider."""
    model = model or config.CHAT_MODEL
    if config.PROVIDER == "openai":
        kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
        res = _retry(lambda: openai_client().chat.completions.create(
            model=model,
            temperature=0,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            **kwargs,
        ))
        return (res.choices[0].message.content or "").strip()

    from google.genai import types

    cfg = types.GenerateContentConfig(
        system_instruction=system,
        temperature=0,
        response_mime_type="application/json" if json_mode else None,
    )
    res = _retry(lambda: gemini_client().models.generate_content(model=model, contents=user, config=cfg))
    return (res.text or "").strip()


def answer(question: str, chunks: list[dict]) -> str:
    return complete(SYSTEM_PROMPT, build_prompt(question, chunks)) or config.IDK + "."


def cited_numbers(text: str, max_n: int) -> list[int]:
    """Citation numbers referenced in the answer, in first-appearance order."""
    seen: list[int] = []
    for m in re.finditer(r"\[(\d+)\]", text):
        n = int(m.group(1))
        if 1 <= n <= max_n and n not in seen:
            seen.append(n)
    return seen
