"""Tests for agent_factory module.

Locks down:
- Each build_X function returns the expected type
- Bundles contain the right component types
- build_router respects primary_provider from config
- build_social_engine derives relationship_state_file from state_dir
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from infra.agent_system.agent_config import (
    MasterControllerConfig,
    load_default_config,
)
from infra.agent_system.agent_factory import (
    AgentToolsBundle,
    SocialEngineBundle,
    build_agent_tools,
    build_orchestrator,
    build_router,
    build_skill_registry,
    build_social_engine,
)
from infra.agent_system.agents.auditor.tools import AuditorTools
from infra.agent_system.agents.character_designer.tools import CharacterDesignerTools
from infra.agent_system.agents.content_writer.tools import ContentWriterTools
from infra.agent_system.agents.outline_master.tools import OutlineMasterTools
from infra.agent_system.agents.polisher.tools import PolisherTools
from infra.agent_system.core.context_builder import ContextBuilder
from infra.agent_system.orchestration.task_orchestrator import TaskOrchestrator
from infra.agent_system.registry.skill_registry import SkillRegistry
from infra.agent_system.social_engine.conflict_alert import ConflictAlert
from infra.agent_system.social_engine.event_effect_calculator import EventEffectCalculator
from infra.agent_system.social_engine.relationship_tracker import RelationshipTracker
from infra.agent_system.social_engine.writing_suggestion import WritingSuggestion
from infra.ai_service import ProviderConfig
from infra.ai_service.router import AIRouter


def _make_config(provider="minimax", model="MiniMax-M2.7"):
    """构造测试用的 MasterControllerConfig（不依赖 env vars）"""
    return MasterControllerConfig(
        state_dir="/tmp/test_state",
        primary_provider=provider,
        enable_failover=True,
        providers={provider: ProviderConfig(api_key="test-key", model=model)},
    )


def test_build_router_uses_config_primary(monkeypatch):
    """build_router 使用 config.primary_provider"""
    monkeypatch.setenv("MINIMAX_API_KEY", "x")
    config = _make_config(provider="minimax", model="test-model")

    router = build_router(config)

    assert isinstance(router, AIRouter)


def test_build_orchestrator_returns_correct_type():
    """build_orchestrator 返回 TaskOrchestrator"""
    orch = build_orchestrator()

    assert isinstance(orch, TaskOrchestrator)


def test_build_skill_registry_returns_correct_type():
    """build_skill_registry 返回 SkillRegistry"""
    reg = build_skill_registry()

    assert isinstance(reg, SkillRegistry)


def test_build_agent_tools_returns_bundle_with_all_5_types():
    """build_agent_tools 返回的 bundle 包含 5 个正确类型的工具"""
    config = _make_config()
    router = build_router(config)

    tools = build_agent_tools(router)

    assert isinstance(tools, AgentToolsBundle)
    assert isinstance(tools.outline_master, OutlineMasterTools)
    assert isinstance(tools.character_designer, CharacterDesignerTools)
    assert isinstance(tools.content_writer, ContentWriterTools)
    assert isinstance(tools.auditor, AuditorTools)
    assert isinstance(tools.polisher, PolisherTools)


def test_build_social_engine_returns_bundle_with_all_5_types(tmp_path):
    """build_social_engine 返回的 bundle 包含 5 个正确类型的组件"""
    social = build_social_engine(str(tmp_path))

    assert isinstance(social, SocialEngineBundle)
    assert isinstance(social.relationship_tracker, RelationshipTracker)
    assert isinstance(social.event_calculator, EventEffectCalculator)
    assert isinstance(social.conflict_alert, ConflictAlert)
    assert isinstance(social.writing_suggestion, WritingSuggestion)
    assert isinstance(social.context_builder, ContextBuilder)


def test_build_social_engine_relationship_state_file_under_state_dir(tmp_path):
    """relationship_tracker 的 state_file 应在 state_dir/social_engine/ 下 (R2-012: .db)"""
    social = build_social_engine(str(tmp_path))

    expected = tmp_path / "social_engine" / "relationship_network.db"
    assert social.relationship_tracker.state_file == str(expected)
    # 状态文件父目录已创建
    assert expected.parent.exists()
