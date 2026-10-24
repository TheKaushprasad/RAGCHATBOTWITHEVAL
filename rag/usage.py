"""Token usage and estimated cost per request.

Every model call reports its tokens with `record()`. `track()` opens a collector for one request (a context
variable, so concurrent requests on the same worker don't mix), and `cost()` prices it with config.PRICES.
"""

import contextvars
from contextlib import contextmanager

from rag import config

_current: contextvars.ContextVar[dict | None] = contextvars.ContextVar("usage", default=None)


def new() -> dict:
    return {"tokens_in": 0, "tokens_out": 0, "by_model": {}}


@contextmanager
def track(totals: dict | None = None):
    """Collect usage into `totals` (a new dict if omitted) for calls made inside the block.

    A streaming response runs each step in a fresh copy of the context, so re-enter track(totals) around
    each step rather than holding one block open across yields."""
    totals = totals if totals is not None else new()
    token = _current.set(totals)
    try:
        yield totals
    finally:
        _current.reset(token)


def record(model: str, tokens_in: int, tokens_out: int = 0) -> None:
    totals = _current.get()
    if totals is None:
        return
    totals["tokens_in"] += tokens_in or 0
    totals["tokens_out"] += tokens_out or 0
    m = totals["by_model"].setdefault(model, [0, 0])
    m[0] += tokens_in or 0
    m[1] += tokens_out or 0


def cost(totals: dict) -> float:
    """Estimated USD from per-million-token prices (config.PRICES); unknown models count as 0."""
    usd = 0.0
    for model, (tin, tout) in totals["by_model"].items():
        price_in, price_out = config.PRICES.get(model, (0.0, 0.0))
        usd += tin / 1e6 * price_in + tout / 1e6 * price_out
    return round(usd, 6)
