"""性能优化模块

提供性能优化功能：
- 向量嵌入缓存
- 查询结果缓存
- 角色状态缓存
- 统计信息收集

Usage:
    from memory_system.performance import PerformanceOptimizer

    optimizer = PerformanceOptimizer()
    optimizer.configure_embedding_cache(max_size=5000, ttl=3600)
    optimizer.configure_query_cache(max_size=1000, ttl=600)

    # 使用优化后的引擎
    optimized_engine = optimizer.wrap_query_engine(query_engine)
"""
import hashlib
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from infra.memory_system.utils.cache import CacheManager, CacheStats, LRUCache


class PerformanceOptimizer:
    """性能优化器

    管理所有缓存，提供统一的性能优化接口。

    Usage:
        optimizer = PerformanceOptimizer()

        # 配置各类缓存
        optimizer.configure_embedding_cache(max_size=5000, ttl=3600)
        optimizer.configure_character_cache(max_size=500, ttl=1800)

        # 获取缓存统计
        stats = optimizer.get_global_stats()
    """

    def __init__(self, default_ttl: Optional[float] = 3600):
        """初始化性能优化器

        Args:
            default_ttl: 默认缓存过期时间（秒）
        """
        self._cache_manager = CacheManager(default_ttl=default_ttl)
        self._lock = threading.RLock()
        self._optimizations_enabled: Dict[str, bool] = {
            "embedding_cache": True,
            "character_cache": True,
            "query_cache": True,
        }

    def configure_embedding_cache(
        self,
        max_size: int = 5000,
        ttl: Optional[float] = 3600,
        enabled: bool = True
    ) -> None:
        """配置向量嵌入缓存

        Args:
            max_size: 最大缓存条目数
            ttl: 过期时间（秒）
            enabled: 是否启用
        """
        with self._lock:
            self._cache_manager.get_cache(
                "embeddings",
                max_size=max_size,
                ttl=ttl,
                track_stats=True
            )
            self._optimizations_enabled["embedding_cache"] = enabled

    def configure_character_cache(
        self,
        max_size: int = 500,
        ttl: Optional[float] = 1800,
        enabled: bool = True
    ) -> None:
        """配置角色状态缓存

        Args:
            max_size: 最大缓存条目数
            ttl: 过期时间（秒）
            enabled: 是否启用
        """
        with self._lock:
            self._cache_manager.get_cache(
                "character_states",
                max_size=max_size,
                ttl=ttl,
                track_stats=True
            )
            self._optimizations_enabled["character_cache"] = enabled

    def configure_query_cache(
        self,
        max_size: int = 1000,
        ttl: Optional[float] = 600,
        enabled: bool = True
    ) -> None:
        """配置查询结果缓存

        Args:
            max_size: 最大缓存条目数
            ttl: 过期时间（秒）
            enabled: 是否启用
        """
        with self._lock:
            self._cache_manager.get_cache(
                "query_results",
                max_size=max_size,
                ttl=ttl,
                track_stats=True
            )
            self._optimizations_enabled["query_cache"] = enabled

    def get_cache(self, name: str) -> LRUCache:
        """获取指定名称的缓存

        Args:
            name: 缓存名称

        Returns:
            LRUCache 实例
        """
        return self._cache_manager.get_cache(name)

    def is_enabled(self, optimization: str) -> bool:
        """检查优化是否启用

        Args:
            optimization: 优化名称

        Returns:
            是否启用
        """
        return self._optimizations_enabled.get(optimization, False)

    def get_global_stats(self) -> Dict[str, Any]:
        """获取全局统计信息

        Returns:
            统计信息字典
        """
        return self._cache_manager.get_global_stats()

    def get_total_stats(self) -> Dict[str, Any]:
        """获取汇总统计信息

        Returns:
            汇总统计
        """
        return self._cache_manager.get_total_stats()

    def clear_all_caches(self) -> None:
        """清空所有缓存"""
        self._cache_manager.clear_all()

    def get_cache_summary(self) -> Dict[str, Any]:
        """获取缓存摘要

        Returns:
            缓存摘要信息
        """
        stats = self.get_total_stats()
        caches = {}

        cache_names = ["embeddings", "character_states", "query_results"]
        for name in cache_names:
            try:
                cache = self._cache_manager.get_cache(name)
                caches[name] = {
                    "size": cache.size(),
                    "enabled": self.is_enabled(name.replace("_", "_") + "_cache"),
                }
            except Exception:
                pass

        return {
            "total_requests": stats.get("total_requests", 0),
            "overall_hit_rate": stats.get("overall_hit_rate", 0.0),
            "cache_count": stats.get("cache_count", 0),
            "caches": caches,
            "optimizations": self._optimizations_enabled.copy(),
        }


