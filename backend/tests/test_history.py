"""test_history.py — solve history persistence, aggregate stats, shareable lookups."""

import pathlib
import tempfile

import pytest

from app.core.history import HistoryStore


@pytest.fixture
def store():
    tmp = pathlib.Path(tempfile.mktemp(suffix=".db"))
    h = HistoryStore(db_path=tmp)
    yield h
    h.close()
    tmp.unlink(missing_ok=True)


def test_store_and_retrieve_full_result(store):
    record_id = store.store(
        "sort_list", True, 2, 1.5, 0.7, "groq:test", {"final_code": "def f(): pass"}
    )
    full = store.get_full_result(record_id)
    assert full == {"final_code": "def f(): pass"}


def test_get_full_result_returns_none_for_unknown_id(store):
    assert store.get_full_result("nonexistent-id") is None


def test_list_recent_orders_newest_first(store):
    id1 = store.store("sort_list", True, 1, 1.0, 1.0, "groq:test", {})
    id2 = store.store("two_sum", True, 1, 1.0, 1.0, "groq:test", {})
    recent = store.list_recent(limit=10)
    assert recent[0]["id"] == id2
    assert recent[1]["id"] == id1


def test_list_recent_respects_limit(store):
    for _ in range(5):
        store.store("sort_list", True, 1, 1.0, 1.0, "groq:test", {})
    assert len(store.list_recent(limit=3)) == 3


def test_aggregate_stats_per_problem(store):
    store.store("sort_list", True, 1, 1.0, 1.0, "groq:test", {})
    store.store("sort_list", False, 5, 8.0, 0.0, "groq:test", {})
    store.store("two_sum", True, 2, 2.0, 0.7, "groq:test", {})

    stats = store.aggregate_stats()
    assert stats["total_solves"] == 3
    assert stats["per_problem"]["sort_list"]["total_solves"] == 2
    assert stats["per_problem"]["sort_list"]["success_rate"] == 0.5
    assert stats["per_problem"]["two_sum"]["success_rate"] == 1.0


def test_aggregate_stats_empty_store(store):
    stats = store.aggregate_stats()
    assert stats["total_solves"] == 0
    assert stats["overall_success_rate"] == 0.0
    assert stats["per_problem"] == {}
