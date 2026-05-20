"""自动推送引擎模块

当作家开始写新章节时，自动推送相关上下文：
- 角色状态摘要
- 待回收伏笔摘要
- 相关历史事件
- 向量检索的相关段落
"""
from typing import Any, Dict, List, Optional

from infra.memory_system.gateway.query_engine import QueryEngine
from infra.memory_system.state.character_tracker import CharacterTracker
from infra.memory_system.state.plot_thread_tracker import PlotThreadTracker
from infra.memory_system.state.timeline_manager import TimelineManager


class PushEngine:
    """自动推送引擎

    负责在作家开始写新章节时，自动推送相关上下文信息。

    使用方式：
        push_engine = PushEngine(
            query_engine=query_engine,
            character_tracker=character_tracker,
            plot_thread_tracker=plot_thread_tracker,
            timeline_manager=timeline_manager,
        )

        # 当作家开始写第5章时
        context = push_engine.push_context(chapter_num=5)
        # -> 返回完整的上下文字典
    """

    def __init__(
        self,
        query_engine: QueryEngine,
        character_tracker: Optional[CharacterTracker] = None,
        plot_thread_tracker: Optional[PlotThreadTracker] = None,
        timeline_manager: Optional[TimelineManager] = None,
    ):
        """初始化推送引擎

        Args:
            query_engine: QueryEngine 实例，用于向量检索
            character_tracker: CharacterTracker 实例（可选）
            plot_thread_tracker: PlotThreadTracker 实例（可选）
            timeline_manager: TimelineManager 实例（可选）
        """
        self.query_engine = query_engine
        self.character_tracker = character_tracker
        self.plot_thread_tracker = plot_thread_tracker
        self.timeline_manager = timeline_manager

    def push_context(self, chapter_num: int) -> Dict[str, Any]:
        """推送当前章节相关上下文

        当作家开始写新章节时调用，汇总所有相关信息。

        Args:
            chapter_num: 当前章节号

        Returns:
            包含以下键的上下文字典：
            - chapter: int - 章节号
            - character_states: Dict - 角色状态摘要
            - pending_foreshadows: Dict - 待回收伏笔摘要
            - recent_events: List - 最近事件列表
            - related_segments: List - 向量检索相关的段落
        """
        # 获取角色状态
        character_states = self.get_character_states()

        # 获取待回收伏笔
        pending_foreshadows = self.get_pending_foreshadows()

        # 获取最近事件
        recent_events = self.get_recent_events(count=5)

        # 获取当前章节的事件
        chapter_events = []
        if self.timeline_manager:
            chapter_events = self.timeline_manager.get_events_by_chapter(chapter_num)

        # 获取向量检索相关的段落
        related_segments = self._get_related_segments(chapter_num)

        return {
            "chapter": chapter_num,
            "character_states": character_states,
            "pending_foreshadows": pending_foreshadows,
            "recent_events": recent_events,
            "chapter_events": chapter_events,
            "related_segments": related_segments,
        }

    def get_character_states(self) -> Dict[str, Dict[str, Any]]:
        """获取所有角色状态摘要

        Returns:
            角色状态字典，键为角色名称，值为角色状态
        """
        if not self.character_tracker:
            return {}

        return self.character_tracker.get_all_characters()

    def get_pending_foreshadows(self) -> Dict[str, Dict[str, Any]]:
        """获取待回收伏笔摘要

        Returns:
            待回收伏笔字典，键为伏笔ID，值为伏笔信息
            只包含 pending 和 in_progress 状态的伏笔
        """
        if not self.plot_thread_tracker:
            return {}

        return self.plot_thread_tracker.get_pending_foreshadows()

    def get_recent_events(self, count: int = 5) -> List[Dict[str, Any]]:
        """获取最近事件

        Args:
            count: 返回的事件数量，默认 5

        Returns:
            最近事件列表，按时间倒序排列
        """
        if not self.timeline_manager:
            return []

        all_events = self.timeline_manager.get_all_events()

        if not all_events:
            return []

        # 按时间戳倒序排序
        sorted_events = sorted(
            all_events,
            key=lambda e: e.get("timestamp", ""),
            reverse=True,
        )

        return sorted_events[:count]

    def _get_related_segments(self, chapter_num: int) -> List[Dict[str, Any]]:
        """获取与当前章节相关的段落

        通过向量检索获取与当前章节相关的内容片段。

        Args:
            chapter_num: 当前章节号

        Returns:
            相关的段落列表
        """
        if not self.query_engine:
            return []

        # 构建查询语句
        query = f"第{chapter_num}章 相关内容"

        try:
            # 执行混合搜索
            results = self.query_engine.hybrid_search(
                query=query,
                filters={"chapter": chapter_num},
                top_k=5,
            )
            return results
        except Exception:
            # 检索失败时返回空列表
            return []
