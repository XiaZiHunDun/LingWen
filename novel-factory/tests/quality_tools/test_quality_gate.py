"""质量门禁测试"""

import pytest
from quality_gate import (
    QualityGate,
    QualityLevel,
    QualityResult,
)
from quality_tools.hard_validators.base import (
    BaseValidator,
    ValidationResult,
    IssueSeverity,
)
from quality_tools.soft_scorers.base import BaseScorer, ScoredResult


class MockValidator(BaseValidator):
    """模拟验证器"""

    def __init__(self, passed: bool = True, issues: list = None, severity: IssueSeverity = IssueSeverity.P2):
        self._passed = passed
        self._issues = issues or []
        self._severity = severity

    def validate(self, content: str, context: dict) -> ValidationResult:
        return ValidationResult(
            passed=self._passed,
            issues=self._issues,
            severity=self._severity
        )


class MockScorer(BaseScorer):
    """模拟评分器"""

    def __init__(self, score: float = 80.0, reason: str = "测试评分"):
        self._score = score
        self._reason = reason
        self.weight = 1.0

    def score(self, content: str, context: dict) -> ScoredResult:
        return ScoredResult(score=self._score, reason=self._reason)


class TestQualityLevel:
    """质量等级枚举测试"""

    def test_quality_levels(self):
        """测试质量等级定义"""
        assert QualityLevel.BRONZE.min_score == 0.60
        assert QualityLevel.SILVER.min_score == 0.75
        assert QualityLevel.GOLD.min_score == 0.90
        assert QualityLevel.PLATINUM.min_score == 0.95

    def test_quality_level_labels(self):
        """测试质量等级标签"""
        assert QualityLevel.BRONZE.name_label == "Bronze"
        assert QualityLevel.SILVER.name_label == "Silver"
        assert QualityLevel.GOLD.name_label == "Gold"
        assert QualityLevel.PLATINUM.name_label == "Platinum"


class TestQualityGate:
    """QualityGate 测试"""

    def test_hard_validators_must_pass(self):
        """测试硬性验证器必须通过"""
        validators = [
            MockValidator(passed=False, issues=["问题1"], severity=IssueSeverity.P0),
        ]
        scorers = [MockScorer(score=90.0)]

        gate = QualityGate(
            hard_validators=validators,
            soft_scorers=scorers,
            required_level=QualityLevel.SILVER
        )

        result = gate.check("测试内容", {})

        assert result.hard_passed is False
        assert "问题1" in result.issues

    def test_bronze_level(self):
        """测试 Bronze 分级"""
        validators = [MockValidator(passed=True)]
        scorers = [MockScorer(score=60.0)]

        gate = QualityGate(hard_validators=validators, soft_scorers=scorers)
        result = gate.check("测试内容", {})

        assert result.level == QualityLevel.BRONZE
        assert result.hard_passed is True
        assert result.soft_score == 0.6

    def test_silver_level(self):
        """测试 Silver 分级"""
        validators = [MockValidator(passed=True)]
        scorers = [MockScorer(score=80.0)]

        gate = QualityGate(hard_validators=validators, soft_scorers=scorers)
        result = gate.check("测试内容", {})

        assert result.level == QualityLevel.SILVER
        assert result.hard_passed is True

    def test_gold_level(self):
        """测试 Gold 分级"""
        validators = [MockValidator(passed=True)]
        scorers = [MockScorer(score=92.0)]

        gate = QualityGate(hard_validators=validators, soft_scorers=scorers)
        result = gate.check("测试内容", {})

        assert result.level == QualityLevel.GOLD
        assert result.soft_score == 0.92

    def test_platinum_level(self):
        """测试 Platinum 分级"""
        validators = [MockValidator(passed=True)]
        scorers = [MockScorer(score=97.0)]

        gate = QualityGate(hard_validators=validators, soft_scorers=scorers)
        result = gate.check("测试内容", {})

        assert result.level == QualityLevel.PLATINUM
        assert result.p0_count == 0

    def test_all_hard_pass_then_soft_score(self):
        """测试硬性通过后才计算软性评分"""
        validators = [MockValidator(passed=True)]
        scorers = [MockScorer(score=85.0)]

        gate = QualityGate(hard_validators=validators, soft_scorers=scorers)
        result = gate.check("测试内容", {})

        assert result.hard_passed is True
        assert result.soft_score == 0.85
        assert result.level == QualityLevel.SILVER

    def test_multiple_hard_validators(self):
        """测试多个硬性验证器"""
        validators = [
            MockValidator(passed=True),
            MockValidator(passed=True),
            MockValidator(passed=False, issues=["问题A"], severity=IssueSeverity.P1),
        ]
        scorers = [MockScorer(score=90.0)]

        gate = QualityGate(hard_validators=validators, soft_scorers=scorers)
        result = gate.check("测试内容", {})

        assert result.hard_passed is False
        assert "问题A" in result.issues
        assert result.p0_count == 1

    def test_required_level(self):
        """测试要求的最低等级"""
        validators = [MockValidator(passed=True)]
        scorers = [MockScorer(score=70.0)]

        gate = QualityGate(
            hard_validators=validators,
            soft_scorers=scorers,
            required_level=QualityLevel.GOLD
        )

        assert gate.get_required_level() == QualityLevel.GOLD