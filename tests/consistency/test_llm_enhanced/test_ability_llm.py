#!/usr/bin/env python3
"""
LLMEnhancedAbilityChecker测试

验证能力检测器的LLM增强功能
"""

from unittest.mock import Mock, patch

import pytest


def test_ability_llm_finds_uncertain_regions():
    """测试LLM增强能力检测器能找到模糊区域"""
    from infra.consistency.checkers.llm_enhanced.ability_llm import LLMEnhancedAbilityChecker

    checker = LLMEnhancedAbilityChecker()
    content = "林夜突然实力大涨，一掌拍出，真气涌动"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) > 0
    assert any("实力大涨" in r["text"] for r in regions)


def test_ability_llm_multiple_patterns():
    """测试LLM增强能力检测器匹配多种模式"""
    from infra.consistency.checkers.llm_enhanced.ability_llm import LLMEnhancedAbilityChecker

    checker = LLMEnhancedAbilityChecker()
    content = "他竟然使出了绝世剑法，明明刚学会却能完美施展"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) >= 2


def test_ability_llm_context_extraction():
    """测试LLM增强能力检测器正确提取上下文"""
    from infra.consistency.checkers.llm_enhanced.ability_llm import LLMEnhancedAbilityChecker

    checker = LLMEnhancedAbilityChecker()
    content = "林夜毫无征兆地突破了修为瓶颈"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) > 0
    assert "context" in regions[0]
    assert len(regions[0]["context"]) > 0


def test_ability_llm_inherits_base_checker():
    """测试LLMEnhancedAbilityChecker继承基类检测器"""
    from infra.consistency.checkers.llm_enhanced.ability_llm import LLMEnhancedAbilityChecker

    checker = LLMEnhancedAbilityChecker()
    assert checker.base_checker is not None
    assert checker.checker_type == "ability"


def test_ability_llm_has_llm_service():
    """测试LLMEnhancedAbilityChecker具有LLM服务"""
    from infra.consistency.checkers.llm_enhanced.ability_llm import LLMEnhancedAbilityChecker

    checker = LLMEnhancedAbilityChecker()
    assert checker.llm_service is not None


def test_ability_llm_region_positions():
    """测试LLM增强能力检测器正确记录位置"""
    from infra.consistency.checkers.llm_enhanced.ability_llm import LLMEnhancedAbilityChecker

    checker = LLMEnhancedAbilityChecker()
    content = "突然实力大涨，一夜之间实力飙升"

    regions = checker._find_uncertain_regions(content, {})

    # 检查start/end位置是否正确
    for region in regions:
        assert "start" in region
        assert "end" in region
        assert region["start"] < region["end"]
        assert content[region["start"]:region["end"]] == region["text"]
