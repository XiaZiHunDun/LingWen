# novel-factory/agent_system/agent_factory.py
"""MasterController 工厂层

从 MasterControllerConfig / 显式依赖构造所有子模块实例。
不读环境变量（那是 agent_config 的职责），不存储状态（那是 controller 的职责）。

Why: 把"如何实例化"集中到一处，使 MasterController.__init__ 变为纯组合逻辑。
每个 build_X 函数都接受最少必要输入，可以独立测试。
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple, Optional

from ..ai_service.router import AIRouter
from ..state.state_manager import StateManager
from .agent_config import MasterControllerConfig
from .agents.auditor.tools import AuditorTools
from .agents.character_designer.tools import CharacterDesignerTools
from .agents.content_writer.tools import ContentWriterTools
from .agents.outline_master.tools import OutlineMasterTools
from .agents.polisher.tools import PolisherTools
from .registry.skill_registry import SkillRegistry
from .social_engine.conflict_alert import ConflictAlert
from .social_engine.event_effect_calculator import EventEffectCalculator
from .social_engine.relationship_tracker import RelationshipTracker
from .social_engine.writing_suggestion import WritingSuggestion
from .core.context_builder import ContextBuilder
from .orchestration.task_orchestrator import TaskOrchestrator


class AgentToolsBundle(NamedTuple):
    """5 个核心 Agent 工具的打包"""
    outline_master: OutlineMasterTools
    character_designer: CharacterDesignerTools
    content_writer: ContentWriterTools
    auditor: AuditorTools
    polisher: PolisherTools


class SocialEngineBundle(NamedTuple):
    """5 个社交引擎组件的打包"""
    relationship_tracker: RelationshipTracker
    event_calculator: EventEffectCalculator
    conflict_alert: ConflictAlert
    writing_suggestion: WritingSuggestion
    context_builder: ContextBuilder


def build_router(config: MasterControllerConfig) -> AIRouter:
    """从配置构造 AIRouter

    使用 config.primary_provider 作为主 provider，config.providers 提供凭据。
    """
    return AIRouter(
        config=config.providers,
        primary_provider=config.primary_provider,
        enable_failover=config.enable_failover,
    )


def build_orchestrator() -> TaskOrchestrator:
    """构造 TaskOrchestrator（任务编排器）

    使用默认 StateManager（SQLite 后端）。
    """
    state_manager = StateManager()
    return TaskOrchestrator(state_manager=state_manager)


def build_skill_registry() -> SkillRegistry:
    """构造 SkillRegistry（角色池技能注册表）"""
    return SkillRegistry()


def build_agent_tools(router: AIRouter) -> AgentToolsBundle:
    """构造 5 个核心 Agent 工具

    4 个工具无依赖，content_writer 和 auditor 接收 AIRouter 用于 LLM 调用。
    """
    return AgentToolsBundle(
        outline_master=OutlineMasterTools(),
        character_designer=CharacterDesignerTools(),
        content_writer=ContentWriterTools(router=router),
        auditor=AuditorTools(router=router),
        polisher=PolisherTools(),
    )


def build_social_engine(state_dir: str) -> SocialEngineBundle:
    """构造 5 个社交引擎组件

    state_dir 是 agent_system 根目录；relationship_tracker 的 state_file
    路径基于此派生（state_dir/social_engine/relationship_network.json）。
    """
    relationship_state_file = str(Path(state_dir) / "social_engine" / "relationship_network.json")
    return SocialEngineBundle(
        relationship_tracker=RelationshipTracker(relationship_state_file),
        event_calculator=EventEffectCalculator(),
        conflict_alert=ConflictAlert(),
        writing_suggestion=WritingSuggestion(),
        context_builder=ContextBuilder(),
    )
