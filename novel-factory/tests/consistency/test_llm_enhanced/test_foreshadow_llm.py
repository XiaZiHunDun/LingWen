#!/usr/bin/env python3
"""
LLMEnhancedForeshadowChecker测试

验证伏笔检测器的LLM增强功能
"""

from unittest.mock import Mock, patch

import pytest


def test_foreshadow_llm_finds_uncertain_regions():
    """测试LLM增强伏笔检测器能找到模糊区域"""
    from infra.consistency.checkers.llm_enhanced.foreshadow_llm import LLMEnhancedForeshadowChecker

    checker = LLMEnhancedForeshadowChecker()
    content = "原来这个人和之前的事件有关，真相终于揭晓"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) > 0
    assert any("真相" in r["text"] or "揭晓" in r["text"] for r in regions)


def test_foreshadow_llm_multiple_patterns():
    """测试LLM增强伏笔检测器匹配多种模式"""
    from infra.consistency.checkers.llm_enhanced.foreshadow_llm import LLMEnhancedForeshadowChecker

    checker = LLMEnhancedForeshadowChecker()
    content = "原来他就是真凶，一切都说得通了"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) >= 2


def test_foreshadow_llm_context_extraction():
    """测试LLM增强伏笔检测器正确提取上下文"""
    from infra.consistency.checkers.llm_enhanced.foreshadow_llm import LLMEnhancedForeshadowChecker

    checker = LLMEnhancedForeshadowChecker()
    content = "直到现在才明白，原来一切都是命中注定"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) > 0
    assert "context" in regions[0]
    assert len(regions[0]["context"]) > 0


def test_foreshadow_llm_inherits_base_checker():
    """测试LLMEnhancedForeshadowChecker继承基类检测器"""
    from infra.consistency.checkers.llm_enhanced.foreshadow_llm import LLMEnhancedForeshadowChecker

    checker = LLMEnhancedForeshadowChecker()
    assert checker.base_checker is not None
    assert checker.checker_type == "foreshadow"


def test_foreshadow_llm_has_llm_service():
    """测试LLMEnhancedForeshadowChecker具有LLM服务"""
    from infra.consistency.checkers.llm_enhanced.foreshadow_llm import LLMEnhancedForeshadowChecker

    checker = LLMEnhancedForeshadowChecker()
    assert checker.llm_service is not None


def test_foreshadow_llm_region_positions():
    """测试LLM增强伏笔检测器正确记录位置"""
    from infra.consistency.checkers.llm_enhanced.foreshadow_llm import LLMEnhancedForeshadowChecker

    checker = LLMEnhancedForeshadowChecker()
    content = "原来真相是这样的，所有谜题揭晓"

    regions = checker._find_uncertain_regions(content, {})

    # 检查start/end位置是否正确
    for region in regions:
        assert "start" in region
        assert "end" in region
        assert region["start"] < region["end"]
        assert content[region["start"]:region["end"]] == region["text"]
