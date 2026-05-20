# tests/agent_system/test_agent_tools.py
import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from infra.agent_system.agents.outline_master.tools import OutlineMasterTools
from infra.agent_system.agents.character_designer.tools import CharacterDesignerTools
from infra.agent_system.agents.content_writer.tools import ContentWriterTools
from infra.agent_system.agents.auditor.tools import AuditorTools
from infra.agent_system.agents.polisher.tools import PolisherTools

def test_outline_master_tools():
    """测试大纲师工具"""
    tools = OutlineMasterTools()
    outline = tools.generate_outline(
        settings={"title": "测试小说", "genre": "玄幻"},
        requirements={"total_chapters": 100}
    )
    assert outline["title"] == "测试小说"
    assert len(outline["chapters"]) == 100

def test_outline_master_generate_chapter_outline():
    """测试生成章大纲"""
    tools = OutlineMasterTools()
    chapter = tools.generate_chapter_outline(
        chapter_num=50,
        events=["战斗", "胜利"],
        foreshadow=["神秘剑客"]
    )
    assert chapter["num"] == 50
    assert "战斗" in chapter["events"]

def test_character_designer_tools():
    """测试人设师工具"""
    tools = CharacterDesignerTools()
    character = tools.generate_character_card({
        "name": "铁蛋",
        "role": "protagonist",
        "personality": ["冷静", "务实"],
        "first_appearance": 1
    })
    assert character["name"] == "铁蛋"
    assert "冷静" in character["personality"]

def test_character_designer_add_relationship():
    """测试添加关系"""
    tools = CharacterDesignerTools()
    character = {"name": "铁蛋", "relationships": []}
    result = tools.add_relationship(character, "林夜", "ally", trust=0.7)
    assert len(result["relationships"]) == 1
    assert result["relationships"][0]["target"] == "林夜"

def test_content_writer_tools_build_prompt():
    """测试构建写作Prompt"""
    tools = ContentWriterTools()
    context = {
        "chapter_outline": {"num": 50, "title": "第五十章", "events": ["战斗"], "word_count_target": 2500},
        "characters": [{"name": "铁蛋", "personality": ["冷静"]}],
        "style_guide": {"tone": "简洁有力", "dialogue_ratio": "30%"}
    }
    prompt = tools.build_writing_prompt(context)
    assert "第五十章" in prompt
    assert "铁蛋" in prompt

def test_content_writer_add_hook():
    """测试添加章末钩子"""
    tools = ContentWriterTools()
    content = "战斗结束了。"
    result = tools.add_chapter_hook(content, "cliffhanger")
    assert len(result) > len(content)

def test_auditor_tools_detect_ai_gloss():
    """测试AI痕迹检测"""
    tools = AuditorTools()
    content = "首先，我们需要明确目标。其次，制定计划。最后，执行。"
    issues = tools.detect_ai_gloss(content)
    assert len(issues) >= 3  # 首先、其次、最后

def test_auditor_tools_check_consistency():
    """测试角色一致性检查"""
    tools = AuditorTools()
    content = "铁蛋冷静地看着对手，突然暴怒起来。"
    character_cards = [{"name": "铁蛋", "personality": ["冷静"]}]
    issues = tools.check_character_consistency(content, character_cards)
    assert len(issues) >= 1

def test_auditor_generate_report():
    """测试生成审核报告"""
    tools = AuditorTools()
    issues = [{"type": "ai_gloss", "severity": "P3"}]
    report = tools.generate_audit_report(50, issues, {"S1": 8, "S2": 7})
    assert report["chapter"] == 50
    assert "issues" in report

def test_polisher_tools_remove_ai_gloss():
    """测试去除AI痕迹"""
    tools = PolisherTools()
    content = "首先，我们需要冷静分析。其次，制定计划。最后，执行。首先要说的是..."
    result = tools.remove_ai_gloss(content)
    assert "首先" not in result
    assert "其次" not in result

def test_polisher_tools_apply_style():
    """测试应用文风指南"""
    tools = PolisherTools()
    content = "值得注意的是，我们需要认真地解决这个问题。"
    style = {"remove_filler": True}
    result = tools.apply_style_guide(content, style)
    assert "值得注意的是" not in result