class CachedEmbedder:
    """带缓存的嵌入器包装器

    包装 Embedder，自动缓存嵌入结果。

    Usage:
        from infra.memory_system.vector.embedder import Embedder
        from infra.memory_system.performance import CachedEmbedder, PerformanceOptimizer

        optimizer = PerformanceOptimizer()
        base_embedder = Embedder(...)
        cached_embedder = CachedEmbedder(base_embedder, optimizer.get_cache("embeddings"))

        # 正常使用
        vectors = cached_embedder.embed_texts(["text"])
    """

    def __init__(
        self,
        base_embedder: Any,
        cache: Optional[LRUCache] = None,
        enabled: bool = True
    ):
        """初始化带缓存的嵌入器

        Args:
            base_embedder: 基础嵌入器
            cache: 缓存实例
            enabled: 是否启用缓存
        """
        self._base_embedder = base_embedder
        self._cache = cache
        self._enabled = enabled

    def _make_cache_key(self, text: str) -> str:
        """生成缓存键

        Args:
            text: 文本

        Returns:
            缓存键
        """
        return hashlib.sha256(text.encode()).hexdigest()[:32]

    def embed_texts(self, texts: List[str], **kwargs) -> List[List[float]]:
        """嵌入文本（带缓存）

        Args:
            texts: 文本列表
            **kwargs: 额外参数

        Returns:
            嵌入向量列表
        """
        if not self._enabled or self._cache is None:
            return self._base_embedder.embed_texts(texts, **kwargs)

        results = []
        texts_to_embed = []
        cache_keys = []

        # 检查缓存
        for text in texts:
            cache_key = self._make_cache_key(text)
            cache_keys.append(cache_key)

            cached = self._cache.get(cache_key)
            if cached is not None:
                results.append(cached)
            else:
                texts_to_embed.append(text)
                results.append(None)  # 占位符

        # 批量嵌入未缓存的文本
        if texts_to_embed:
            new_vectors = self._base_embedder.embed_texts(texts_to_embed, **kwargs)

            # 填充结果并更新缓存
            result_idx = 0
            for i, result in enumerate(results):
                if result is None:
                    results[i] = new_vectors[result_idx]
                    self._cache.set(cache_keys[i], new_vectors[result_idx])
                    result_idx += 1

        return results

    def embed_query(self, query: str, **kwargs) -> List[float]:
        """嵌入单个查询

        Args:
            query: 查询文本
            **kwargs: 额外参数

        Returns:
            嵌入向量
        """
        vectors = self.embed_texts([query], purpose="query")
        return vectors[0] if vectors else []

    @property
    def cache(self) -> Optional[LRUCache]:
        """获取缓存"""
        return self._cache

    @cache.setter
    def cache(self, cache: LRUCache) -> None:
        """设置缓存"""
        self._cache = cache

    @property
    def enabled(self) -> bool:
        """获取缓存启用状态"""
        return self._enabled

    @enabled.setter
    def enabled(self, enabled: bool) -> None:
        """设置缓存启用状态"""
        self._enabled = enabled


class CachedVectorSearch:
    """带缓存的向量搜索包装器

    包装 QdrantClientWrapper，自动缓存搜索结果。

    Usage:
        from infra.memory_system.vector.qdrant_client import QdrantClientWrapper
        from memory_system.performance import CachedVectorSearch, PerformanceOptimizer

        optimizer = PerformanceOptimizer()
        base_client = QdrantClientWrapper(...)
        cached_client = CachedVectorSearch(base_client, optimizer.get_cache("query_results"))

        # 正常使用
        results = cached_client.search(collection_name="chapters_seg", query_vector=[...])
    """

    def __init__(
        self,
        base_client: Any,
        cache: Optional[LRUCache] = None,
        enabled: bool = True
    ):
        """初始化带缓存的向量搜索

        Args:
            base_client: 基础客户端
            cache: 缓存实例
            enabled: 是否启用缓存
        """
        self._base_client = base_client
        self._cache = cache
        self._enabled = enabled

    def _make_cache_key(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int,
        query_filter: Any
    ) -> str:
        """生成缓存键

        使用向量前几个维度 + collection + top_k 生成键
        """
        # 使用向量的前几个值作为键的一部分
        vec_prefix = ",".join(str(v) for v in query_vector[:8])
        filter_str = str(query_filter) if query_filter else "none"

        key_str = f"{collection_name}:{vec_prefix}:{top_k}:{filter_str}"
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: Optional[int] = None,
        query_filter: Any = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """搜索（带缓存）

        Args:
            collection_name: 集合名称
            query_vector: 查询向量
            top_k: 返回数量
            query_filter: 过滤条件
            **kwargs: 额外参数

        Returns:
            搜索结果列表
        """
        if not self._enabled or self._cache is None:
            return self._base_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                top_k=top_k,
                query_filter=query_filter,
                **kwargs
            )

        cache_key = self._make_cache_key(
            collection_name, query_vector, top_k or 5, query_filter
        )

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        results = self._base_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            top_k=top_k,
            query_filter=query_filter,
            **kwargs
        )

        self._cache.set(cache_key, results)
        return results

    def __getattr__(self, name: str) -> Any:
        """代理其他方法到基础客户端"""
        return getattr(self._base_client, name)

    @property
    def cache(self) -> Optional[LRUCache]:
        """获取缓存"""
        return self._cache

    @cache.setter
    def cache(self, cache: LRUCache) -> None:
        """设置缓存"""
        self._cache = cache

    @property
    def enabled(self) -> bool:
        """获取缓存启用状态"""
        return self._enabled

    @enabled.setter
    def enabled(self, enabled: bool) -> None:
        """设置缓存启用状态"""
        self._enabled = enabled


def create_cached_embedder(
    base_embedder: Any,
    optimizer: Optional[PerformanceOptimizer] = None,
    cache_name: str = "embeddings"
) -> CachedEmbedder:
    """创建带缓存的嵌入器

    Args:
        base_embedder: 基础嵌入器
        optimizer: 性能优化器（可选）
        cache_name: 缓存名称

    Returns:
        CachedEmbedder 实例
    """
    cache = optimizer.get_cache(cache_name) if optimizer else None
    return CachedEmbedder(base_embedder, cache)


def create_cached_vector_client(
    base_client: Any,
    optimizer: Optional[PerformanceOptimizer] = None,
    cache_name: str = "query_results"
) -> CachedVectorSearch:
    """创建带缓存的向量客户端

    Args:
        base_client: 基础客户端
        optimizer: 性能优化器（可选）
        cache_name: 缓存名称

    Returns:
        CachedVectorSearch 实例
    """
    cache = optimizer.get_cache(cache_name) if optimizer else None
    return CachedVectorSearch(base_client, cache)
