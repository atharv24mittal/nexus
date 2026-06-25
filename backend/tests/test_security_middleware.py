"""test_security_middleware.py — body size cap, CSP/HSTS headers, docs visibility."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_oversized_body_rejected_at_transport_level():
    huge_payload = {"problem_id": "sort_list", "code": "x" * 30_000}
    r = client.post("/check", json=huge_payload)
    assert r.status_code == 413


def test_normal_sized_body_passes_through():
    r = client.post("/check", json={
        "problem_id": "is_palindrome",
        "code": "def is_palindrome(s):\n    return s == s[::-1]",
    })
    assert r.status_code == 200


def test_csp_header_present():
    r = client.get("/health")
    assert r.headers.get("content-security-policy") == "default-src 'none'"


def test_hsts_header_present():
    r = client.get("/health")
    assert "max-age" in r.headers.get("strict-transport-security", "")


def test_docs_visible_by_default():
    r = client.get("/docs")
    assert r.status_code == 200
