#!/usr/bin/env python3
"""
性能优化模块测试

测试缓存机制、性能优化器和带缓存的包装器
"""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

# Add project root to path: tests/memory_system/test_performance.py -> project root
_project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_project_root))

from infra.memory_system.performance import (
    CachedEmbedder,
    CachedVectorSearch,
    PerformanceOptimizer,
)
from infra.memory_system.utils.cache import (
    CacheManager,
    CacheStats,
    LRUCache,
)


class TestCacheStats:
    """测试缓存统计"""

    def test_initial_state(self):
        """测试初始状态"""
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.hit_rate == 0.0

    def test_record_hit(self):
        """测试记录命中"""
        stats = CacheStats()
        stats.record_hit()
        assert stats.hits == 1
        assert stats.total_requests == 1
        assert stats.hit_rate == 1.0

    def test_record_miss(self):
        """测试记录未命中"""
        stats = CacheStats()
        stats.record_miss()
        assert stats.misses == 1
        assert stats.total_requests == 1
        assert stats.hit_rate == 0.0

    def test_hit_rate_calculation(self):
        """测试命中率计算"""
        stats = CacheStats()
        stats.record_hit()
        stats.record_hit()
        stats.record_miss()
        assert stats.hits == 2
        assert stats.total_requests == 3
        assert stats.hit_rate == pytest.approx(2/3)

    def test_to_dict(self):
        """测试转换为字典"""
        stats = CacheStats()
        stats.record_hit()
        stats.record_miss()

        d = stats.to_dict()
        assert d["hits"] == 1
        assert d["misses"] == 1
        assert d["total_requests"] == 2
        assert "hit_rate" in d


class TestLRUCache:
    """测试 LRU 缓存"""

    def test_basic_set_get(self):
        """测试基本设置和获取"""
        cache = LRUCache(max_size=10)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_cache_miss(self):
        """测试缓存未命中"""
        cache = LRUCache(max_size=10)
        assert cache.get("nonexistent") is None

    def test_lru_eviction(self):
        """测试 LRU 淘汰"""
        cache = LRUCache(max_size=3)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # 触发 key1 的访问
        cache.get("key1")

        # 添加新键，触发淘汰
        cache.set("key4", "value4")

        # key2 应该被淘汰（最久未使用）
        assert cache.get("key2") is None
        assert cache.get("key1") == "value1"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_ttl_expiration(self):
        """测试 TTL 过期"""
        cache = LRUCache(max_size=10, ttl=0.1)
        cache.set("key1", "value1")

        # 立即获取应该成功
        assert cache.get("key1") == "value1"

        # 等待过期
        time.sleep(0.15)

        # 应该过期
        assert cache.get("key1") is None

    def test_update_existing_key(self):
        """测试更新已存在的键"""
        cache = LRUCache(max_size=10)
        cache.set("key1", "value1")
        cache.set("key1", "value2")

        assert cache.get("key1") == "value2"
        assert cache.size() == 1

    def test_delete(self):
        """测试删除"""
        cache = LRUCache(max_size=10)
        cache.set("key1", "value1")
        assert cache.delete("key1") is True
        assert cache.get("key1") is None
        assert cache.delete("nonexistent") is False

    def test_clear(self):
        """测试清空"""
        cache = LRUCache(max_size=10)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()

        assert cache.size() == 0
        assert cache.get("key1") is None

    def test_has(self):
        """测试存在检查"""
        cache = LRUCache(max_size=10, ttl=0.1)
        cache.set("key1", "value1")

        assert cache.has("key1") is True
        assert cache.has("nonexistent") is False

        time.sleep(0.15)
        assert cache.has("key1") is False

    def test_get_or_compute(self):
        """测试 get_or_compute"""
        cache = LRUCache(max_size=10)
        compute_fn = Mock(return_value="computed")

        # 第一次调用
        result1 = cache.get_or_compute("key1", compute_fn)
        assert result1 == "computed"
        compute_fn.assert_called_once()

        # 第二次调用应该使用缓存
        result2 = cache.get_or_compute("key1", compute_fn)
        assert result2 == "computed"
        # compute_fn 不应该再次调用
        compute_fn.assert_called_once()

    def test_stats_tracking(self):
        """测试统计跟踪"""
        cache = LRUCache(max_size=10, track_stats=True)
        cache.set("key1", "value1")

        # 命中
        cache.get("key1")
        cache.get("key1")

        # 未命中
        cache.get("nonexistent")

        stats = cache.get_stats()
        assert stats.hits == 2
        assert stats.misses == 1
        assert stats.hit_rate == pytest.approx(2/3)


class TestCacheManager:
    """测试缓存管理器"""

    def test_get_cache_creates_new(self):
        """测试获取缓存时创建新的"""
        manager = CacheManager()
        cache = manager.get_cache("test")

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_cache_returns_same(self):
        """测试获取缓存返回同一个"""
        manager = CacheManager()
        cache1 = manager.get_cache("test")
        cache2 = manager.get_cache("test")

        assert cache1 is cache2

    def test_global_stats(self):
        """测试全局统计"""
        manager = CacheManager()

        cache1 = manager.get_cache("cache1", track_stats=True)
        cache2 = manager.get_cache("cache2", track_stats=True)

        cache1.set("k1", "v1")
        cache1.get("k1")
        cache1.get("nonexistent")

        cache2.set("k2", "v2")
        cache2.get("k2")

        stats = manager.get_total_stats()
        assert stats["total_hits"] == 2
        assert stats["total_misses"] == 1
        assert stats["total_requests"] == 3

    def test_clear_all(self):
        """测试清空所有缓存"""
        manager = CacheManager()
        cache1 = manager.get_cache("cache1")
        cache2 = manager.get_cache("cache2")

        cache1.set("key1", "value1")
        cache2.set("key2", "value2")

        manager.clear_all()

        assert cache1.size() == 0
        assert cache2.size() == 0


