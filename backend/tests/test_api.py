"""test_api.py — endpoint-level tests for the FastAPI app."""

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_problems():
    r = client.get("/problems")
    assert r.status_code == 200
    body = r.json()
    assert len(body) >= 5
    ids = {p["id"] for p in body}
    assert "sort_list" in ids
    assert "two_sum" in ids


def test_check_endpoint_with_correct_code():
    r = client.post("/check", json={
        "problem_id": "is_palindrome",
        "code": "def is_palindrome(s):\n    return s == s[::-1]",
    })
    assert r.status_code == 200
    assert r.json()["passed"] is True


def test_check_endpoint_with_buggy_code():
    r = client.post("/check", json={
        "problem_id": "is_palindrome",
        "code": "def is_palindrome(s):\n    return True",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["passed"] is False
    assert any(not c["passed"] for c in body["checks"])


def test_check_endpoint_unknown_problem_returns_404():
    r = client.post("/check", json={"problem_id": "does_not_exist", "code": "def f(): pass"})
    assert r.status_code == 404


def test_check_endpoint_rejects_empty_code():
    r = client.post("/check", json={"problem_id": "sort_list", "code": "   "})
    assert r.status_code == 422


def test_check_endpoint_rejects_oversized_code():
    r = client.post("/check", json={"problem_id": "sort_list", "code": "x" * 9000})
    assert r.status_code == 422


def test_stats_endpoint_shape():
    r = client.get("/stats")
    assert r.status_code == 200
    body = r.json()
    assert "skill_library" in body
    assert "llm_provider" in body
    assert "llm_is_live" in body


def test_solve_endpoint_unknown_problem_returns_404():
    r = client.post("/solve", json={"problem_id": "nonexistent_problem"})
    assert r.status_code == 404


def test_root_endpoint():
    r = client.get("/")
    assert r.status_code == 200
    assert "NEXUS" in r.json()["name"]


def test_security_headers_present():
    r = client.get("/health")
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "DENY"


def test_request_id_header_present_on_every_response():
    r = client.get("/health")
    assert "x-request-id" in r.headers
    assert len(r.headers["x-request-id"]) > 0


def test_request_id_is_echoed_back_if_client_supplies_one():
    r = client.get("/health", headers={"X-Request-ID": "my-custom-id-123"})
    assert r.headers["x-request-id"] == "my-custom-id-123"


def test_problems_endpoint_has_cache_control():
    r = client.get("/problems")
    assert "max-age" in r.headers.get("cache-control", "")


def test_solve_response_includes_rate_limit_headers():
    r = client.post("/solve", json={"problem_id": "is_palindrome"})
    assert "x-ratelimit-limit" in r.headers
    assert "x-ratelimit-remaining" in r.headers


def test_check_response_includes_rate_limit_headers():
    r = client.post("/check", json={"problem_id": "is_palindrome", "code": "def is_palindrome(s):\n    return s == s[::-1]"})
    assert "x-ratelimit-limit" in r.headers


def test_explain_endpoint_returns_explanation():
    r = client.post("/explain", json={
        "problem_id": "is_palindrome",
        "code": "def is_palindrome(s):\n    return s == s[::-1]",
    })
    assert r.status_code == 200
    body = r.json()
    assert "explanation" in body
    assert isinstance(body["explanation"], str)
    assert len(body["explanation"]) > 0


def test_explain_endpoint_caches_repeat_requests():
    payload = {"problem_id": "is_palindrome", "code": "def is_palindrome(s):\n    return s == s[::-1]\n# unique marker for cache test"}
    r1 = client.post("/explain", json=payload)
    assert r1.json()["cached"] is False
    r2 = client.post("/explain", json=payload)
    assert r2.json()["cached"] is True
    assert r2.json()["explanation"] == r1.json()["explanation"]


def test_hint_endpoint_returns_hint():
    r = client.post("/hint", json={
        "problem_id": "is_palindrome",
        "code": "def is_palindrome(s):\n    return True",
        "error_message": "fails on non-palindromes",
    })
    assert r.status_code == 200
    assert len(r.json()["hint"]) > 0


def test_explain_unknown_problem_returns_404():
    r = client.post("/explain", json={"problem_id": "nope", "code": "def f(): pass"})
    assert r.status_code == 404


def test_history_endpoint_returns_list():
    client.post("/check", json={"problem_id": "is_palindrome", "code": "def is_palindrome(s):\n    return s == s[::-1]"})
    r = client.get("/history")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_history_stats_endpoint_shape():
    r = client.get("/history/stats")
    assert r.status_code == 200
    body = r.json()
    assert "total_solves" in body
    assert "overall_success_rate" in body
    assert "per_problem" in body


def test_history_limit_is_clamped():
    r = client.get("/history?limit=99999")
    assert r.status_code == 200
    assert len(r.json()) <= 100


def test_result_endpoint_after_solve_returns_full_result():
    solve_r = client.post("/solve", json={"problem_id": "is_palindrome"})
    assert solve_r.status_code == 200
    result_id = solve_r.json()["result_id"]
    result_r = client.get(f"/result/{result_id}")
    assert result_r.status_code == 200
    body = result_r.json()
    assert body["id"] == result_id
    assert body["result"]["problem_id"] == "is_palindrome"


def test_result_endpoint_unknown_id_returns_404():
    r = client.get("/result/totally-made-up-id")
    assert r.status_code == 404


def test_solve_stream_endpoint_emits_sse_events():
    with client.stream("POST", "/solve/stream", json={"problem_id": "is_palindrome"}) as r:
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]
        events = []
        for line in r.iter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[len("data: "):]))
        event_types = [e["event"] for e in events]
        assert "attempt_start" in event_types
        assert event_types[-1] == "final_result"
        assert "result_id" in events[-1]


def test_solve_stream_unknown_problem_returns_404():
    r = client.post("/solve/stream", json={"problem_id": "nonexistent_problem"})
    assert r.status_code == 404
