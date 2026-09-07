# tests/agent_system/test_master_controller.py
import os
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


def test_master_controller_init():
    """测试主控调度器初始化"""
    with patch("lingwen_core.agents.social_engine.relationship_tracker.RelationshipTracker"):
        with patch("lingwen_core.agents.core.context_builder.ContextBuilder"):
            from lingwen_pipeline.master_controller import MasterController

            controller = MasterController()
            assert controller is not None
            assert controller.outline_master is not None
            assert controller.character_designer is not None
            assert controller.content_writer is not None
            assert controller.auditor is not None
            assert controller.polisher is not None


def test_master_controller_generate_outline():
    """测试生成大纲"""
    with patch("lingwen_core.agents.social_engine.relationship_tracker.RelationshipTracker"):
        with patch("lingwen_core.agents.core.context_builder.ContextBuilder"):
            from lingwen_pipeline.master_controller import MasterController

            controller = MasterController()
            outline = controller.generate_outline(
                settings={"title": "测试小说", "genre": "玄幻"}, requirements={"total_chapters": 100}
            )
            assert outline["title"] == "测试小说"
            assert len(outline["chapters"]) == 100


def test_master_controller_generate_characters():
    """测试生成角色"""
    with patch("lingwen_core.agents.social_engine.relationship_tracker.RelationshipTracker"):
        with patch("lingwen_core.agents.core.context_builder.ContextBuilder"):
            from lingwen_pipeline.master_controller import MasterController

            controller = MasterController()
            characters = controller.generate_characters(
                outline={"title": "测试"},
                character_requirements=[{"name": "铁蛋", "personality": ["冷静"], "first_appearance": 1}],
            )
            assert len(characters) == 1
            assert characters[0]["name"] == "铁蛋"


def test_master_controller_write_chapter(tmp_path):
    """测试写章节流程 (no-LLM path 返回 prompt+suggestions+context).

    Phase 30 T5: 用 make_master_with_router 注入 stub router,
    消除对 OPENAI_API_KEY / ANTHROPIC_API_KEY / MINIMAX_API_KEY env 的依赖.
    """
    from tests.agent_system._e2e_helpers import make_master_with_router

    master = make_master_with_router(tmp_path)

    result = master.write_chapter(
        chapter_num=50,
        outline={"title": "测试", "chapters": [{"num": 50, "title": "第五十章", "events": []}]},
        characters=[],
        memory_context={},
        style_guide={},
        use_llm=False,
    )

    assert "prompt" in result
    assert "suggestions" in result
    assert "context" in result


def test_master_controller_audit_chapter(tmp_path):
    """测试审核章节 (no-LLM path 返回 issues+suggestions 空列表).

    Phase 30 T5: 用 make_master_with_router 注入 stub router,
    消除对 API key env 的依赖. 修正 assert 反映真实契约:
    no-LLM 路径不返 'chapter' 字段,只返 issues/suggestions.
    """
    from tests.agent_system._e2e_helpers import make_master_with_router

    master = make_master_with_router(tmp_path)
    content = "铁蛋冷静地看着对手。首先，他需要分析局势。"
    report = master.audit_chapter(
        chapter_num=50,
        content=content,
        characters=[{"name": "铁蛋", "personality": ["冷静"]}],
        timeline=[],
        use_llm=False,
    )
    assert "issues" in report
    assert "suggestions" in report


def test_master_controller_polish_chapter():
    """测试润色章节"""
    with patch("lingwen_core.agents.social_engine.relationship_tracker.RelationshipTracker"):
        with patch("lingwen_core.agents.core.context_builder.ContextBuilder"):
            from lingwen_pipeline.master_controller import MasterController

            controller = MasterController()
            content = "首先，铁蛋分析了情况。其次，他做出了决定。最后，执行计划。"
            result = controller.polish_chapter(content)
            assert "首先" not in result
            assert "其次" not in result
