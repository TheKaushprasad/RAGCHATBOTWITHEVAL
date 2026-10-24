"""One row per answered (or failed) question in `answer_metrics`: latency per stage, tokens, cost, outcome.

Feeds the admin dashboard (/admin/) and the scheduled health check. Writing a metric never fails a request,
and until the table exists (supabase/schema.sql) rows are skipped.
"""

import sys
from datetime import datetime, timedelta, timezone

from rag import store, usage

TABLE = "answer_metrics"
STAGES = ("rewrite", "cache", "search", "rerank", "first_token", "answer", "save", "total")
_disabled = False


def save(user_id: str | None, timings: dict, totals: dict, *, streamed: bool, grounded: bool | None,
         error: str | None = None) -> None:
    global _disabled
    if _disabled:
        return
    row = {
        "user_id": user_id,
        "streamed": streamed,
        "cache_hit": bool(timings.get("cache_hit")),
        "grounded": grounded,
        "error": error,
        "tokens_in": totals["tokens_in"],
        "tokens_out": totals["tokens_out"],
        "cost_usd": usage.cost(totals),
        **{f"{k}_s": round(timings[k], 3) for k in STAGES if k in timings},
    }
    try:
        store.client().table(TABLE).insert(row).execute()
    except Exception as e:  # noqa: BLE001
        if "PGRST205" in str(e):
            _disabled = True
        print(f"[queryva] metrics skipped: {type(e).__name__}: {e}", file=sys.stderr)


def recent(days: int) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows, start = [], 0
    while True:  # PostgREST pages at 1000 rows
        page = (store.client().table(TABLE).select("*").gte("created_at", since)
                .order("created_at").range(start, start + 999).execute().data)
        rows += page
        if len(page) < 1000:
            return rows
        start += 1000


def _pct(values: list[float], p: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    return values[min(len(values) - 1, max(0, round(p / 100 * len(values) + 0.5) - 1))]


def summarize(rows: list[dict]) -> dict:
    """Totals plus per-day and per-stage percentiles for the dashboard and health check."""
    def stats(rs: list[dict]) -> dict:
        ok = [r for r in rs if not r.get("error")]
        totals = [r["total_s"] for r in ok if r.get("total_s") is not None]
        firsts = [r["first_token_s"] for r in ok if r.get("first_token_s") is not None]
        answered = [r for r in ok if r.get("grounded") is not None]
        return {
            "questions": len(rs),
            "errors": len(rs) - len(ok),
            "error_rate": round((len(rs) - len(ok)) / len(rs), 4) if rs else 0,
            "p50_s": _pct(totals, 50), "p95_s": _pct(totals, 95),
            "first_token_p50_s": _pct(firsts, 50), "first_token_p95_s": _pct(firsts, 95),
            "cache_hit_rate": round(sum(bool(r.get("cache_hit")) for r in ok) / len(ok), 4) if ok else 0,
            "grounded_rate": round(sum(bool(r["grounded"]) for r in answered) / len(answered), 4) if answered else 0,
            "tokens": sum((r.get("tokens_in") or 0) + (r.get("tokens_out") or 0) for r in rs),
            "cost_usd": round(sum(float(r.get("cost_usd") or 0) for r in rs), 4),
        }

    by_day: dict[str, list[dict]] = {}
    for r in rows:
        by_day.setdefault(r["created_at"][:10], []).append(r)
    ok = [r for r in rows if not r.get("error")]
    stages = {s: {"p50": _pct([r[f"{s}_s"] for r in ok if r.get(f"{s}_s") is not None], 50),
                  "p95": _pct([r[f"{s}_s"] for r in ok if r.get(f"{s}_s") is not None], 95)} for s in STAGES}
    return {"overall": stats(rows), "days": [{"day": d, **stats(rs)} for d, rs in sorted(by_day.items())],
            "stages": stages}
