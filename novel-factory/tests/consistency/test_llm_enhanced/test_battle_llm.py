#!/usr/bin/env python3
"""
LLMEnhancedBattleVisualizationChecker测试

验证战斗描写检测器的LLM增强功能
"""

import pytest
from unittest.mock import Mock, patch


def test_battle_llm_finds_uncertain_regions():
    """测试LLM增强战斗检测器能找到模糊区域"""
    from infra.consistency.checkers.llm_enhanced.battle_llm import LLMEnhancedBattleVisualizationChecker

    checker = LLMEnhancedBattleVisualizationChecker()
    content = "林夜轻松击败了对手，但其实对手是修仙界第一人"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) > 0
    assert any("轻松击败" in r["text"] or "第一人" in r["text"] for r in regions)


def test_battle_llm_multiple_patterns():
    """测试LLM增强战斗检测器匹配多种模式"""
    from infra.consistency.checkers.llm_enhanced.battle_llm import LLMEnhancedBattleVisualizationChecker

    checker = LLMEnhancedBattleVisualizationChecker()
    content = "他瞬间斩杀了对手，竟然输了"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) >= 2


def test_battle_llm_context_extraction():
    """测试LLM增强战斗检测器正确提取上下文"""
    from infra.consistency.checkers.llm_enhanced.battle_llm import LLMEnhancedBattleVisualizationChecker

    checker = LLMEnhancedBattleVisualizationChecker()
    content = "林夜一招毙命，对方毫无还手之力"

    regions = checker._find_uncertain_regions(content, {})
    assert len(regions) > 0
    assert "context" in regions[0]
    assert len(regions[0]["context"]) > 0


def test_battle_llm_inherits_base_checker():
    """测试LLMEnhancedBattleVisualizationChecker继承基类检测器"""
    from infra.consistency.checkers.llm_enhanced.battle_llm import LLMEnhancedBattleVisualizationChecker

    checker = LLMEnhancedBattleVisualizationChecker()
    assert checker.base_checker is not None
    assert checker.checker_type == "battle"


def test_battle_llm_has_llm_service():
    """测试LLMEnhancedBattleVisualizationChecker具有LLM服务"""
    from infra.consistency.checkers.llm_enhanced.battle_llm import LLMEnhancedBattleVisualizationChecker

    checker = LLMEnhancedBattleVisualizationChecker()
    assert checker.llm_service is not None


def test_battle_llm_region_positions():
    """测试LLM增强战斗检测器正确记录位置"""
    from infra.consistency.checkers.llm_enhanced.battle_llm import LLMEnhancedBattleVisualizationChecker

    checker = LLMEnhancedBattleVisualizationChecker()
    content = "轻松击败，瞬间斩杀，一招毙命"

    regions = checker._find_uncertain_regions(content, {})

    # 检查start/end位置是否正确
    for region in regions:
        assert "start" in region
        assert "end" in region
        assert region["start"] < region["end"]
        assert content[region["start"]:region["end"]] == region["text"]