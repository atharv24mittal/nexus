"""
rate_limit.py
-------------
Minimal in-memory rate limiting, implemented as a plain FastAPI dependency
(no decorator-wraps-the-endpoint-function magic involved at all).

This replaces an earlier slowapi-decorator-based version. That approach
worked in this project's own Linux test environment but produced clean,
unexplained 422 Unprocessable Entity responses specifically on Windows +
Python 3.11 (the decorator re-derives the endpoint's signature via
`functools.wraps` + `inspect.signature` to extract the `Request` argument,
and to determine the registered-route lookup key) — fragile in a way that
wasn't worth chasing further across Python versions/OSes for what a
fixed-window counter does perfectly well on its own.

A FastAPI `Depends(...)` has none of that fragility: FastAPI calls it with
a freshly-injected `Request` before the route runs, with no rewriting of
the route function's own signature whatsoever.

Also exposes standard X-RateLimit-* response headers so a client (or you,
debugging in browser devtools) can see exactly where they stand without
guessing.

Scope, honestly stated: this is a single-process, in-memory fixed-window
limiter. It resets if the process restarts, and does NOT coordinate limits
across multiple instances/workers. That's the right tradeoff for a single
Render free-tier instance (no Redis, no extra paid infrastructure); it is
NOT the right tradeoff for a horizontally-scaled multi-instance deployment,
where you'd want a shared store (Redis) instead — worth saying out loud if
asked about it, same as the sandbox's documented limitations in SECURITY.md.
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request, Response

from app.config import settings


class _FixedWindowLimiter:
    def __init__(self):
        self._hits: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, max_requests: int, window_seconds: int) -> tuple[int, int]:
        """Returns (remaining, reset_in_seconds). Raises HTTPException(429) if over the limit."""
        now = time.time()
        window_start = now - window_seconds
        hits = self._hits[key]
        while hits and hits[0] < window_start:
            hits.pop(0)
        if len(hits) >= max_requests:
            retry_after = int(hits[0] + window_seconds - now) + 1
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Rate limit exceeded ({max_requests} requests per "
                    f"{window_seconds}s). Try again in {retry_after}s."
                ),
                headers={"Retry-After": str(retry_after)},
            )
        hits.append(now)
        remaining = max_requests - len(hits)
        reset_in = int(hits[0] + window_seconds - now) if hits else window_seconds
        return remaining, reset_in


_limiter = _FixedWindowLimiter()


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def rate_limit_solve(request: Request, response: Response) -> None:
    """Dependency for /solve: stricter limit since it calls an external LLM
    and can run several sandboxed executions per request."""
    remaining, reset_in = _limiter.check(
        f"solve:{_client_key(request)}",
        max_requests=settings.RATE_LIMIT_SOLVE_MAX,
        window_seconds=settings.RATE_LIMIT_SOLVE_WINDOW_SECONDS,
    )
    response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_SOLVE_MAX)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset_in)


def rate_limit_default(request: Request, response: Response) -> None:
    """Dependency for lighter endpoints like /check, /explain, /hint."""
    remaining, reset_in = _limiter.check(
        f"default:{_client_key(request)}",
        max_requests=settings.RATE_LIMIT_DEFAULT_MAX,
        window_seconds=settings.RATE_LIMIT_DEFAULT_WINDOW_SECONDS,
    )
    response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_DEFAULT_MAX)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset_in)
