# tests/agent_system/test_master_controller.py
import os
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

def test_master_controller_init():
    """测试主控调度器初始化"""
    with patch('agent_system.master_controller.RelationshipTracker'):
        with patch('agent_system.master_controller.ContextBuilder'):
            from agent_system.master_controller import MasterController
            controller = MasterController()
            assert controller is not None
            assert controller.outline_master is not None
            assert controller.character_designer is not None
            assert controller.content_writer is not None
            assert controller.auditor is not None
            assert controller.polisher is not None

def test_master_controller_generate_outline():
    """测试生成大纲"""
    with patch('agent_system.master_controller.RelationshipTracker'):
        with patch('agent_system.master_controller.ContextBuilder'):
            from agent_system.master_controller import MasterController
            controller = MasterController()
            outline = controller.generate_outline(
                settings={"title": "测试小说", "genre": "玄幻"},
                requirements={"total_chapters": 100}
            )
            assert outline["title"] == "测试小说"
            assert len(outline["chapters"]) == 100

def test_master_controller_generate_characters():
    """测试生成角色"""
    with patch('agent_system.master_controller.RelationshipTracker'):
        with patch('agent_system.master_controller.ContextBuilder'):
            from agent_system.master_controller import MasterController
            controller = MasterController()
            characters = controller.generate_characters(
                outline={"title": "测试"},
                character_requirements=[
                    {"name": "铁蛋", "personality": ["冷静"], "first_appearance": 1}
                ]
            )
            assert len(characters) == 1
            assert characters[0]["name"] == "铁蛋"

def test_master_controller_write_chapter():
    """测试写章节流程"""
    with patch('agent_system.master_controller.RelationshipTracker') as mock_rt:
        with patch('agent_system.master_controller.ContextBuilder') as mock_cb:
            mock_network = {"characters": [], "relationships": [], "events": []}
            mock_rt_instance = Mock()
            mock_rt_instance.get_network.return_value = mock_network
            mock_rt.return_value = mock_rt_instance

            mock_cb_instance = Mock()
            mock_cb_instance.build_writing_context.return_value = {
                "chapter_outline": {"num": 50, "title": "第五十章"},
                "characters": [],
                "style_guide": {}
            }
            mock_cb.return_value = mock_cb_instance

            from agent_system.master_controller import MasterController
            controller = MasterController()

            result = controller.write_chapter(
                chapter_num=50,
                outline={"title": "测试", "chapters": [{"num": 50, "title": "第五十章", "events": []}]},
                characters=[],
                memory_context={},
                style_guide={}
            )

            assert "prompt" in result
            assert "suggestions" in result
            assert "context" in result

def test_master_controller_audit_chapter():
    """测试审核章节"""
    with patch('agent_system.master_controller.RelationshipTracker'):
        with patch('agent_system.master_controller.ContextBuilder'):
            from agent_system.master_controller import MasterController
            controller = MasterController()
            content = "铁蛋冷静地看着对手。首先，他需要分析局势。"
            report = controller.audit_chapter(
                chapter_num=50,
                content=content,
                characters=[{"name": "铁蛋", "personality": ["冷静"]}],
                timeline=[]
            )
            assert "chapter" in report
            assert "issues" in report

def test_master_controller_polish_chapter():
    """测试润色章节"""
    with patch('agent_system.master_controller.RelationshipTracker'):
        with patch('agent_system.master_controller.ContextBuilder'):
            from agent_system.master_controller import MasterController
            controller = MasterController()
            content = "首先，铁蛋分析了情况。其次，他做出了决定。最后，执行计划。"
            result = controller.polish_chapter(content)
            assert "首先" not in result
            assert "其次" not in result
