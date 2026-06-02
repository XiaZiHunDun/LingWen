#!/usr/bin/env python3
"""
测试 Claude/MiniMax 增强工具
"""

import os

import pytest
from unittest.mock import MagicMock, patch
from tools.anti_trope_enhancer import AntiTropeEnhancer, CreativeOption
from tools.llm_quality_analyzer import LLMQualityAnalyzer, SeverityDecision, RepairDecision, AnalysisResult


# Some tests construct real LLMService (which needs an API key in env).
# Per-test skipif so the pure-enum / dataclass tests still run offline.
_REQUIRES_API_KEY = pytest.mark.skipif(
    not (
        os.environ.get("MINIMAX_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
    ),
    reason="requires MINIMAX_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY env var",
)


class TestAntiTropeEnhancer:
    """AntiTropeEnhancer 测试"""

    @_REQUIRES_API_KEY
    def test_init(self):
        """测试初始化"""
        enhancer = AntiTropeEnhancer()
        assert enhancer is not None
        assert enhancer._llm is not None

    def test_generate_options_returns_list(self):
        """测试生成选项返回列表"""
        with patch.object(AntiTropeEnhancer, '__init__', lambda x: None):
            enhancer = AntiTropeEnhancer()
            enhancer._llm = MagicMock()
            enhancer._config = MagicMock()
            enhancer._config.minimax_api_key = "test-key"

            # Mock the LLM response
            mock_response = '[{"setting": "废土世界", "conflict": "生存竞争", "character": "沉默主角", "twist": "盟友背叛", "anti_trope_tags": ["反套路"]}]'
            enhancer._llm.execute = MagicMock(return_value=mock_response)

            # Use actual method
            with patch('tools.anti_trope_enhancer.LLMService') as MockLLM:
                MockLLM.return_value = MagicMock()
                MockLLM.return_value.execute = MagicMock(return_value=mock_response)

                actual_enhancer = AntiTropeEnhancer()
                options = actual_enhancer.generate_options("测试大纲", count=1)

                assert isinstance(options, list)

    @_REQUIRES_API_KEY
    def test_format_options(self):
        """测试格式化输出"""
        enhancer = AntiTropeEnhancer()
        options = [
            CreativeOption(
                id="test1",
                setting="废土世界",
                conflict="生存竞争",
                character="沉默主角",
                twist="盟友背叛",
                anti_trope_tags=["反套路"],
                match_score=0.8
            )
        ]

        formatted = enhancer.format_options(options)
        assert "反套路创意选项" in formatted
        assert "废土世界" in formatted
        assert "生存竞争" in formatted

    @_REQUIRES_API_KEY
    def test_format_options_empty(self):
        """测试空选项格式化"""
        enhancer = AntiTropeEnhancer()
        formatted = enhancer.format_options([])
        assert "无可用选项" in formatted


class TestLLMQualityAnalyzer:
    """LLM质检分析器测试"""

    @_REQUIRES_API_KEY
    def test_init(self):
        """测试初始化"""
        analyzer = LLMQualityAnalyzer()
        assert analyzer is not None
        assert analyzer._llm is not None

    def test_severity_decision_enum(self):
        """测试严重性枚举"""
        assert SeverityDecision.P0.value == "P0"
        assert SeverityDecision.P1.value == "P1"
        assert SeverityDecision.P2.value == "P2"

    def test_repair_decision_enum(self):
        """测试修复决策枚举"""
        assert RepairDecision.REQUIRED.value == "required"
        assert RepairDecision.RECOMMENDED.value == "recommended"
        assert RepairDecision.OPTIONAL.value == "optional"
        assert RepairDecision.SKIP.value == "skip"

    def test_analysis_result_dataclass(self):
        """测试分析结果数据类"""
        result = AnalysisResult(
            severity=SeverityDecision.P0,
            repair_decision=RepairDecision.REQUIRED,
            reasoning="角色行为逻辑矛盾",
            repair_suggestion="需要修复",
            confidence=0.95
        )

        assert result.severity == SeverityDecision.P0
        assert result.repair_decision == RepairDecision.REQUIRED
        assert result.confidence == 0.95

    @_REQUIRES_API_KEY
    def test_should_repair_required(self):
        """测试should_repair - 包含REQUIRED"""
        analyzer = LLMQualityAnalyzer()

        results = [
            AnalysisResult(
                severity=SeverityDecision.P2,
                repair_decision=RepairDecision.OPTIONAL,
                reasoning="",
                repair_suggestion="",
                confidence=0.5
            ),
            AnalysisResult(
                severity=SeverityDecision.P0,
                repair_decision=RepairDecision.REQUIRED,
                reasoning="",
                repair_suggestion="",
                confidence=0.9
            ),
        ]

        assert analyzer.should_repair(results) == True

    @_REQUIRES_API_KEY
    def test_should_repair_no_required(self):
        """测试should_repair - 无REQUIRED"""
        analyzer = LLMQualityAnalyzer()

        results = [
            AnalysisResult(
                severity=SeverityDecision.P2,
                repair_decision=RepairDecision.OPTIONAL,
                reasoning="",
                repair_suggestion="",
                confidence=0.5
            ),
        ]

        assert analyzer.should_repair(results) == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])