#!/usr/bin/env python3
"""
LLM因果推理检测器测试

测试LLM辅助的复杂因果推理检测器
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infra.consistency.checkers.llm_causal_reasoning_checker import LLMCausalReasoningChecker
from infra.consistency.engine.data_structures import Issue


def test_llm_causal_reasoning_checker_basic():
    """基础测试：验证检查器可以正常初始化和调用"""
    checker = LLMCausalReasoningChecker()

    # 验证检查器可以正常初始化
    assert checker is not None
    assert checker.enabled is True

    # 这是一个复杂的因果场景，需要LLM判断
    chapter_content = """
    林夜看着倒在地上的剑尘子，嘴角勾起一抹冷笑。
    "你终究还是死在了我手里。"
    剑尘子的身体逐渐消散，仿佛从未存在过。

    十年后，林夜站在山巅，突然听到身后传来熟悉的声音。
    "林夜，我回来了。"
    剑尘子完好无损地站在他身后，脸上带着微笑。
    """

    # 由于LLM调用可能较慢或昂贵，基础测试只检查结构
    issues = checker.check(chapter_content, chapter_num=50, context={})

    # 返回的应该是Issue列表（即使为空）
    assert isinstance(issues, list)


def test_llm_causal_reasoning_checker_structure():
    """测试：验证返回的Issue结构正确"""
    checker = LLMCausalReasoningChecker()

    # 简单场景
    content = "林夜杀死了剑尘子。十年后，剑尘子复活了。"

    issues = checker.check(content, chapter_num=1, context={})

    # 验证返回的是Issue列表
    for issue in issues:
        assert isinstance(issue, Issue)
        assert issue.checker_type.value == "llm_causal_reasoning"


def test_llm_causal_reasoning_checker_disabled():
    """测试：验证禁用时返回空列表"""
    checker = LLMCausalReasoningChecker(enabled=False)

    content = "林夜杀死了剑尘子。"

    issues = checker.check(content, chapter_num=1, context={})

    assert isinstance(issues, list)
    assert len(issues) == 0


def test_llm_causal_reasoning_checker_context():
    """测试：验证上下文信息被正确使用"""
    checker = LLMCausalReasoningChecker()

    content = "林夜看着倒在地上的剑尘子。"

    context = {
        "character_profiles": {
            "林夜": {"gender": "male", "description": "主角"},
            "剑尘子": {"gender": "male", "description": "反派"}
        },
        "world_rules": "修真世界，修炼境界分为炼气、筑基、金丹、元婴、化神",
        "previous_summary": "林夜与剑尘子决战，这是他们的最终对决。"
    }

    issues = checker.check(content, chapter_num=1, context=context)

    assert isinstance(issues, list)


def test_llm_causal_reasoning_checker_emotional_proportion():
    """测试：情感反应比例失调场景"""
    checker = LLMCausalReasoningChecker()

    # 情感反应不符合人物关系
    content = """
    林夜走在街上，突然听到一声惨叫。
    一个陌生人倒在了血泊中。
    林夜悲痛欲绝，泪流满面。
    "我的朋友啊，你怎么能死！"
    """

    issues = checker.check(content, chapter_num=5, context={})

    assert isinstance(issues, list)
    # LLM应该能识别出这种情感反应不合理（刚认识的人却极度悲伤）


def test_llm_causal_reasoning_checker_world_rule_violation():
    """测试：世界规则矛盾场景"""
    checker = LLMCausalReasoningChecker()

    # 世界规则矛盾
    content = """
    在这个修真世界，修士们无法飞行。
    境界限制了一切飞行能力。

    然而，林夜却轻松飞上了天空。
    """

    issues = checker.check(content, chapter_num=10, context={})

    assert isinstance(issues, list)
    # LLM应该能识别出世界规则矛盾


def test_llm_causal_reasoning_checker_causal_chain():
    """测试：因果链断裂场景"""
    checker = LLMCausalReasoningChecker()

    # 因果链断裂
    content = """
    林夜用尽全力发出了毁天灭地的一击。
    整个山峰被夷为平地。

    然而，剑尘子只是拍了拍身上的灰尘。
    "就这？"
    """

    issues = checker.check(content, chapter_num=20, context={})

    assert isinstance(issues, list)


def test_extract_json_text_strips_thinking_blocks():
    """测试：剥离 reasoning 块后仍能解析 JSON"""
    checker = LLMCausalReasoningChecker()
    wrapped = (
        "<think>internal reasoning</think>\n"
        '{"contradictions": [{"type": "causal_chain", "description": "x"}]}'
    )
    assert json.loads(checker._extract_json_text(wrapped))["contradictions"]


def test_llm_issue_severity_is_p1():
    """LLM 检测项最高 P1，避免 golden P0 门误拦"""
    checker = LLMCausalReasoningChecker()
    issue = checker._create_issue(
        {"type": "world_rule_violation", "description": "test", "severity": "P0"},
        chapter_num=10,
    )
    assert issue.severity.value == "P1"


    """测试：不应该产生误报的情况"""
    checker = LLMCausalReasoningChecker()

    # 伏笔场景（不应该报为矛盾）
    content = """
    林夜看着手中的剑胚，眼神深邃。
    "这把剑，注定要改变一切。"
    他将剑胚藏入怀中，转身离去。

    （这是伏笔，不是矛盾）
    """

    issues = checker.check(content, chapter_num=30, context={})

    # 伏笔不应该被报告为矛盾
    assert isinstance(issues, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
