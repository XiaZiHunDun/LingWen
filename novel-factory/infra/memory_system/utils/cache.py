"""缓存工具模块

提供通用缓存功能，支持：
- LRU 缓存策略
- 缓存命中率统计
- TTL（过期时间）支持
- 线程安全
"""

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


@dataclass
class CacheStats:
    """缓存统计信息"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0

    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    @property
    def miss_rate(self) -> float:
        """缓存未命中率"""
        return 1.0 - self.hit_rate

    def record_hit(self) -> None:
        """记录缓存命中"""
        self.hits += 1
        self.total_requests += 1

    def record_miss(self) -> None:
        """记录缓存未命中"""
        self.misses += 1
        self.total_requests += 1

    def record_eviction(self) -> None:
        """记录缓存淘汰"""
        self.evictions += 1

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "total_requests": self.total_requests,
            "hit_rate": round(self.hit_rate, 4),
            "miss_rate": round(self.miss_rate, 4),
        }


@dataclass
class CacheEntry:
    """缓存条目"""
    value: Any
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0

    def is_expired(self, ttl: Optional[float]) -> bool:
        """检查是否过期"""
        if ttl is None:
            return False
        return (time.time() - self.created_at) > ttl

    def touch(self) -> None:
        """更新访问时间"""
        self.last_accessed = time.time()
        self.access_count += 1


class LRUCache:
    """线程安全的 LRU 缓存

    特性：
    - LRU 淘汰策略
    - 可选 TTL 过期时间
    - 缓存命中率统计
    - 线程安全

    Usage:
        cache = LRUCache(max_size=1000, ttl=3600)  # 最多1000条，1小时过期

        # 设置缓存
        cache.set("key", "value")

        # 获取缓存
        value = cache.get("key")

        # 获取统计
        stats = cache.get_stats()
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl: Optional[float] = None,
        track_stats: bool = True
    ):
        """初始化 LRU 缓存

        Args:
            max_size: 最大缓存条目数
            ttl: 过期时间（秒），None 表示永不过期
            track_stats: 是否跟踪统计信息
        """
        self._max_size = max_size
        self._ttl = ttl
        self._track_stats = track_stats
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats() if track_stats else None

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或已过期则返回 None
        """
        with self._lock:
            if key not in self._cache:
                if self._stats:
                    self._stats.record_miss()
                return None

            entry = self._cache[key]

            # 检查过期
            if entry.is_expired(self._ttl):
                del self._cache[key]
                if self._stats:
                    self._stats.record_miss()
                    self._stats.record_eviction()
                return None

            # 更新访问顺序（移到末尾表示最近使用）
            self._cache.move_to_end(key)
            entry.touch()

            if self._stats:
                self._stats.record_hit()

            return entry.value

    def set(self, key: str, value: Any) -> None:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
        """
        with self._lock:
            # 如果 key 已存在，更新值
            if key in self._cache:
                self._cache[key].value = value
                self._cache[key].touch()
                self._cache.move_to_end(key)
                return

            # 如果缓存已满，淘汰最旧的条目
            if len(self._cache) >= self._max_size:
                # 移除最旧的条目（第一个）
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                if self._stats:
                    self._stats.record_eviction()

            # 添加新条目
            self._cache[key] = CacheEntry(value=value)

    def delete(self, key: str) -> bool:
        """删除缓存条目

        Args:
            key: 缓存键

        Returns:
            是否成功删除
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            if self._stats:
                self._stats = CacheStats()

    def has(self, key: str) -> bool:
        """检查键是否存在且未过期

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        with self._lock:
            if key not in self._cache:
                return False
            entry = self._cache[key]
            if entry.is_expired(self._ttl):
                del self._cache[key]
                if self._stats:
                    self._stats.record_eviction()
                return False
            return True

    def get_stats(self) -> Optional[CacheStats]:
        """获取缓存统计信息

        Returns:
            CacheStats 对象，如果未启用统计则返回 None
        """
        return self._stats

    def size(self) -> int:
        """获取当前缓存大小"""
        with self._lock:
            return len(self._cache)

    def keys(self) -> list[str]:
        """获取所有缓存键"""
        with self._lock:
            return list(self._cache.keys())

    def get_or_compute(self, key: str, compute_fn: Callable[[], Any]) -> Any:
        """获取缓存值，如果不存在则计算并缓存

        Args:
            key: 缓存键
            compute_fn: 计算函数

        Returns:
            缓存值或计算结果
        """
        value = self.get(key)
        if value is not None:
            return value

        # 计算新值
        value = compute_fn()
        self.set(key, value)
        return value


class CacheManager:
    """缓存管理器

    管理多个命名的缓存，支持：
    - 按名称访问缓存
    - 统一统计
    - 全局 TTL 设置

    Usage:
        manager = CacheManager()

        # 创建/获取命名缓存
        cache = manager.get_cache("embeddings", max_size=5000, ttl=3600)

        # 获取全局统计
        stats = manager.get_global_stats()
    """

    def __init__(self, default_ttl: Optional[float] = None):
        """初始化缓存管理器

        Args:
            default_ttl: 默认过期时间（秒）
        """
        self._default_ttl = default_ttl
        self._caches: Dict[str, LRUCache] = {}
        self._lock = threading.RLock()

    def get_cache(
        self,
        name: str,
        max_size: int = 1000,
        ttl: Optional[float] = None,
        track_stats: bool = True
    ) -> LRUCache:
        """获取或创建命名缓存

        Args:
            name: 缓存名称
            max_size: 最大缓存条目数
            ttl: 过期时间（秒），None 使用管理器默认值
            track_stats: 是否跟踪统计信息

        Returns:
            LRUCache 实例
        """
        with self._lock:
            if name in self._caches:
                return self._caches[name]

            # 使用管理器默认值如果未指定
            effective_ttl = ttl if ttl is not None else self._default_ttl

            cache = LRUCache(
                max_size=max_size,
                ttl=effective_ttl,
                track_stats=track_stats
            )
            self._caches[name] = cache
            return cache

    def delete_cache(self, name: str) -> bool:
        """删除命名缓存

        Args:
            name: 缓存名称

        Returns:
            是否成功删除
        """
        with self._lock:
            if name in self._caches:
                del self._caches[name]
                return True
            return False

    def clear_all(self) -> None:
        """清空所有缓存"""
        with self._lock:
            for cache in self._caches.values():
                cache.clear()

    def get_global_stats(self) -> Dict[str, CacheStats]:
        """获取所有缓存的统计信息

        Returns:
            统计信息字典，键为缓存名称
        """
        with self._lock:
            result = {}
            for name, cache in self._caches.items():
                stats = cache.get_stats()
                if stats:
                    result[name] = stats.to_dict()
            return result

    def get_total_stats(self) -> Dict[str, Any]:
        """获取汇总统计信息

        Returns:
            汇总后的统计信息
        """
        with self._lock:
            total_hits = 0
            total_misses = 0
            total_evictions = 0
            total_requests = 0

            for cache in self._caches.values():
                stats = cache.get_stats()
                if stats:
                    total_hits += stats.hits
                    total_misses += stats.misses
                    total_evictions += stats.evictions
                    total_requests += stats.total_requests

            hit_rate = total_hits / total_requests if total_requests > 0 else 0.0

            return {
                "total_hits": total_hits,
                "total_misses": total_misses,
                "total_evictions": total_evictions,
                "total_requests": total_requests,
                "overall_hit_rate": round(hit_rate, 4),
                "cache_count": len(self._caches),
            }
