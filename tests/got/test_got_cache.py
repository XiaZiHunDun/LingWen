"""Tests for got.cache (ThoughtCache).

Phase 1.4.e — RED tests for ThoughtCache.

设计约束 (per Doc 4 v1.0):
- ThoughtCache: 节点输出缓存
- hash_inputs(inputs): SHA-256(json.dumps(inputs, sort_keys=True))[:16]
- get_or_compute(node, inputs_hash, compute_fn):
  - 命中 → 返回缓存
  - 未命中 → 调 compute_fn 存结果 → 返回
"""
from __future__ import annotations

import pytest


class TestHashInputs:
    def test_hash_stable(self):
        from infra.got.cache import ThoughtCache

        cache = ThoughtCache()
        h1 = cache.hash_inputs({"a": 1, "b": 2})
        h2 = cache.hash_inputs({"a": 1, "b": 2})
        assert h1 == h2
        assert isinstance(h1, str)
        assert len(h1) == 16  # SHA-256 前 16 字符

    def test_hash_key_order_independent(self):
        """sort_keys=True → dict key 顺序不影响 hash"""
        from infra.got.cache import ThoughtCache

        cache = ThoughtCache()
        h1 = cache.hash_inputs({"a": 1, "b": 2})
        h2 = cache.hash_inputs({"b": 2, "a": 1})
        assert h1 == h2

    def test_hash_value_changes(self):
        from infra.got.cache import ThoughtCache

        cache = ThoughtCache()
        h1 = cache.hash_inputs({"a": 1})
        h2 = cache.hash_inputs({"a": 2})
        assert h1 != h2


class TestGetOrCompute:
    def test_compute_on_miss(self):
        from infra.got.cache import ThoughtCache

        cache = ThoughtCache()
        call_count = [0]

        def compute():
            call_count[0] += 1
            return "computed_value"

        result = cache.get_or_compute("n1", "hash_abc", compute)
        assert result == "computed_value"
        assert call_count[0] == 1

    def test_cache_hit(self):
        from infra.got.cache import ThoughtCache

        cache = ThoughtCache()
        call_count = [0]

        def compute():
            call_count[0] += 1
            return "computed_value"

        # 第 1 次: 缓存未命中 → 计算
        result1 = cache.get_or_compute("n1", "hash_abc", compute)
        # 第 2 次: 缓存命中 → 不再计算
        result2 = cache.get_or_compute("n1", "hash_abc", compute)
        assert result1 == result2 == "computed_value"
        assert call_count[0] == 1  # 只算 1 次

    def test_different_hashes_different_results(self):
        from infra.got.cache import ThoughtCache

        cache = ThoughtCache()
        call_count = [0]

        def compute():
            call_count[0] += 1
            return f"value_{call_count[0]}"

        r1 = cache.get_or_compute("n1", "hash_a", compute)
        r2 = cache.get_or_compute("n1", "hash_b", compute)
        assert r1 == "value_1"
        assert r2 == "value_2"
        assert call_count[0] == 2

    def test_clear_cache(self):
        from infra.got.cache import ThoughtCache

        cache = ThoughtCache()
        call_count = [0]

        def compute():
            call_count[0] += 1
            return "x"

        cache.get_or_compute("n1", "h", compute)
        cache.clear()
        cache.get_or_compute("n1", "h", compute)
        assert call_count[0] == 2  # 清空后重算

    def test_cache_size(self):
        from infra.got.cache import ThoughtCache

        cache = ThoughtCache()
        cache.get_or_compute("n1", "h1", lambda: 1)
        cache.get_or_compute("n2", "h2", lambda: 2)
        assert cache.size() == 2
