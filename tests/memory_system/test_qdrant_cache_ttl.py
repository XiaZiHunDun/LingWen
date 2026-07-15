# tests/memory_system/test_qdrant_cache_ttl.py
"""Phase 14.0 T3: _LRUCache TTL stale eviction RED→GREEN tests.

新增 `ttl_seconds: float = 300.0` 字段给 `_LRUCache`, 防 chapter 新版本覆盖
时旧 embedding 的 vector search cache 命中 stale entry 占用 LRU slot。

测试覆盖:
1. `get` 移除 stale entry (now-10, ttl=5 → None)
2. `get` 返回 fresh entry (now, ttl=300 → value)
3. `ttl=0` 等价禁用 cache (put 后 get 仍 None)
4. `put` 同 key 只刷 value 保 ts (fast TTL 不被人为延长)
"""
from __future__ import annotations

import time

import pytest

from infra.memory_system.vector.qdrant_client import _LRUCache


def _make_cache(ttl: float = 300.0, max_size: int = 100) -> _LRUCache:
    """Phase 14.0 T3: new ttl_seconds kwarg."""
    return _LRUCache(max_size=max_size, ttl_seconds=ttl)


class TestLRUCacheTTL:
    def test_get_removes_stale_entry(self):
        """put(key, value, ts=now-10), ttl=5; get(返回 None 因 stale)。"""
        cache = _make_cache(ttl=5.0)
        cache.put("k1", "v1", ts=time.monotonic() - 10.0)
        assert cache.get("k1") is None, "stale entry should be evicted and return None"

    def test_get_returns_fresh_entry(self):
        """put(key, value, ts=now), ttl=300; get 返回 value。"""
        cache = _make_cache(ttl=300.0)
        cache.put("k1", "v1", ts=time.monotonic())
        assert cache.get("k1") == "v1", "fresh entry should be returned"

    def test_ttl_zero_disables_cache(self):
        """ttl=0 等价禁用: put 后 get 仍 None (或每次都 miss)。"""
        cache = _make_cache(ttl=0.0)
        cache.put("k1", "v1", ts=time.monotonic())
        assert cache.get("k1") is None, "TTL=0 cache should always miss"

    def test_put_same_key_keeps_original_ts(self):
        """同 key 多次 put, ts 不刷; fast TTL 时不被人为延长。"""
        cache = _make_cache(ttl=5.0)
        original_ts = time.monotonic() - 4.5  # 0.5s within window
        cache.put("k1", "v1-original", ts=original_ts)
        # Re-put same key 1s later (still within window, ts unchanged)
        cache.put("k1", "v1-updated", ts=time.monotonic())
        # Should still be fresh because original_ts is unchanged
        result = cache.get("k1")
        assert result == "v1-updated", "value updated but ts preserved"
        # After original_ts + 5s, even with re-put, should expire
        # Simulate by waiting past original_ts + ttl
        # (Don't actually sleep in test — instead verify using direct ts check)
        cache._cache["k1"]  # type: ignore[attr-defined]
        # Reconstruct: cache now has (v1-updated, original_ts)
        stored_value, stored_ts = cache._cache["k1"]  # type: ignore[attr-defined]
        assert stored_ts == original_ts, "ts should not be refreshed on re-put of same key"
