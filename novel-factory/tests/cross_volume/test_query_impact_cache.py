"""Phase 9.42 F31: QueryImpactCache tests."""
from __future__ import annotations

import time

from infra.cross_volume.cache import QueryImpactCache


class TestQueryImpactCache:
    def test_hit_after_set(self):
        cache = QueryImpactCache(maxsize=10, ttl_seconds=60.0)
        key = QueryImpactCache.make_key("node-a", 3)
        cache.set(key, ("e1", "e2"))
        assert cache.get(key) == ("e1", "e2")
        assert cache.hits == 1
        assert cache.misses == 0

    def test_miss_on_unknown_key(self):
        cache = QueryImpactCache()
        assert cache.get("missing") is None
        assert cache.misses == 1

    def test_ttl_expiry(self):
        cache = QueryImpactCache(maxsize=10, ttl_seconds=0.05)
        key = "k1"
        cache.set(key, ("e1",))
        assert cache.get(key) == ("e1",)
        time.sleep(0.06)
        assert cache.get(key) is None
        assert cache.misses == 1

    def test_lru_eviction(self):
        cache = QueryImpactCache(maxsize=2, ttl_seconds=60.0)
        cache.set("a", ("1",))
        cache.set("b", ("2",))
        cache.set("c", ("3",))
        assert cache.get("a") is None
        assert cache.get("b") == ("2",)
        assert cache.get("c") == ("3",)

    def test_invalidate_clears_all(self):
        cache = QueryImpactCache()
        cache.set("a", ("1",))
        cache.set("b", ("2",))
        cache.invalidate()
        assert cache.stats()["size"] == 0
        assert cache.get("a") is None