class TestPerformanceOptimizer:
    """测试性能优化器"""

    def test_init(self):
        """测试初始化"""
        optimizer = PerformanceOptimizer()
        assert optimizer is not None

    def test_configure_caches(self):
        """测试配置缓存"""
        optimizer = PerformanceOptimizer()

        optimizer.configure_embedding_cache(max_size=1000, ttl=3600)
        optimizer.configure_character_cache(max_size=500, ttl=1800)
        optimizer.configure_query_cache(max_size=200, ttl=600)

        stats = optimizer.get_total_stats()
        assert stats["cache_count"] == 3

    def test_cache_summary(self):
        """测试获取缓存摘要"""
        optimizer = PerformanceOptimizer()
        optimizer.configure_embedding_cache(max_size=1000)

        # 使用缓存
        cache = optimizer.get_cache("embeddings")
        cache.set("test", "value")

        summary = optimizer.get_cache_summary()
        assert "overall_hit_rate" in summary
        assert "caches" in summary
        assert "optimizations" in summary

    def test_clear_all(self):
        """测试清空所有缓存"""
        optimizer = PerformanceOptimizer()
        optimizer.configure_embedding_cache(max_size=100)

        cache = optimizer.get_cache("embeddings")
        cache.set("key1", "value1")

        optimizer.clear_all_caches()
        assert cache.size() == 0


class TestCachedEmbedder:
    """测试带缓存的嵌入器"""

    def test_disabled_cache(self):
        """测试禁用缓存"""
        mock_embedder = Mock()
        mock_embedder.embed_texts.return_value = [[1.0, 2.0], [3.0, 4.0]]

        cached = CachedEmbedder(mock_embedder, enabled=False)

        results = cached.embed_texts(["text1", "text2"])

        assert results == [[1.0, 2.0], [3.0, 4.0]]
        mock_embedder.embed_texts.assert_called_once()

    def test_cache_hit(self):
        """测试缓存命中"""
        mock_embedder = Mock()
        mock_embedder.embed_texts.return_value = [[1.0, 2.0]]

        cache = LRUCache(max_size=10)
        cached_embedder = CachedEmbedder(mock_embedder, cache)

        # 预先通过 cached_embedder 设置缓存
        cached_embedder.embed_texts(["text1"])

        # 重置 mock 以跟踪下次调用
        mock_embedder.reset_mock()

        results = cached_embedder.embed_texts(["text1"])

        # 应该从缓存获取，不调用 base_embedder
        assert results == [[1.0, 2.0]]
        mock_embedder.embed_texts.assert_not_called()

    def test_cache_miss_then_populate(self):
        """测试缓存未命中后填充"""
        mock_embedder = Mock()
        mock_embedder.embed_texts.return_value = [[5.0, 6.0]]

        cache = LRUCache(max_size=10)
        cached = CachedEmbedder(mock_embedder, cache)

        results = cached.embed_texts(["new_text"])

        assert results == [[5.0, 6.0]]
        mock_embedder.embed_texts.assert_called_once()

        # 再次获取应该命中
        results2 = cached.embed_texts(["new_text"])
        assert results2 == [[5.0, 6.0]]
        # 不应该再次调用 embedder
        mock_embedder.embed_texts.assert_called_once()


class TestCachedVectorSearch:
    """测试带缓存的向量搜索"""

    def test_disabled_cache(self):
        """测试禁用缓存"""
        mock_client = Mock()
        mock_client.search.return_value = [{"id": "1", "score": 0.9}]

        cached = CachedVectorSearch(mock_client, enabled=False)

        results = cached.search(
            collection_name="test",
            query_vector=[1.0, 2.0, 3.0],
            top_k=5
        )

        assert results == [{"id": "1", "score": 0.9}]
        mock_client.search.assert_called_once()

    def test_cache_miss_then_populate(self):
        """测试缓存未命中后填充"""
        mock_client = Mock()
        mock_client.search.return_value = [{"id": "2", "score": 0.8}]

        cache = LRUCache(max_size=10)
        cached = CachedVectorSearch(mock_client, cache)

        results = cached.search(
            collection_name="chapters_seg",
            query_vector=[1.0, 2.0, 3.0],
            top_k=5
        )

        assert results == [{"id": "2", "score": 0.8}]
        mock_client.search.assert_called_once()


class TestPerformanceRequirements:
    """测试性能需求（响应时间 < 2秒，缓存命中率可统计）"""

    def test_cache_hit_response_time(self):
        """测试缓存命中时响应时间 < 2秒"""
        cache = LRUCache(max_size=1000)

        # 预热缓存
        for i in range(100):
            cache.set(f"key_{i}", f"value_{i}")

        # 测试缓存命中响应时间
        start = time.time()
        for _ in range(1000):
            cache.get("key_50")
        elapsed = time.time() - start

        assert elapsed < 2.0, f"Cache hit response time {elapsed}s exceeds 2s"

    def test_cache_stats_availability(self):
        """测试缓存命中率可统计"""
        cache = LRUCache(max_size=100, track_stats=True)

        # 模拟 80% 命中率场景
        for i in range(100):
            cache.set(f"key_{i}", f"value_{i}")

        # 80 次命中，20 次未命中
        for i in range(80):
            cache.get(f"key_{i % 50}")  # 50 个 key 全部命中
        for i in range(20):
            cache.get("nonexistent")

        stats = cache.get_stats()
        assert stats.total_requests == 100
        assert stats.hit_rate >= 0.75  # 允许一些误差


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
