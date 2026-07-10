"""Qdrant 客户端封装

封装 Qdrant 向量数据库连接和操作接口。
支持 memory_system/config/memory_config.yaml 中的配置。
支持 memory_system/config/collections_schema.yaml 中定义的集合。

优化特性:
- upsert_batch: 大批量插入分批提交
- LRU 缓存: search 操作结果缓存
- batch_search: 批量查询多个向量
- timeout: 单次请求超时（默认30秒）
- retry: 自动重试机制（默认3次）
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import threading
import time
from collections import OrderedDict
from functools import wraps
from typing import Any, Callable, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointIdsList,
    PointStruct,
    VectorParams,
)

from infra.memory_system.config import load_yaml

logger = logging.getLogger(__name__)


def with_retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """带指数退避重试的装饰器

    Args:
        max_retries: 最大重试次数，默认3
        delay: 初始重试延迟（秒），默认1
        backoff: 退避系数，默认2（1s, 2s, 4s...）

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}: {e}")
            raise last_exception
        return wrapper
    return decorator


class _LRUCache:
    """简单的 LRU 缓存实现，线程安全"""

    def __init__(self, max_size: int = 1000):
        self._max_size = max_size
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值，如果存在则移动到末尾"""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
            return None

    def put(self, key: str, value: Any) -> None:
        """存入缓存，超限时移除最旧的项"""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self._max_size:
                    self._cache.popitem(last=False)
            self._cache[key] = value

    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()

    def clear_collection(self, collection_name: str) -> None:
        """清除指定集合相关的所有缓存条目"""
        with self._lock:
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{collection_name}:")]
            for key in keys_to_remove:
                del self._cache[key]

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)


def _make_filter_hash(filter_obj: Optional[Filter]) -> str:
    """生成过滤器的哈希值用于缓存键"""
    if filter_obj is None:
        return "no_filter"
    # 将 filter 对象转换为字符串后哈希
    filter_str = str(filter_obj)
    return hashlib.md5(filter_str.encode()).hexdigest()[:12]


class QdrantClientWrapper:
    """Qdrant 客户端封装类

    提供向量存储和检索接口，支持以下集合：
    - chapters_seg: 章节内容片段向量
    - entities: 实体向量（角色/物品/地点）
    - relationships: 关系向量
    """

    COLLECTIONS_CONFIG_PATH = "config/collections_schema.yaml"
    MEMORY_CONFIG_PATH = "config/memory_config.yaml"

    # Distance 映射
    DISTANCE_MAP = {
        "Cosine": Distance.COSINE,
        "Euclidean": Distance.EUCLID,
        "Dot": Distance.DOT,
    }

    def __init__(self, cache_size: int = 1000, default_batch_size: int = 100):
        """初始化 Qdrant 客户端

        Args:
            cache_size: LRU 缓存大小，默认 1000
            default_batch_size: 默认批量操作大小，默认 100
        """
        # 加载配置
        try:
            memory_config = load_yaml(self.MEMORY_CONFIG_PATH)
            collections_config = load_yaml(self.COLLECTIONS_CONFIG_PATH)
        except FileNotFoundError as e:
            raise RuntimeError(f"Failed to load configuration: {e}")

        # Qdrant 连接配置
        qdrant_config = memory_config["qdrant"]
        self.host = qdrant_config["host"]
        self.port = qdrant_config["port"]
        self.grpc_port = qdrant_config["grpc_port"]

        # 超时和重试配置（从配置文件读取，无则使用默认值）
        self.timeout = qdrant_config.get("timeout", 30)  # 单次请求超时（秒）
        self.max_retries = qdrant_config.get("max_retries", 3)  # 最大重试次数
        self.retry_delay = qdrant_config.get("retry_delay", 1)  # 重试延迟（秒）

        # Embedding 配置
        embedding_config = memory_config["embedding"]
        self.dimension = embedding_config["dimension"]

        # Retrieval 配置
        retrieval_config = memory_config["retrieval"]
        self.default_top_k = retrieval_config["default_top_k"]
        self.hybrid_alpha = retrieval_config["hybrid_alpha"]

        # 集合配置
        self.collections = collections_config["collections"]

        # 初始化 Qdrant 客户端
        check_compatibility = qdrant_config.get("check_compatibility", False)
        self._client = QdrantClient(
            host=self.host,
            port=self.port,
            grpc_port=self.grpc_port,
            timeout=self.timeout,  # 单次请求超时
            check_compatibility=check_compatibility,
        )

        # 缓存配置
        self._cache_size = cache_size
        self._default_batch_size = default_batch_size
        self._search_cache = _LRUCache(max_size=cache_size)

    @property
    def client(self) -> QdrantClient:
        """获取 Qdrant 客户端实例"""
        return self._client

    def get_collection_info(self, collection_name: str) -> dict:
        """获取集合信息

        Args:
            collection_name: 集合名称

        Returns:
            集合配置信息

        Raises:
            ValueError: 集合不存在
        """
        if collection_name not in self.collections:
            raise ValueError(f"Collection '{collection_name}' not found. Available: {list(self.collections.keys())}")

        return self.collections[collection_name]

    def _convert_search_hits(self, hits: list[Any]) -> list[dict]:
        """Normalize ScoredPoint / dict hits to wrapper result rows."""
        return [
            {
                "id": hit.id if hasattr(hit, "id") else hit["id"],
                "score": hit.score if hasattr(hit, "score") else hit["score"],
                "payload": hit.payload if hasattr(hit, "payload") else hit.get("payload", {}),
            }
            for hit in hits
        ]

    def _uses_query_points_api(self) -> bool:
        """True when the installed qdrant-client exposes query_points instead of search."""
        return not hasattr(type(self._client), "search")

    def _raw_vector_search(
        self,
        collection_name: str,
        query_vector: list[float],
        *,
        limit: int,
        query_filter: Optional[Filter] = None,
    ) -> list[Any]:
        """Call Qdrant vector search (query_points on 1.7+ client, legacy search otherwise)."""
        if self._uses_query_points_api():
            kwargs: dict[str, Any] = {
                "collection_name": collection_name,
                "query": query_vector,
                "limit": limit,
            }
            if query_filter is not None:
                kwargs["query_filter"] = query_filter
            response = self._client.query_points(**kwargs)
            return list(response.points)

        search_params: dict[str, Any] = {"limit": limit}
        if query_filter is not None:
            search_params["query_filter"] = query_filter
        return self._client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            **search_params,
        )

    def _validate_collection(self, collection_name: str) -> None:
        """验证集合是否存在

        Args:
            collection_name: 集合名称

        Raises:
            ValueError: 集合不存在
        """
        if collection_name not in self.collections:
            raise ValueError(f"Collection '{collection_name}' not found. Available: {list(self.collections.keys())}")

    @with_retry(max_retries=3, delay=1.0)
    def upsert(self, collection_name: str, points: list[dict]) -> None:
        """Upsert 向量点到集合

        Args:
            collection_name: 集合名称
            points: 点列表，每个点包含 id, vector, payload

        Raises:
            ValueError: 集合不存在或向量维度不匹配
        """
        self._validate_collection(collection_name)

        # 验证向量维度
        for point in points:
            if len(point["vector"]) != self.dimension:
                raise ValueError(
                    f"Vector dimension mismatch: expected {self.dimension}, got {len(point['vector'])}"
                )

        # 转换 points 格式

        qdrant_points = [
            PointStruct(
                id=point["id"],
                vector=point["vector"],
                payload=point.get("payload", {}),
            )
            for point in points
        ]

        self._client.upsert(collection_name=collection_name, points=qdrant_points)

        # 清除该集合的缓存
        self._search_cache.clear_collection(collection_name)

    def upsert_batch(self, collection_name: str, points: list[dict], batch_size: Optional[int] = None) -> None:
        """批量 upsert 向量点，分批提交

        Args:
            collection_name: 集合名称
            points: 点列表，每个点包含 id, vector, payload
            batch_size: 每批大小，默认使用 default_batch_size

        Raises:
            ValueError: 集合不存在或向量维度不匹配
        """
        self._validate_collection(collection_name)

        if batch_size is None:
            batch_size = self._default_batch_size

        # 验证向量维度
        for point in points:
            if len(point["vector"]) != self.dimension:
                raise ValueError(
                    f"Vector dimension mismatch: expected {self.dimension}, got {len(point['vector'])}"
                )

        # 转换 points 格式

        qdrant_points = [
            PointStruct(
                id=point["id"],
                vector=point["vector"],
                payload=point.get("payload", {}),
            )
            for point in points
        ]

        # 分批提交
        total = len(qdrant_points)
        for i in range(0, total, batch_size):
            batch = qdrant_points[i:i + batch_size]
            self._client.upsert(collection_name=collection_name, points=batch)

        # 清除该集合的缓存
        self._search_cache.clear_collection(collection_name)

    @with_retry(max_retries=3, delay=1.0)
    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        top_k: Optional[int] = None,
        query_filter: Optional[Filter] = None,
    ) -> list[dict]:
        """搜索最相似的向量

        Args:
            collection_name: 集合名称
            query_vector: 查询向量
            top_k: 返回数量，默认使用 default_top_k
            query_filter: 可选的过滤器

        Returns:
            搜索结果列表

        Raises:
            ValueError: 集合不存在或向量维度不匹配
        """
        self._validate_collection(collection_name)

        if len(query_vector) != self.dimension:
            raise ValueError(
                f"Query vector dimension mismatch: expected {self.dimension}, got {len(query_vector)}"
            )

        if top_k is None:
            top_k = self.default_top_k

        # 构建缓存键（使用JSON序列化float向量，因为float无法直接hash）
        filter_hash = _make_filter_hash(query_filter)
        vector_hash = hashlib.md5(json.dumps(list(query_vector), sort_keys=True).encode()).hexdigest()[:16]
        cache_key = f"{collection_name}:{vector_hash}:{top_k}:{filter_hash}"

        # 检查缓存
        cached_result = self._search_cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        results = self._raw_vector_search(
            collection_name,
            query_vector,
            limit=top_k,
            query_filter=query_filter,
        )

        # 转换结果
        converted_results = self._convert_search_hits(results)

        # 存入缓存
        self._search_cache.put(cache_key, converted_results)

        return converted_results

    @with_retry(max_retries=3, delay=1.0)
    def batch_search(
        self,
        collection_name: str,
        queries: list[dict],
        top_k: Optional[int] = None,
    ) -> list[list[dict]]:
        """批量搜索多个向量

        Args:
            collection_name: 集合名称
            queries: 查询列表，每个查询包含 query_vector 和可选的 filter
            top_k: 返回数量，默认使用 default_top_k

        Returns:
            每组查询的搜索结果列表
        """
        self._validate_collection(collection_name)

        if top_k is None:
            top_k = self.default_top_k

        results: list[list[dict]] = []

        for query in queries:
            query_vector = query["query_vector"]
            query_filter = query.get("filter")

            if len(query_vector) != self.dimension:
                raise ValueError(
                    f"Query vector dimension mismatch: expected {self.dimension}, got {len(query_vector)}"
                )

            # 构建缓存键（使用JSON序列化float向量，因为float无法直接hash）
            filter_hash = _make_filter_hash(query_filter)
            vector_hash = hashlib.md5(json.dumps(list(query_vector), sort_keys=True).encode()).hexdigest()[:16]
            cache_key = f"{collection_name}:{vector_hash}:{top_k}:{filter_hash}"

            # 检查缓存
            cached_result = self._search_cache.get(cache_key)
            if cached_result is not None:
                results.append(cached_result)
                continue

            search_results = self._raw_vector_search(
                collection_name,
                query_vector,
                limit=top_k,
                query_filter=query_filter,
            )

            # 转换结果
            converted_results = self._convert_search_hits(search_results)

            # 存入缓存
            self._search_cache.put(cache_key, converted_results)
            results.append(converted_results)

        return results

    def search_with_filter(
        self,
        collection_name: str,
        query_vector: list[float],
        must: Optional[dict] = None,
        must_not: Optional[dict] = None,
        top_k: Optional[int] = None,
    ) -> list[dict]:
        """使用过滤器搜索向量

        Args:
            collection_name: 集合名称
            query_vector: 查询向量
            must: 必须满足的条件 (field: value)
            must_not: 必须不满足的条件 (field: value)
            top_k: 返回数量

        Returns:
            搜索结果列表
        """
        conditions = []

        if must:
            for field, value in must.items():
                conditions.append(FieldCondition(key=field, match=MatchValue(value=value)))

        if must_not:
            for field, value in must_not.items():
                conditions.append(FieldCondition(key=field, match=MatchValue(value=value)))

        query_filter = Filter(must=conditions) if conditions else None

        return self.search(
            collection_name=collection_name,
            query_vector=query_vector,
            top_k=top_k,
            query_filter=query_filter,
        )

    def delete(self, collection_name: str, point_id: str) -> None:
        """删除向量

        Args:
            collection_name: 集合名称
            point_id: 点 ID

        Raises:
            ValueError: 集合不存在
        """
        self._validate_collection(collection_name)

        self._client.delete(
            collection_name=collection_name,
            points_selector=PointIdsList(points=[point_id]),
        )

        # 清除该集合的缓存
        self._search_cache.clear_collection(collection_name)

    def collection_exists(self, collection_name: str) -> bool:
        """检查集合是否存在

        Args:
            collection_name: 集合名称

        Returns:
            是否存在
        """
        return self._client.collection_exists(collection_name=collection_name)

    def create_collection(self, collection_name: str) -> None:
        """创建集合

        Args:
            collection_name: 集合名称

        Raises:
            ValueError: 集合类型未知
        """
        if collection_name not in self.collections:
            raise ValueError(f"Unknown collection type: {collection_name}. Available: {list(self.collections.keys())}")

        collection_info = self.collections[collection_name]

        self._client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=collection_info["vector_size"],
                distance=self.DISTANCE_MAP.get(collection_info["distance"], Distance.COSINE),
            ),
        )

    def close(self) -> None:
        """关闭客户端连接"""
        self._client.close()

    def clear_cache(self, collection_name: Optional[str] = None) -> None:
        """清除搜索缓存

        Args:
            collection_name: 如果指定，只清除该集合的缓存；否则清除所有缓存
        """
        if collection_name is not None:
            self._search_cache.clear_collection(collection_name)
        else:
            self._search_cache.clear()

    def get_cache_stats(self) -> dict:
        """获取缓存统计信息

        Returns:
            缓存统计字典，包含 size 和 max_size
        """
        return {
            "size": len(self._search_cache),
            "max_size": self._cache_size,
        }

    async def search_async(
        self,
        collection_name: str,
        query_vector: list[float],
        top_k: Optional[int] = None,
        query_filter: Optional[Filter] = None,
    ) -> list[dict]:
        """Phase 14.0 T2: async 包装 sync search(), 释放 FastAPI event loop.

        主路径仍 sync `search()` (6+ callers 0 改); async 仅供 FastAPI endpoint 用。
        用 `asyncio.to_thread()` 把 sync Qdrant 阻塞调用送到 thread pool。
        """
        return await asyncio.to_thread(
            self.search,
            collection_name,
            list(query_vector),
            top_k=top_k,
            query_filter=query_filter,
        )

    async def _raw_vector_search_async(
        self,
        collection_name: str,
        query_vector: list[float],
        *,
        limit: int = 10,
        query_filter: Optional[Filter] = None,
    ) -> list[Any]:
        """Phase 14.0 T2: async 包装 sync `_raw_vector_search()`. 同样 to_thread."""
        return await asyncio.to_thread(
            self._raw_vector_search,
            collection_name,
            list(query_vector),
            limit=limit,
            query_filter=query_filter,
        )
