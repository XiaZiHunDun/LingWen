"""查询引擎辅助类

提供查询构建、混合搜索和调试工具。
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import time


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    total_queries: int = 0
    total_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    max_latency_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    embedding_time_ms: float = 0.0
    embedding_calls: int = 0


class PerformanceMonitor:
    """性能监控器

    收集和统计查询性能指标，包括：
    - 查询延迟统计（平均、最小、最大）
    - 缓存命中率
    - 嵌入生成时间
    """

    def __init__(self) -> None:
        self._metrics = PerformanceMetrics()
        self._enabled: bool = True

    def enable(self) -> None:
        """启用性能监控"""
        self._enabled = True

    def disable(self) -> None:
        """禁用性能监控"""
        self._enabled = False

    def record_query(self, latency_ms: float) -> None:
        """记录查询延迟

        Args:
            latency_ms: 查询延迟（毫秒）
        """
        if not self._enabled:
            return
        self._metrics.total_queries += 1
        self._metrics.total_latency_ms += latency_ms
        self._metrics.min_latency_ms = min(self._metrics.min_latency_ms, latency_ms)
        self._metrics.max_latency_ms = max(self._metrics.max_latency_ms, latency_ms)

    def record_cache_hit(self) -> None:
        """记录缓存命中"""
        if not self._enabled:
            return
        self._metrics.cache_hits += 1

    def record_cache_miss(self) -> None:
        """记录缓存未命中"""
        if not self._enabled:
            return
        self._metrics.cache_misses += 1

    def record_embedding(self, time_ms: float) -> None:
        """记录嵌入生成时间

        Args:
            time_ms: 嵌入生成时间（毫秒）
        """
        if not self._enabled:
            return
        self._metrics.embedding_time_ms += time_ms
        self._metrics.embedding_calls += 1

    def get_metrics(self) -> Dict[str, Any]:
        """获取当前性能统计

        Returns:
            性能指标字典
        """
        avg_latency = (
            self._metrics.total_latency_ms / self._metrics.total_queries
            if self._metrics.total_queries > 0
            else 0.0
        )
        cache_total = self._metrics.cache_hits + self._metrics.cache_misses
        cache_hit_rate = (
            self._metrics.cache_hits / cache_total if cache_total > 0 else 0.0
        )
        avg_embedding_time = (
            self._metrics.embedding_time_ms / self._metrics.embedding_calls
            if self._metrics.embedding_calls > 0
            else 0.0
        )

        return {
            "total_queries": self._metrics.total_queries,
            "avg_latency_ms": round(avg_latency, 3),
            "min_latency_ms": round(
                self._metrics.min_latency_ms if self._metrics.min_latency_ms != float('inf') else 0.0, 3
            ),
            "max_latency_ms": round(self._metrics.max_latency_ms, 3),
            "cache_hit_rate": round(cache_hit_rate, 3),
            "cache_hits": self._metrics.cache_hits,
            "cache_misses": self._metrics.cache_misses,
            "embedding_calls": self._metrics.embedding_calls,
            "avg_embedding_time_ms": round(avg_embedding_time, 3),
            "total_embedding_time_ms": round(self._metrics.embedding_time_ms, 3),
        }

    def reset(self) -> None:
        """重置所有性能统计"""
        self._metrics = PerformanceMetrics()

    @property
    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self._enabled


class QueryBuilder:
    """查询构建器

    用于构建复杂的查询条件，支持过滤、排序等。
    """

    def __init__(self) -> None:
        self._filters: Dict[str, Any] = {}
        self._top_k: int = 5
        self._collection: str = "chapters_seg"

    def set_filter(self, field: str, value: Any) -> "QueryBuilder":
        """设置过滤条件"""
        self._filters[field] = value
        return self

    def set_top_k(self, top_k: int) -> "QueryBuilder":
        """设置返回结果数量"""
        self._top_k = top_k
        return self

    def set_collection(self, collection: str) -> "QueryBuilder":
        """设置搜索集合"""
        self._collection = collection
        return self

    def build(self) -> Tuple[str, Dict[str, Any], int]:
        """构建查询参数"""
        return self._collection, self._filters, self._top_k


class HybridSearch:
    """混合搜索器

    支持向量搜索和关键词搜索的混合检索。
    """

    def __init__(self, embedder: Any, qdrant_wrapper: Any) -> None:
        self.embedder = embedder
        self.qdrant_wrapper = qdrant_wrapper

    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        collection: str = "chapters_seg"
    ) -> List[Dict[str, Any]]:
        """执行混合搜索

        Args:
            query: 查询文本
            filters: 过滤条件
            top_k: 返回结果数量
            collection: 集合名称

        Returns:
            搜索结果列表
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        # 生成查询向量
        query_vectors = self.embedder.embed_texts([query])
        if not query_vectors:
            return []

        query_vector = query_vectors[0]

        # 构建过滤器
        conditions = []
        if filters:
            for field, value in filters.items():
                conditions.append(
                    FieldCondition(key=field, match=MatchValue(value=value))
                )
        qdrant_filter = Filter(must=conditions) if conditions else None

        # 执行搜索
        results = self.qdrant_wrapper.search(
            collection_name=collection,
            query_vector=query_vector,
            top_k=top_k,
            query_filter=qdrant_filter,
        )

        return results


class ScoreDebugger:
    """评分调试器

    用于分析和调试相似度评分。
    """

    def __init__(self) -> None:
        self._debug_info: List[Dict[str, Any]] = []

    def record_score(
        self,
        query: str,
        result_id: str,
        score: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录评分详情

        Args:
            query: 查询文本
            result_id: 结果ID
            score: 相似度分数
            metadata: 附加元数据
        """
        self._debug_info.append({
            "query": query,
            "result_id": result_id,
            "score": score,
            "metadata": metadata or {}
        })

    def get_debug_info(self) -> List[Dict[str, Any]]:
        """获取调试信息"""
        return self._debug_info

    def clear(self) -> None:
        """清空调试信息"""
        self._debug_info = []

    def get_top_scores(self, n: int = 10) -> List[Dict[str, Any]]:
        """获取最高分数的结果"""
        sorted_results = sorted(
            self._debug_info,
            key=lambda x: x["score"],
            reverse=True
        )
        return sorted_results[:n]