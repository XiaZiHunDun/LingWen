"""记忆系统统一入口模块

MemoryGateway 是记忆系统的统一入口，整合所有组件，提供：
- 自动推送：章节开始时推送相关上下文
- 主动查询：作家/审核/主控手动输入查询
- 状态管理：角色状态更新、伏笔管理
"""
from typing import Any, Dict, List, Optional

from infra.memory_system.gateway.push_engine import PushEngine
from infra.memory_system.gateway.query_engine import QueryEngine
from infra.memory_system.state.character_tracker import CharacterTracker
from infra.memory_system.state.fact_base import FactBase
from infra.memory_system.state.plot_thread_tracker import PlotThreadTracker
from infra.memory_system.state.timeline_manager import TimelineManager
from infra.memory_system.vector.embedder import Embedder
from infra.memory_system.vector.qdrant_client import QdrantClientWrapper


class MemoryGateway:
    """记忆系统统一入口

    整合 QueryEngine、PushEngine 和所有状态管理组件，提供统一的记忆系统接口。

    使用方式：
        gateway = MemoryGateway(
            qdrant_wrapper=qdrant_wrapper,
            embedder=embedder,
            character_tracker=character_tracker,
            plot_thread_tracker=plot_thread_tracker,
            timeline_manager=timeline_manager,
            fact_base=fact_base,
        )

        # 自动推送上下文（作家写新章节时）
        context = gateway.auto_push_context(chapter_num=5)

        # 主动查询
        results = gateway.query("李逍遥在哪里", scope="character")

        # 更新角色状态
        gateway.update_character_state("李逍遥", {"current_location": "王宫"})

        # 登记伏笔
        gateway.plant_foreshadow("fp_001", {"title": "神秘剑客", "planted_chapter": 3})

        # 更新伏笔状态
        gateway.update_foreshadow("fp_001", chapter=10, event_type="activate")
    """

    def __init__(
        self,
        qdrant_wrapper: QdrantClientWrapper,
        embedder: Embedder,
        character_tracker: Optional[CharacterTracker] = None,
        plot_thread_tracker: Optional[PlotThreadTracker] = None,
        timeline_manager: Optional[TimelineManager] = None,
        fact_base: Optional[FactBase] = None,
        query_engine: Optional[QueryEngine] = None,
        push_engine: Optional[PushEngine] = None,
    ):
        """初始化 MemoryGateway

        Args:
            qdrant_wrapper: QdrantClientWrapper 实例
            embedder: Embedder 实例
            character_tracker: CharacterTracker 实例（可选）
            plot_thread_tracker: PlotThreadTracker 实例（可选）
            timeline_manager: TimelineManager 实例（可选）
            fact_base: FactBase 实例（可选）
            query_engine: QueryEngine 实例（可选，如果不提供会自动创建）
            push_engine: PushEngine 实例（可选，如果不提供会自动创建）
        """
        self.qdrant_wrapper = qdrant_wrapper
        self.embedder = embedder

        # 状态管理组件
        self.character_tracker = character_tracker
        self.plot_thread_tracker = plot_thread_tracker
        self.timeline_manager = timeline_manager
        self.fact_base = fact_base

        # 如果没有提供 QueryEngine，自动创建一个
        if query_engine is None:
            self.query_engine = QueryEngine(
                qdrant_wrapper=qdrant_wrapper,
                embedder=embedder,
                character_tracker=character_tracker,
                plot_thread_tracker=plot_thread_tracker,
                timeline_manager=timeline_manager,
                fact_base=fact_base,
            )
        else:
            self.query_engine = query_engine

        # 如果没有提供 PushEngine，自动创建一个
        if push_engine is None:
            self.push_engine = PushEngine(
                query_engine=self.query_engine,
                character_tracker=character_tracker,
                plot_thread_tracker=plot_thread_tracker,
                timeline_manager=timeline_manager,
            )
        else:
            self.push_engine = push_engine

    def auto_push_context(self, chapter_num: int) -> Dict[str, Any]:
        """自动推送上下文

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
        if self.push_engine is None:
            # 如果没有 PushEngine，返回空上下文
            return {
                "chapter": chapter_num,
                "character_states": {},
                "pending_foreshadows": {},
                "recent_events": [],
                "related_segments": [],
            }

        return self.push_engine.push_context(chapter_num=chapter_num)

    def query(
        self,
        query: str,
        scope: Optional[str] = "all",
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """主动查询

        Args:
            query: 查询字符串
            scope: 查询范围，可选值：
                - "character": 角色范围
                - "chapter": 章节范围
                - "relationship": 关系范围
                - "all": 全局搜索（默认）
            filters: 过滤条件（可选）
            top_k: 返回结果数量（可选）

        Returns:
            搜索结果列表
        """
        if not query or not query.strip():
            return []

        if self.query_engine is None:
            return []

        # 根据 scope 添加过滤条件
        query_filters = filters.copy() if filters else {}
        if scope == "character":
            query_filters["type"] = "character"
        elif scope == "chapter":
            # 章节范围查询 - 不过滤类型
            pass
        elif scope == "relationship":
            query_filters["type"] = "relationship"
        # scope 为 None 或其他值时不过滤

        # 执行混合搜索
        results = self.query_engine.hybrid_search(
            query=query,
            filters=query_filters,
            top_k=top_k,
        )

        return results

    def update_character_state(self, character: str, state: Dict[str, Any]) -> None:
        """更新角色状态

        Args:
            character: 角色名称
            state: 状态字典，包含以下字段（均为可选）：
                - current_location: str - 当前位置
                - current_form: str - 当前形态
                - alive: bool - 是否存活
                - last_updated_chapter: int - 最后更新章节
                - emotion_state: str - 情绪状态
        """
        if self.character_tracker is None:
            return

        self.character_tracker.update_character_state(character, state)

    def get_character_state(self, character: str) -> Optional[Dict[str, Any]]:
        """获取角色状态

        Args:
            character: 角色名称

        Returns:
            角色状态字典，如果角色不存在则返回 None
        """
        if self.character_tracker is None:
            return None

        return self.character_tracker.get_character_state(character)

    def get_all_characters(self) -> Dict[str, Dict[str, Any]]:
        """获取所有角色状态

        Returns:
            所有角色状态字典，键为角色名称，值为角色状态
        """
        if self.character_tracker is None:
            return {}

        return self.character_tracker.get_all_characters()

    def plant_foreshadow(self, fp_id: str, metadata: Dict[str, Any]) -> None:
        """登记伏笔

        Args:
            fp_id: 伏笔唯一标识
            metadata: 伏笔元数据，包含以下字段（均为可选）：
                - title: str - 伏笔标题
                - description: str - 伏笔描述
                - planted_chapter: int - 引入章节
                - expected_recycle_chapter: int - 预期回收章节
                - status: str - 状态 (pending/in_progress/recycled/invalid)
                - mentions: List[int] - 提及章节列表
        """
        if self.plot_thread_tracker is None:
            return

        self.plot_thread_tracker.plant_foreshadow(fp_id, metadata)

    def update_foreshadow(
        self,
        fp_id: str,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        chapter: Optional[int] = None
    ) -> None:
        """更新伏笔状态

        Args:
            fp_id: 伏笔唯一标识
            event_type: 事件类型 (plant/activate/recycle/invalidate)
                - plant: 登记新伏笔，需要 metadata（title, description, planted_chapter, expected_recycle_chapter）
                - activate: 伏笔开始被提及，设置状态为 in_progress
                - recycle: 伏笔已回收，设置状态为 recycled
                - invalidate: 伏笔失效，设置状态为 invalid
            metadata: 伏笔元数据（用于 plant 事件）
            chapter: 事件发生章节（用于其他事件类型）
        """
        if self.plot_thread_tracker is None:
            return

        # 验证事件类型
        valid_event_types = {"plant", "activate", "recycle", "invalidate"}
        if event_type not in valid_event_types:
            return

        if event_type == "plant":
            if metadata:
                self.plot_thread_tracker.plant_foreshadow(fp_id, metadata)
        else:
            if chapter is not None:
                self.plot_thread_tracker.update_foreshadow(fp_id, chapter, event_type)

    def get_pending_foreshadows(self) -> Dict[str, Dict[str, Any]]:
        """获取待回收伏笔

        Returns:
            待回收伏笔字典，键为伏笔ID，值为伏笔信息
        """
        if self.plot_thread_tracker is None:
            return {}

        return self.plot_thread_tracker.get_pending_foreshadows()

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
        if self.query_engine is None:
            return {
                "is_consistent": True,
                "consistency_score": 1.0,
                "issues": [],
            }

        return self.query_engine.check_consistency(chapter_content, chapter)

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
        if self.query_engine is None:
            return []

        return self.query_engine.get_relationship_network(character, depth)
