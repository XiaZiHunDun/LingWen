#!/usr/bin/env python3
"""
LLMEnhancedRelationshipStateChecker测试

验证关系状态检测器的LLM增强功能
"""

from unittest.mock import Mock, patch

import pytest


def test_relationship_llm_finds_uncertain_regions():
    """测试LLM增强关系状态检测器能找到模糊区域"""
    from infra.consistency.checkers.llm_enhanced.relationship_llm import LLMEnhancedRelationshipStateChecker

    checker = LLMEnhancedRelationshipStateChecker()
    content = "林夜和星月原本是死对头，但这一刻他们突然和解了"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) > 0
    assert any("和解" in r["text"] or "突然" in r["text"] for r in regions)


def test_relationship_llm_multiple_patterns():
    """测试LLM增强关系状态检测器匹配多种模式"""
    from infra.consistency.checkers.llm_enhanced.relationship_llm import LLMEnhancedRelationshipStateChecker

    checker = LLMEnhancedRelationshipStateChecker()
    content = "从敌人变成朋友，一夜之间反目成仇"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) >= 2


def test_relationship_llm_context_extraction():
    """测试LLM增强关系状态检测器正确提取上下文"""
    from infra.consistency.checkers.llm_enhanced.relationship_llm import LLMEnhancedRelationshipStateChecker

    checker = LLMEnhancedRelationshipStateChecker()
    content = "星月竟然相信了林夜的话，这对曾经的敌人竟然握手言和"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) > 0
    assert "context" in regions[0]
    assert len(regions[0]["context"]) > 0


def test_relationship_llm_inherits_base_checker():
    """测试LLMEnhancedRelationshipStateChecker继承基类检测器"""
    from infra.consistency.checkers.llm_enhanced.relationship_llm import LLMEnhancedRelationshipStateChecker

    checker = LLMEnhancedRelationshipStateChecker()
    assert checker.base_checker is not None
    assert checker.checker_type == "relationship"


def test_relationship_llm_has_llm_service():
    """测试LLMEnhancedRelationshipStateChecker具有LLM服务"""
    from infra.consistency.checkers.llm_enhanced.relationship_llm import LLMEnhancedRelationshipStateChecker

    checker = LLMEnhancedRelationshipStateChecker()
    assert checker.llm_service is not None


def test_relationship_llm_region_positions():
    """测试LLM增强关系状态检测器正确记录位置"""
    from infra.consistency.checkers.llm_enhanced.relationship_llm import LLMEnhancedRelationshipStateChecker

    checker = LLMEnhancedRelationshipStateChecker()
    content = "突然和解，瞬间成为朋友，从敌人变成"

    regions = checker._find_uncertain_regions(content, {})

    # 检查start/end位置是否正确
    for region in regions:
        assert "start" in region
        assert "end" in region
        assert region["start"] < region["end"]
        assert content[region["start"]:region["end"]] == region["text"]


def test_relationship_llm_no_matches():
    """测试LLM增强关系状态检测器在无匹配时返回空列表"""
    from infra.consistency.checkers.llm_enhanced.relationship_llm import LLMEnhancedRelationshipStateChecker

    checker = LLMEnhancedRelationshipStateChecker()
    content = "林夜和星月在战场上相遇，两人都是冷静的战士"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) == 0
