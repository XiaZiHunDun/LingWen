"""查询引擎模块

提供混合检索、角色状态查询、关系网络查询和一致性检查功能。
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import time

from memory_system.config import load_yaml
from memory_system.vector.embedder import Embedder
from memory_system.state.character_tracker import CharacterTracker
from memory_system.state.plot_thread_tracker import PlotThreadTracker
from memory_system.state.timeline_manager import TimelineManager
from memory_system.state.fact_base import FactBase


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


class QueryEngine:
    """查询引擎

    负责：
    - 混合检索：向量 + 关键词 + 时间范围
    - 获取角色状态
    - 获取关系网络
    - 一致性检查

    使用 memory_config.yaml 中的 retrieval.default_top_k 和 retrieval.hybrid_alpha 配置。
    """

    MEMORY_CONFIG_PATH = "config/memory_config.yaml"

    def __init__(
        self,
        qdrant_wrapper,
        embedder: Embedder,
        character_tracker: Optional[CharacterTracker] = None,
        plot_thread_tracker: Optional[PlotThreadTracker] = None,
        timeline_manager: Optional[TimelineManager] = None,
        fact_base: Optional[FactBase] = None,
        enable_profiling: bool = False,
    ):
        """初始化查询引擎

        Args:
            qdrant_wrapper: QdrantClientWrapper 实例
            embedder: Embedder 实例
            character_tracker: CharacterTracker 实例（可选）
            plot_thread_tracker: PlotThreadTracker 实例（可选）
            timeline_manager: TimelineManager 实例（可选）
            fact_base: FactBase 实例（可选）
            enable_profiling: 是否启用性能监控（默认关闭）
        """
        self.qdrant_wrapper = qdrant_wrapper
        self.embedder = embedder

        # 性能监控
        self._profiler = PerformanceMonitor()
        if not enable_profiling:
            self._profiler.disable()

        # 从配置加载默认参数
        try:
            config = load_yaml(self.MEMORY_CONFIG_PATH)
            retrieval_config = config.get("retrieval", {})
            self.default_top_k = retrieval_config.get("default_top_k", 5)
            self.hybrid_alpha = retrieval_config.get("hybrid_alpha", 0.7)
        except Exception:
            # 配置加载失败时使用硬编码默认值
            self.default_top_k = 5
            self.hybrid_alpha = 0.7

        # 可选依赖，使用懒加载
        self._character_tracker = character_tracker
        self._plot_thread_tracker = plot_thread_tracker
        self._timeline_manager = timeline_manager
        self._fact_base = fact_base

    @property
    def character_tracker(self) -> Optional[CharacterTracker]:
        """获取角色追踪器（懒加载）"""
        return self._character_tracker

    @property
    def plot_thread_tracker(self) -> Optional[PlotThreadTracker]:
        """获取伏笔追踪器（懒加载）"""
        return self._plot_thread_tracker

    @property
    def timeline_manager(self) -> Optional[TimelineManager]:
        """获取时间线管理器（懒加载）"""
        return self._timeline_manager

    @property
    def fact_base(self) -> Optional[FactBase]:
        """获取事实库（懒加载）"""
        return self._fact_base

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标

        Returns:
            性能指标字典，包含：
            - total_queries: 总查询数
            - avg_latency_ms: 平均延迟（毫秒）
            - min_latency_ms: 最小延迟（毫秒）
            - max_latency_ms: 最大延迟（毫秒）
            - cache_hit_rate: 缓存命中率
            - cache_hits: 缓存命中次数
            - cache_misses: 缓存未命中次数
            - embedding_calls: 嵌入调用次数
            - avg_embedding_time_ms: 平均嵌入时间（毫秒）
            - total_embedding_time_ms: 总嵌入时间（毫秒）
        """
        return self._profiler.get_metrics()

    def hybrid_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """混合检索

        结合向量检索和关键词匹配，返回最相关的结果。

        Args:
            query: 查询文本
            filters: 过滤条件（如 {"character": "李逍遥", "chapter": 1}）
            top_k: 返回结果数量，默认使用 default_top_k

        Returns:
            搜索结果列表，每项包含 id, score, payload
        """
        if not query or not query.strip():
            return []

        if top_k is None:
            top_k = self.default_top_k

        # 生成查询向量（带性能监控）
        start_time = time.perf_counter()
        query_vectors = self.embedder.embed_texts([query])
        embedding_time = (time.perf_counter() - start_time) * 1000
        self._profiler.record_embedding(embedding_time)

        if not query_vectors:
            return []

        query_vector = query_vectors[0]

        # 执行向量搜索（带性能监控）
        start_time = time.perf_counter()
        search_results = self.qdrant_wrapper.search(
            collection_name="chapters_seg",
            query_vector=query_vector,
            top_k=top_k,
            query_filter=self._build_filter(filters) if filters else None,
        )
        search_time = (time.perf_counter() - start_time) * 1000
        self._profiler.record_query(search_time)

        return search_results

    def _build_filter(self, filters: Dict[str, Any]) -> Optional[Any]:
        """构建 Qdrant 过滤器

        Args:
            filters: 过滤条件字典

        Returns:
            Qdrant Filter 对象或 None
        """
        if not filters:
            return None

        from qdrant_client.models import Filter, FieldCondition, MatchValue

        conditions = []
        for field, value in filters.items():
            conditions.append(
                FieldCondition(key=field, match=MatchValue(value=value))
            )

        return Filter(must=conditions) if conditions else None

    def get_character_state(
        self, character: str, before_chapter: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """获取角色状态

        Args:
            character: 角色名称
            before_chapter: 可选，指定章节之前的状态

        Returns:
            角色状态字典，如果角色不存在则返回 None
        """
        if not self._character_tracker:
            return None

        state = self._character_tracker.get_character_state(character)

        if state is None:
            return None

        # 如果指定了 before_chapter，检查状态是否在该章节之前有效
        if before_chapter is not None:
            last_updated = state.get("last_updated_chapter")
            if last_updated is not None and last_updated > before_chapter:
                # 状态在指定章节之后，可能需要获取历史状态
                # 目前返回当前状态作为简化
                pass

        return state

    def get_relationship_network(
        self, character: str, depth: int = 1
    ) -> List[Dict[str, Any]]:
        """获取角色关系网络

        Args:
            character: 角色名称
            depth: 关系深度（目前仅支持 1）

        Returns:
            关系列表，每项包含 from_character, to_character, relationship_type, score
        """
        if not self.qdrant_wrapper:
            return []

        # 生成角色名称的向量
        query_vectors = self.embedder.embed_texts([character])
        if not query_vectors:
            return []

        query_vector = query_vectors[0]

        # 在 relationships 集合中搜索
        search_results = self.qdrant_wrapper.search(
            collection_name="relationships",
            query_vector=query_vector,
            top_k=20,
        )

        # 过滤出与该角色相关的关系
        relationships = []
        for result in search_results:
            payload = result.get("payload", {})
            from_char = payload.get("from_character", "")
            to_char = payload.get("to_character", "")

            if from_char == character or to_char == character:
                relationships.append({
                    "from_character": from_char,
                    "to_character": to_char,
                    "relationship_type": payload.get("relationship_type", "unknown"),
                    "score": result.get("score", 0.0),
                    "id": result.get("id"),
                })

        return relationships

    def check_consistency(
        self, chapter_content: str, chapter: Optional[int] = None
    ) -> Dict[str, Any]:
        """一致性检查

        检查章节内容与已知角色状态、时间线、伏笔的一致性。

        Args:
            chapter_content: 章节内容
            chapter: 章节号（可选）

        Returns:
            一致性检查结果，包含：
            - is_consistent: bool - 是否一致
            - consistency_score: float - 一致性分数 (0.0 - 1.0)
            - issues: List[Dict] - 发现的问题列表
        """
        issues = []
        consistency_score = 1.0

        # 1. 检查角色状态一致性
        if self._character_tracker and chapter_content:
            character_issues = self._check_character_consistency(chapter_content)
            issues.extend(character_issues)

        # 2. 检查事实一致性
        if self._fact_base and chapter_content:
            fact_issues = self._check_fact_consistency(chapter_content)
            issues.extend(fact_issues)

        # 3. 检查伏笔一致性
        if self._plot_thread_tracker and chapter:
            plot_issues = self._check_plot_thread_consistency(chapter_content, chapter)
            issues.extend(plot_issues)

        # 4. 检查时间线一致性
        if self._timeline_manager and chapter:
            timeline_issues = self._check_timeline_consistency(chapter_content, chapter)
            issues.extend(timeline_issues)

        # 计算一致性分数
        if issues:
            # 每个问题降低分数，严重问题降低更多
            for issue in issues:
                severity = issue.get("severity", "medium")
                if severity == "critical":
                    consistency_score -= 0.3
                elif severity == "high":
                    consistency_score -= 0.2
                elif severity == "medium":
                    consistency_score -= 0.1
                else:
                    consistency_score -= 0.05

            consistency_score = max(0.0, consistency_score)

        return {
            "is_consistent": len([i for i in issues if i.get("severity") in ("critical", "high")]) == 0,
            "consistency_score": consistency_score,
            "issues": issues,
        }

    def _check_character_consistency(
        self, chapter_content: str
    ) -> List[Dict[str, Any]]:
        """检查角色状态一致性

        Args:
            chapter_content: 章节内容

        Returns:
            发现的问题列表
        """
        issues = []

        if not self._character_tracker:
            return issues

        all_characters = self._character_tracker.get_all_characters()

        for char_name, char_state in all_characters.items():
            # 检查角色名称是否在内容中出现
            if char_name in chapter_content:
                # 检查状态一致性
                current_location = char_state.get("current_location", "")
                alive = char_state.get("alive", True)

                # 如果角色已死亡，警告不要在内容中描述其活动
                if not alive and self._is_describing_activity(chapter_content, char_name):
                    issues.append({
                        "type": "character_state_conflict",
                        "severity": "high",
                        "character": char_name,
                        "message": f"角色 '{char_name}' 已经死亡，不应描述其活动",
                        "current_state": char_state,
                    })

                # 检查位置一致性（如果能确定位置的话）
                # 这需要更复杂的内容解析，暂时简化处理

        return issues

    def _check_fact_consistency(
        self, chapter_content: str
    ) -> List[Dict[str, Any]]:
        """检查事实一致性

        Args:
            chapter_content: 章节内容

        Returns:
            发现的问题列表
        """
        issues = []

        if not self._fact_base:
            return issues

        all_facts = self._fact_base.get_all_facts()

        for fact_id, fact in all_facts.items():
            content = fact.get("content", "")
            verified = fact.get("verified", False)

            # 只检查已验证的事实
            if not verified:
                continue

            # 检查内容中是否与已知事实矛盾
            # 这需要更复杂的 NLP 处理，暂时简化处理
            # 实际实现应该使用 LLM 来判断一致性

        return issues

    def _check_plot_thread_consistency(
        self, chapter_content: str, chapter: int
    ) -> List[Dict[str, Any]]:
        """检查伏笔一致性

        Args:
            chapter_content: 章节内容
            chapter: 章节号

        Returns:
            发现的问题列表
        """
        issues = []

        if not self._plot_thread_tracker:
            return issues

        pending_foreshadows = self._plot_thread_tracker.get_pending_foreshadows()

        for fp_id, fp_data in pending_foreshadows.items():
            planted_chapter = fp_data.get("planted_chapter", 0)

            # 检查伏笔是否在引入之前被提及
            if chapter < planted_chapter:
                # 伏笔尚未引入，查找是否被提及
                if self._contains_foreshadow_reference(chapter_content, fp_data):
                    issues.append({
                        "type": "foreshadow_reference_before_planting",
                        "severity": "medium",
                        "foreshadow_id": fp_id,
                        "message": f"伏笔 '{fp_data.get('title', fp_id)}' 在引入之前被提及",
                        "current_chapter": chapter,
                        "planted_chapter": planted_chapter,
                    })

        return issues

    def _check_timeline_consistency(
        self, chapter_content: str, chapter: int
    ) -> List[Dict[str, Any]]:
        """检查时间线一致性

        Args:
            chapter_content: 章节内容
            chapter: 章节号

        Returns:
            发现的问题列表
        """
        issues = []

        if not self._timeline_manager:
            return issues

        # 获取本章事件
        chapter_events = self._timeline_manager.get_events_by_chapter(chapter)

        # 检查时间顺序是否合理
        # 这需要解析内容中的时间描述，暂时简化处理

        return issues

    def _is_describing_activity(self, content: str, char_name: str) -> bool:
        """检查内容是否在描述角色的活动

        Args:
            content: 章节内容
            char_name: 角色名称

        Returns:
            是否在描述活动
        """
        # 简化的活动检测
        activity_indicators = ["在", "去", "来", "走", "跑", "说", "看", "想"]
        char_appearances = content.count(char_name)

        if char_appearances > 0:
            # 检查角色周围是否有活动指示词
            for indicator in activity_indicators:
                pattern = f"{char_name}{indicator}"
                if pattern in content:
                    return True

        return False

    def _contains_foreshadow_reference(
        self, content: str, foreshadow_data: Dict[str, Any]
    ) -> bool:
        """检查内容是否包含伏笔引用

        Args:
            content: 章节内容
            foreshadow_data: 伏笔数据

        Returns:
            是否包含引用
        """
        title = foreshadow_data.get("title", "")
        description = foreshadow_data.get("description", "")

        if title and title in content:
            return True

        if description:
            # 检查关键词
            keywords = description.split()[:3]  # 取前三个词
            for keyword in keywords:
                if len(keyword) > 2 and keyword in content:
                    return True

        return False

    def query_foreshadows(
        self,
        query: str,
        status: Optional[str] = None,
        chapter_range: Optional[tuple] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """查询伏笔

        Args:
            query: 查询文本，用于语义搜索
            status: 可选，按状态过滤（pending/in_progress/recycled/invalid）
            chapter_range: 可选，按章节范围过滤 (min_chapter, max_chapter)
            top_k: 返回结果数量，默认5

        Returns:
            伏笔列表，包含状态、描述、提及章节等信息
        """
        start_time = time.perf_counter()

        if not self._plot_thread_tracker:
            return []

        # 获取所有伏笔
        all_foreshadows = self._plot_thread_tracker.get_all_foreshadows()

        # 按状态过滤
        if status:
            all_foreshadows = {
                fp_id: fp_data
                for fp_id, fp_data in all_foreshadows.items()
                if fp_data.get("status") == status
            }

        # 按章节范围过滤
        if chapter_range:
            min_ch, max_ch = chapter_range
            all_foreshadows = {
                fp_id: fp_data
                for fp_id, fp_data in all_foreshadows.items()
                if self._matches_chapter_range(fp_data, min_ch, max_ch)
            }

        # 如果没有查询文本，返回过滤后的结果（按提及章节排序）
        if not query or not query.strip():
            results = list(all_foreshadows.values())
            # 按 planted_chapter 降序排列（越新的伏笔越靠前）
            results.sort(key=lambda x: x.get("planted_chapter", 0), reverse=True)
            elapsed = (time.perf_counter() - start_time) * 1000
            self._profiler.record_query(elapsed)
            return results[:top_k]

        # 语义搜索：使用嵌入向量匹配
        try:
            query_start = time.perf_counter()
            query_vectors = self.embedder.embed_texts([query])
            query_time = (time.perf_counter() - query_start) * 1000
            self._profiler.record_embedding(query_time)

            if not query_vectors:
                return list(all_foreshadows.values())[:top_k]

            query_vector = query_vectors[0]

            # 对每个伏笔计算相似度
            scored_results = []
            for fp_id, fp_data in all_foreshadows.items():
                # 构建伏笔文本用于嵌入
                fp_text = self._build_foreshadow_text(fp_data)
                fp_start = time.perf_counter()
                fp_vectors = self.embedder.embed_texts([fp_text])
                fp_time = (time.perf_counter() - fp_start) * 1000
                self._profiler.record_embedding(fp_time)

                if fp_vectors:
                    # 计算余弦相似度
                    similarity = self._cosine_similarity(query_vector, fp_vectors[0])
                    scored_results.append({
                        "fp_id": fp_id,
                        "similarity": similarity,
                        **fp_data
                    })

            # 按相似度降序排列
            scored_results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
            elapsed = (time.perf_counter() - start_time) * 1000
            self._profiler.record_query(elapsed)
            return scored_results[:top_k]

        except Exception:
            # 嵌入失败时返回过滤后的结果
            elapsed = (time.perf_counter() - start_time) * 1000
            self._profiler.record_query(elapsed)
            return list(all_foreshadows.values())[:top_k]

    def _matches_chapter_range(
        self, fp_data: Dict[str, Any], min_ch: int, max_ch: int
    ) -> bool:
        """检查伏笔是否在章节范围内"""
        planted_chapter = fp_data.get("planted_chapter", 0)
        expected_recycle = fp_data.get("expected_recycle_chapter", 0)
        mentions = fp_data.get("mentions", [])

        # 检查引入章节
        if min_ch <= planted_chapter <= max_ch:
            return True
        # 检查预期回收章节
        if min_ch <= expected_recycle <= max_ch:
            return True
        # 检查提及章节
        for m in mentions:
            if min_ch <= m <= max_ch:
                return True

        return False

    def _build_foreshadow_text(self, fp_data: Dict[str, Any]) -> str:
        """构建伏笔文本用于嵌入"""
        parts = []
        if fp_data.get("title"):
            parts.append(fp_data["title"])
        if fp_data.get("description"):
            parts.append(fp_data["description"])
        return " ".join(parts)

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2) or len(vec1) == 0:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)