#!/usr/bin/env python3
"""
LLMEnhancedChecker基类测试

验证LLMEnhancedChecker基类的初始化和基本功能
"""

import pytest
from unittest.mock import Mock, patch


def test_llm_enhanced_base_initialization():
    """测试LLMEnhancedChecker基类初始化"""
    from infra.consistency.checkers.llm_enhanced.base import LLMEnhancedChecker
    from infra.consistency.checkers.ability_checker import AbilityChecker
    from infra.consistency.llm_service.base import LLMService

    base_checker = AbilityChecker()
    llm_service = LLMService()
    enhanced = LLMEnhancedChecker(base_checker, llm_service, "ability")

    assert enhanced.base_checker is base_checker
    assert enhanced.llm_service is llm_service
    assert enhanced.checker_type == "ability"


def test_llm_enhanced_prompt_mapping():
    """测试PROMPT_MAP正确映射"""
    from infra.consistency.checkers.llm_enhanced.base import LLMEnhancedChecker
    from infra.consistency.checkers.ability_checker import AbilityChecker
    from infra.consistency.llm_service.base import LLMService
    from infra.consistency.llm_service.prompts import ABILITY_LLM_PROMPT

    base_checker = AbilityChecker()
    llm_service = LLMService()
    enhanced = LLMEnhancedChecker(base_checker, llm_service, "ability")

    assert enhanced.prompt_template == ABILITY_LLM_PROMPT


def test_llm_enhanced_checker_type_all():
    """测试所有checker_type都能正确映射"""
    from infra.consistency.checkers.llm_enhanced.base import LLMEnhancedChecker
    from infra.consistency.checkers.ability_checker import AbilityChecker
    from infra.consistency.llm_service.base import LLMService

    checker_types = [
        "ability", "character", "relationship",
        "foreshadow", "battle", "personality", "knowledge"
    ]

    for ct in checker_types:
        base_checker = AbilityChecker()
        llm_service = LLMService()
        enhanced = LLMEnhancedChecker(base_checker, llm_service, ct)
        assert enhanced.checker_type == ct
        assert enhanced.prompt_template != ""  # 应该都有prompt


def test_llm_enhanced_find_uncertain_regions():
    """测试_find_uncertain_regions返回空列表（基类实现）"""
    from infra.consistency.checkers.llm_enhanced.base import LLMEnhancedChecker
    from infra.consistency.checkers.ability_checker import AbilityChecker
    from infra.consistency.llm_service.base import LLMService

    base_checker = AbilityChecker()
    llm_service = LLMService()
    enhanced = LLMEnhancedChecker(base_checker, llm_service, "ability")

    regions = enhanced._find_uncertain_regions("test content", {})
    assert regions == []


def test_llm_enhanced_convert_llm_issues():
    """测试_convert_llm_issues正确转换LLMIssue为Issue"""
    from infra.consistency.checkers.llm_enhanced.base import LLMEnhancedChecker
    from infra.consistency.checkers.ability_checker import AbilityChecker
    from infra.consistency.llm_service.base import LLMService
    from infra.consistency.llm_service.chapter_content import LLMIssue

    base_checker = AbilityChecker()
    llm_service = LLMService()
    enhanced = LLMEnhancedChecker(base_checker, llm_service, "ability")

    llm_issues = [
        LLMIssue(chapter=1, type="test_type", description="test description",
                 evidence="test evidence", suggestion="test suggestion", severity="P0"),
        LLMIssue(chapter=2, type="test_type2", description="test description2",
                 evidence="test evidence2", suggestion="test suggestion2", severity="P1"),
    ]

    issues = enhanced._convert_llm_issues(llm_issues, default_chapter=1)

    assert len(issues) == 2
    assert issues[0].severity.value == "P0"
    assert issues[1].severity.value == "P1"
    assert issues[0].issue_type == "test_type"
    assert issues[1].issue_type == "test_type2"