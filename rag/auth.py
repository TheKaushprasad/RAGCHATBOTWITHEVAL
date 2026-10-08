"""Verify Supabase Auth access tokens sent by the browser (Authorization: Bearer <token>)."""

import time

from rag import store

_CACHE: dict[str, tuple[float, dict]] = {}  # token -> (expires_at, user); avoids an auth call per request
_TTL = 60.0


class AuthError(Exception):
    pass


def verify(token: str | None) -> dict:
    """Return {"id", "email"} for a valid access token, else raise AuthError."""
    if not token:
        raise AuthError("Not logged in.")
    now = time.monotonic()
    hit = _CACHE.get(token)
    if hit and hit[0] > now:
        return hit[1]
    try:
        res = store.client().auth.get_user(token)
    except Exception as e:  # expired / revoked / malformed token
        raise AuthError("Your session has expired. Please log in again.") from e
    if not res or not res.user:
        raise AuthError("Your session has expired. Please log in again.")
    user = {"id": str(res.user.id), "email": res.user.email}
    if len(_CACHE) > 1000:
        _CACHE.clear()
    _CACHE[token] = (now + _TTL, user)
    return user


def bearer(header: str | None) -> str | None:
    if header and header.lower().startswith("bearer "):
        return header[7:].strip() or None
    return None


def forget(user_id: str) -> None:
    """Drop cached tokens for a user (e.g. after their account is deleted)."""
    for token in [t for t, (_, u) in _CACHE.items() if u["id"] == user_id]:
        _CACHE.pop(token, None)
