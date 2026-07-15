#!/usr/bin/env python3
"""
LLMEnhancedPersonalityChecker测试

验证性格检测器的LLM增强功能
"""

from unittest.mock import Mock, patch

import pytest


def test_personality_llm_finds_uncertain_regions():
    """测试LLM增强性格检测器能找到模糊区域"""
    from infra.consistency.checkers.llm_enhanced.personality_llm import LLMEnhancedPersonalityChecker

    checker = LLMEnhancedPersonalityChecker()
    content = "原本善良的林夜突然变得残忍无情，杀害了无辜的人"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) > 0
    assert any("残忍" in r["text"] or "善良" in r["text"] for r in regions)


def test_personality_llm_multiple_patterns():
    """测试LLM增强性格检测器匹配多种模式"""
    from infra.consistency.checkers.llm_enhanced.personality_llm import LLMEnhancedPersonalityChecker

    checker = LLMEnhancedPersonalityChecker()
    content = "他性情大变，完全变了一个人，判若两人"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) >= 2


def test_personality_llm_context_extraction():
    """测试LLM增强性格检测器正确提取上下文"""
    from infra.consistency.checkers.llm_enhanced.personality_llm import LLMEnhancedPersonalityChecker

    checker = LLMEnhancedPersonalityChecker()
    content = "林夜核心性格发生了巨大转变"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) > 0
    assert "context" in regions[0]
    assert len(regions[0]["context"]) > 0


def test_personality_llm_inherits_base_checker():
    """测试LLMEnhancedPersonalityChecker继承基类检测器"""
    from infra.consistency.checkers.llm_enhanced.personality_llm import LLMEnhancedPersonalityChecker

    checker = LLMEnhancedPersonalityChecker()
    assert checker.base_checker is not None
    assert checker.checker_type == "personality"


def test_personality_llm_has_llm_service():
    """测试LLMEnhancedPersonalityChecker具有LLM服务"""
    from infra.consistency.checkers.llm_enhanced.personality_llm import LLMEnhancedPersonalityChecker

    checker = LLMEnhancedPersonalityChecker()
    assert checker.llm_service is not None


def test_personality_llm_region_positions():
    """测试LLM增强性格检测器正确记录位置"""
    from infra.consistency.checkers.llm_enhanced.personality_llm import LLMEnhancedPersonalityChecker

    checker = LLMEnhancedPersonalityChecker()
    content = "突然变得残忍，性情大变"

    regions = checker._find_uncertain_regions(content, {})

    # 检查start/end位置是否正确
    for region in regions:
        assert "start" in region
        assert "end" in region
        assert region["start"] < region["end"]
        assert content[region["start"]:region["end"]] == region["text"]
