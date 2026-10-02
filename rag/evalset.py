"""Shared helpers for eval.py, eval_answers.py and tune.py."""

import json
import sys
from pathlib import Path

RESULTS = Path("results")
DEFAULT_EVALS = "evals_golden.json"


def results_dir(eval_file: str) -> Path:
    """Where an eval set's reports go: examples/<x>/results for archived sets, else results/<name>."""
    p = Path(eval_file)
    if "examples" in p.parts:
        out = p.parent / "results"
    else:
        out = RESULTS / p.stem.removeprefix("evals_")
    out.mkdir(parents=True, exist_ok=True)
    return out


def load_cases(path: str = "evals.json") -> list[dict]:
    with open(path, encoding="utf-8") as f:
        cases = json.load(f)
    for c in cases:
        c.setdefault("answerable", True)
    return cases


def is_hit(chunk: dict, case: dict) -> bool:
    """A retrieved chunk is relevant if it comes from an expected source and contains the expected text."""
    if chunk["source"] not in case["expected_sources"]:
        return False
    needle = case.get("expected_substring")
    return not needle or needle.lower() in chunk["content"].lower()


def first_hit_rank(chunks: list[dict], case: dict) -> int | None:
    return next((r for r, c in enumerate(chunks, start=1) if is_hit(c, case)), None)


def best_threshold(pos: list[float], neg: list[float]) -> tuple[float, float]:
    """Similarity cutoff that best separates answerable (pos) from unanswerable (neg) top-1 scores.

    Returns (threshold, accuracy). Ties are broken toward the middle of the widest gap,
    which generalises better than sitting right on a data point.
    """
    if not pos or not neg:
        return (min(pos or neg or [0.0]) - 0.01, 1.0)
    points = sorted(set(pos + neg))
    candidates = [points[0] - 0.01] + [(a + b) / 2 for a, b in zip(points, points[1:])] + [points[-1] + 0.01]
    total = len(pos) + len(neg)

    def acc(t: float) -> float:
        return (sum(p >= t for p in pos) + sum(n < t for n in neg)) / total

    best = max(acc(t) for t in candidates)
    winners = [t for t in candidates if acc(t) == best]
    return (winners[len(winners) // 2], best)


def safe_threshold(pos: list[float], margin: float = 0.03) -> float:
    """Highest cutoff that refuses no answerable question, minus a safety margin.

    The threshold is an off-topic filter that saves an LLM call, not the main refusal mechanism:
    on-topic-but-unanswerable questions score as high as answerable ones, and the prompt guard
    handles those. So it must never block a real question; that's what this optimizes for.
    """
    return round(max(0.0, min(pos) - margin), 3) if pos else 0.0


def md_table(rows: list[dict], cols: list[str]) -> str:
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
    return "\n".join(out)


def utf8_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # ✓/✗ on Windows consoles
