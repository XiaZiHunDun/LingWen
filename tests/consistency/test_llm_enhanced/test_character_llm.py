#!/usr/bin/env python3
"""
LLMEnhancedCharacterChecker测试

验证角色检测器的LLM增强功能
"""

from unittest.mock import Mock, patch

import pytest


def test_character_llm_finds_uncertain_regions():
    """测试LLM增强角色检测器能找到模糊区域"""
    from infra.consistency.checkers.llm_enhanced.character_llm import LLMEnhancedCharacterChecker

    checker = LLMEnhancedCharacterChecker()
    content = "林夜性情大变，原本冷静的他突然暴怒起来"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) > 0
    assert any("性情大变" in r["text"] or "突然暴怒" in r["text"] for r in regions)


def test_character_llm_multiple_patterns():
    """测试LLM增强角色检测器匹配多种模式"""
    from infra.consistency.checkers.llm_enhanced.character_llm import LLMEnhancedCharacterChecker

    checker = LLMEnhancedCharacterChecker()
    content = "他仿佛换了一个人，完全不像他平日里的样子，判若两人"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) >= 2


def test_character_llm_context_extraction():
    """测试LLM增强角色检测器正确提取上下文"""
    from infra.consistency.checkers.llm_enhanced.character_llm import LLMEnhancedCharacterChecker

    checker = LLMEnhancedCharacterChecker()
    content = "林夜突然暴怒，眼中闪过一丝疯狂"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) > 0
    assert "context" in regions[0]
    assert len(regions[0]["context"]) > 0


def test_character_llm_inherits_base_checker():
    """测试LLMEnhancedCharacterChecker继承基类检测器"""
    from infra.consistency.checkers.llm_enhanced.character_llm import LLMEnhancedCharacterChecker

    checker = LLMEnhancedCharacterChecker()
    assert checker.base_checker is not None
    assert checker.checker_type == "character"


def test_character_llm_has_llm_service():
    """测试LLMEnhancedCharacterChecker具有LLM服务"""
    from infra.consistency.checkers.llm_enhanced.character_llm import LLMEnhancedCharacterChecker

    checker = LLMEnhancedCharacterChecker()
    assert checker.llm_service is not None


def test_character_llm_region_positions():
    """测试LLM增强角色检测器正确记录位置"""
    from infra.consistency.checkers.llm_enhanced.character_llm import LLMEnhancedCharacterChecker

    checker = LLMEnhancedCharacterChecker()
    content = "性情大变，突然暴怒，判若两人"

    regions = checker._find_uncertain_regions(content, {})

    # 检查start/end位置是否正确
    for region in regions:
        assert "start" in region
        assert "end" in region
        assert region["start"] < region["end"]
        assert content[region["start"]:region["end"]] == region["text"]


def test_character_llm_no_matches():
    """测试LLM增强角色检测器在无匹配时返回空列表"""
    from infra.consistency.checkers.llm_enhanced.character_llm import LLMEnhancedCharacterChecker

    checker = LLMEnhancedCharacterChecker()
    content = "林夜冷静地分析着局势，一切都在计划之中"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) == 0
