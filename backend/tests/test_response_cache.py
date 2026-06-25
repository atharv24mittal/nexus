"""test_response_cache.py — the in-memory cache used by /explain and /hint."""

from app.core.response_cache import ResponseCache


def test_cache_miss_then_hit():
    cache = ResponseCache()
    key = cache.make_key("sort_list", "def f(): pass")
    assert cache.get(key) is None
    cache.set(key, "an explanation")
    assert cache.get(key) == "an explanation"


def test_different_inputs_produce_different_keys():
    cache = ResponseCache()
    k1 = cache.make_key("sort_list", "code A")
    k2 = cache.make_key("sort_list", "code B")
    assert k1 != k2


def test_same_inputs_produce_same_key():
    cache = ResponseCache()
    k1 = cache.make_key("sort_list", "identical code")
    k2 = cache.make_key("sort_list", "identical code")
    assert k1 == k2


def test_eviction_at_max_entries():
    cache = ResponseCache(max_entries=3)
    keys = [cache.make_key(f"item-{i}") for i in range(5)]
    for k in keys:
        cache.set(k, "value")
    assert cache.stats()["entries"] == 3
    # the oldest entries should have been evicted
    assert cache.get(keys[0]) is None
    assert cache.get(keys[-1]) == "value"


def test_stats_track_hits_and_misses():
    cache = ResponseCache()
    key = cache.make_key("x")
    cache.get(key)  # miss
    cache.set(key, "v")
    cache.get(key)  # hit
    cache.get(key)  # hit
    stats = cache.stats()
    assert stats["hits"] == 2
    assert stats["misses"] == 1
