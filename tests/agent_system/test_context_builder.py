# tests/agent_system/test_context_builder.py
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../novel-factory'))

from agent_system.shared.context_builder import ContextBuilder

def test_context_builder_init():
    """测试上下文构建器初始化"""
    builder = ContextBuilder()
    assert builder is not None

def test_build_writing_context():
    """测试构建写作上下文"""
    builder = ContextBuilder()
    context = builder.build_writing_context(
        chapter_outline={"num": 50, "title": "第五十章", "events": ["战斗"]},
        characters=[{"name": "铁蛋", "personality": ["冷静"], "current_location": "战场"}],
        memory_context={},
        relationship_network={}
    )
    assert context["chapter_outline"]["num"] == 50
    assert len(context["characters"]) == 1
    assert "character_states" in context
    assert "style_guide" in context

def test_build_writing_context_with_foreshadow():
    """测试构建包含伏笔的上下文"""
    builder = ContextBuilder()
    memory = {
        "pending_foreshadows": [
            {"id": 1, "setup_chapter": 10, "description": "神秘剑客"}
        ]
    }
    context = builder.build_writing_context(
        chapter_outline={"num": 30, "title": "第三十章", "events": []},
        characters=[],
        memory_context=memory,
        relationship_network={}
    )
    assert len(context["active_foreshadow"]) == 1

def test_build_writing_context_with_recent_events():
    """测试构建包含最近事件的上下文"""
    builder = ContextBuilder()
    memory = {
        "recent_events": [
            {"chapter": 45, "event": "铁蛋获得神秘力量"},
            {"chapter": 46, "event": "林夜受伤"}
        ]
    }
    context = builder.build_writing_context(
        chapter_outline={"num": 47, "title": "第四十七章", "events": []},
        characters=[],
        memory_context=memory,
        relationship_network={}
    )
    # 只取最近5条
    assert isinstance(context["recent_events"], list)

def test_build_writing_context_with_style_guide():
    """测试自定义文风指南"""
    builder = ContextBuilder()
    custom_style = {"tone": "古风", "dialogue_ratio": "40%"}
    context = builder.build_writing_context(
        chapter_outline={"num": 1, "title": "第一章", "events": []},
        characters=[],
        memory_context={},
        relationship_network={},
        style_guide=custom_style
    )
    assert context["style_guide"]["tone"] == "古风"

def test_get_current_states():
    """测试获取角色当前状态"""
    builder = ContextBuilder()
    characters = [
        {"name": "铁蛋", "current_location": "村庄", "emotion_state": "平静", "alive": True},
        {"name": "林夜", "current_location": "山谷", "emotion_state": "悲伤", "alive": True}
    ]
    states = builder._get_current_states(characters)
    assert states["铁蛋"]["location"] == "村庄"
    assert states["铁蛋"]["emotion"] == "平静"

def test_get_default_style_guide():
    """测试默认文风指南"""
    builder = ContextBuilder()
    style = builder._get_default_style_guide()
    assert "tone" in style
    assert "dialogue_ratio" in style
    assert style["tone"] == "简洁有力"