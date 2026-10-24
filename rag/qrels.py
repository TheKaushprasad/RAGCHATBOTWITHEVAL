"""Passage-level relevance labels ("qrels") for the retrieval eval.

A hit used to mean "a chunk from the expected file was retrieved". With a single source document every
chunk qualifies, so hit rate was always 100% and couldn't compare retrieval settings. Instead, an LLM judge
reads the golden answer and marks which candidate passages contain the information it needs. Labels are
pooled over every query variant being compared and saved next to the eval file, so all settings are scored
against the same answer key and labelling is paid for once.
"""

import json
from pathlib import Path

from rag import config, llm

JUDGE_SYSTEM = """You label search results for a retrieval evaluation. Reply with JSON only:
{"relevant": [<passage ids>]}

A passage is relevant if it contains information that the reference answer relies on, so that someone
could write a substantial part of that answer from it. Passages that only mention the topic are not
relevant. List every relevant id; the list may be empty."""


def chunk_key(c: dict) -> str:
    return f"{c['source']}#{c['chunk_index']}"


def qrels_path(eval_file: str) -> Path:
    """Labels file for an eval set. A judge from another provider keeps its own labels (…_qrels_gemini.json)."""
    p = Path(eval_file)
    suffix = "" if config.JUDGE_PROVIDER == config.PROVIDER else f"_{config.JUDGE_PROVIDER}"
    return p.with_name(f"{p.stem}_qrels{suffix}.json")


def load(eval_file: str) -> dict:
    p = qrels_path(eval_file)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save(eval_file: str, labels: dict) -> None:
    qrels_path(eval_file).write_text(json.dumps(labels, indent=1, ensure_ascii=False), encoding="utf-8")


def judge(case: dict, pool: list[dict]) -> dict:
    """Label a pool of candidate chunks for one case. Returns {"judged": [...keys], "relevant": [...keys]}."""
    passages = "\n\n".join(f'<passage id="{i}">\n{c["content"][:1800]}\n</passage>' for i, c in enumerate(pool, 1))
    user = f"Question: {case['question']}\n\nReference answer: {case.get('answer', '')}\n\n{passages}"
    raw = llm.complete(JUDGE_SYSTEM, user, model=config.JUDGE_MODEL, json_mode=True,
                       provider=config.JUDGE_PROVIDER)
    ids = {int(i) for i in json.loads(raw).get("relevant", []) if str(i).isdigit()}
    return {
        "judged": [chunk_key(c) for c in pool],
        "relevant": [chunk_key(c) for i, c in enumerate(pool, 1) if i in ids],
    }
