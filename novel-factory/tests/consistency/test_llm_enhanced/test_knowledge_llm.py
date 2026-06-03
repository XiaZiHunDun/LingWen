# novel-factory/tests/consistency/test_llm_enhanced/test_knowledge_llm.py
from unittest.mock import MagicMock, patch

import pytest


class TestLLMEnhancedKnowledgeTracker:
    """测试知识追踪LLM增强检测器"""

    def test_knowledge_llm_finds_uncertain_regions(self):
        """测试_find_uncertain_regions能正确识别需要LLM判断的信息知晓段落"""
        from infra.consistency.checkers.llm_enhanced.knowledge_llm import LLMEnhancedKnowledgeTracker

        checker = LLMEnhancedKnowledgeTracker()
        content = "林夜明明知道这个秘密，却假装不知道，继续演戏"

        regions = checker._find_uncertain_regions(content, {})

        assert len(regions) > 0
        assert any("假装不知道" in r["text"] or "明明知道" in r["text"] for r in regions)

    def test_knowledge_llm_finds_multiple_patterns(self):
        """测试多种知识知晓模式都能被识别"""
        from infra.consistency.checkers.llm_enhanced.knowledge_llm import LLMEnhancedKnowledgeTracker

        checker = LLMEnhancedKnowledgeTracker()
        content = "他心知肚明，却装作不知情"

        regions = checker._find_uncertain_regions(content, {})

        assert len(regions) > 0
        assert any("心知肚明" in r["text"] or "装作不知" in r["text"] for r in regions)

    def test_knowledge_llm_returns_empty_for_plain_text(self):
        """测试没有模糊区域时返回空列表"""
        from infra.consistency.checkers.llm_enhanced.knowledge_llm import LLMEnhancedKnowledgeTracker

        checker = LLMEnhancedKnowledgeTracker()
        content = "林夜走进了房间，看到桌上放着一封信。"

        regions = checker._find_uncertain_regions(content, {})

        # 正常叙事不包含模糊区域
        assert len(regions) == 0

    def test_knowledge_llm_has_correct_structure(self):
        """测试返回的region结构正确"""
        from infra.consistency.checkers.llm_enhanced.knowledge_llm import LLMEnhancedKnowledgeTracker

        checker = LLMEnhancedKnowledgeTracker()
        content = "他应该记得这件事，但看起来完全忘了"

        regions = checker._find_uncertain_regions(content, {})

        assert len(regions) > 0
        region = regions[0]
        assert "type" in region
        assert "text" in region
        assert "start" in region
        assert "end" in region
        assert "context" in region
        assert region["type"] == "knowledge_uncertain"

    def test_checker_type_is_knowledge(self):
        """测试checker_type设置为knowledge"""
        from infra.consistency.checkers.llm_enhanced.knowledge_llm import LLMEnhancedKnowledgeTracker

        checker = LLMEnhancedKnowledgeTracker()

        assert checker.checker_type == "knowledge"

    def test_prompt_template_is_knowledge_llm(self):
        """测试prompt模板是KNOWLEDGE_LLM_PROMPT"""
        from infra.consistency.checkers.llm_enhanced.base import LLMEnhancedChecker
        from infra.consistency.checkers.llm_enhanced.knowledge_llm import LLMEnhancedKnowledgeTracker

        checker = LLMEnhancedKnowledgeTracker()

        # prompt_template应该来自KNOWLEDGE_LLM_PROMPT
        assert checker.prompt_template is not None
        assert "知识" in checker.prompt_template or "knowledge" in checker.prompt_template.lower()
