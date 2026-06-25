"""test_rate_limit.py — the in-memory fixed-window limiter that replaced slowapi."""

import pytest
from fastapi import HTTPException

from app.security.rate_limit import _FixedWindowLimiter


def test_allows_requests_under_the_limit():
    limiter = _FixedWindowLimiter()
    for _ in range(5):
        limiter.check("test-key", max_requests=5, window_seconds=60)  # should not raise


def test_blocks_requests_over_the_limit():
    limiter = _FixedWindowLimiter()
    for _ in range(3):
        limiter.check("test-key", max_requests=3, window_seconds=60)
    with pytest.raises(HTTPException) as exc_info:
        limiter.check("test-key", max_requests=3, window_seconds=60)
    assert exc_info.value.status_code == 429


def test_different_keys_have_independent_limits():
    limiter = _FixedWindowLimiter()
    for _ in range(3):
        limiter.check("key-a", max_requests=3, window_seconds=60)
    # key-b should be unaffected by key-a's usage
    limiter.check("key-b", max_requests=3, window_seconds=60)  # should not raise


def test_window_expiry_allows_requests_again(monkeypatch):
    limiter = _FixedWindowLimiter()
    times = iter([100.0, 100.1, 100.2, 161.0])  # last one is past the 60s window
    monkeypatch.setattr("app.security.rate_limit.time.time", lambda: next(times))

    limiter.check("test-key", max_requests=3, window_seconds=60)
    limiter.check("test-key", max_requests=3, window_seconds=60)
    limiter.check("test-key", max_requests=3, window_seconds=60)
    # at t=161, the t=100.0 hit has expired out of the 60s window, so this
    # should succeed instead of raising even though 3 hits were already recorded
    limiter.check("test-key", max_requests=3, window_seconds=60)


def test_check_returns_remaining_count():
    limiter = _FixedWindowLimiter()
    remaining, _ = limiter.check("test-key", max_requests=5, window_seconds=60)
    assert remaining == 4
    remaining, _ = limiter.check("test-key", max_requests=5, window_seconds=60)
    assert remaining == 3


def test_429_includes_retry_after_header():
    limiter = _FixedWindowLimiter()
    limiter.check("test-key", max_requests=1, window_seconds=60)
    with pytest.raises(HTTPException) as exc_info:
        limiter.check("test-key", max_requests=1, window_seconds=60)
    assert "Retry-After" in exc_info.value.headers
    assert int(exc_info.value.headers["Retry-After"]) > 0
