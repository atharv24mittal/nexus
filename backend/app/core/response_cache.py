"""
response_cache.py
------------------
A tiny in-memory cache for LLM-backed responses that are genuinely safe to
cache: given the EXACT same (problem, code) pair, an explanation or hint is
fine to reuse rather than re-spend a Groq API call and ~1-2s of latency.

This is NOT used anywhere on the actual /solve path (a generation result
must never be cached — every solve should be a fresh attempt) — only on
/explain and /hint, which are pure functions of their input from the
caller's perspective.

Deliberately a plain dict with a max size + FIFO eviction, not a real LRU
library: this is small, auditable, and entirely sufficient for a single
free-tier instance. No Redis, no extra paid infrastructure.
"""

from __future__ import annotations

import hashlib
from collections import OrderedDict

MAX_ENTRIES = 500


class ResponseCache:
    def __init__(self, max_entries: int = MAX_ENTRIES):
        self._store: OrderedDict[str, str] = OrderedDict()
        self._max_entries = max_entries
        self.hits = 0
        self.misses = 0

    @staticmethod
    def make_key(*parts: str) -> str:
        joined = "||".join(parts)
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()

    def get(self, key: str) -> str | None:
        if key in self._store:
            self.hits += 1
            self._store.move_to_end(key)  # mark as recently used
            return self._store[key]
        self.misses += 1
        return None

    def set(self, key: str, value: str) -> None:
        self._store[key] = value
        self._store.move_to_end(key)
        if len(self._store) > self._max_entries:
            self._store.popitem(last=False)  # evict oldest

    def stats(self) -> dict:
        total = self.hits + self.misses
        return {
            "entries": len(self._store),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 3) if total else 0.0,
        }
