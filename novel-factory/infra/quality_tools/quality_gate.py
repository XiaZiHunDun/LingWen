"""质量门禁 - 方向H质量工具集"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from quality_tools.hard_validators.base import BaseValidator, ValidationResult
from quality_tools.soft_scorers.base import BaseScorer, ScoredResult


class QualityLevel(Enum):
    """质量等级枚举"""
    BRONZE = ("Bronze", 0.60)    # (名称, 最低分数)
    SILVER = ("Silver", 0.75)
    GOLD = ("Gold", 0.90)
    PLATINUM = ("Platinum", 0.95)

    @property
    def name_label(self) -> str:
        return self.value[0]

    @property
    def min_score(self) -> float:
        return self.value[1]


@dataclass
class QualityResult:
    """质量检查结果"""
    level: QualityLevel
    hard_passed: bool
    soft_score: float
    issues: List[str] = field(default_factory=list)
    p0_count: int = 0


class QualityGate:
    """质量门禁"""

    def __init__(
        self,
        hard_validators: Optional[List[BaseValidator]] = None,
        soft_scorers: Optional[List[BaseScorer]] = None,
        required_level: QualityLevel = QualityLevel.BRONZE
    ):
        self.hard_validators = hard_validators or []
        self.soft_scorers = soft_scorers or []
        self.required_level = required_level

    def get_required_level(self) -> QualityLevel:
        """获取要求的最低质量等级"""
        return self.required_level

    def _run_hard_validators(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> tuple[bool, List[str], int]:
        """运行硬性验证器"""
        all_passed = True
        all_issues: List[str] = []
        p0_count = 0

        for validator in self.hard_validators:
            result = validator.validate(content, context)
            if not result.passed:
                all_passed = False
                all_issues.extend(result.issues)
                if result.severity.value <= 2:  # P0 or P1
                    p0_count += 1

        return all_passed, all_issues, p0_count

    def _run_soft_scorers(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> float:
        """运行软性评分器并计算加权总分"""
        if not self.soft_scorers:
            return 0.0

        total_weight = 0.0
        weighted_score = 0.0

        for scorer in self.soft_scorers:
            result = scorer.score(content, context)
            weight = getattr(scorer, 'weight', 1.0)
            weighted_score += result.score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return (weighted_score / total_weight) / 100.0  # 归一化到 0-1

    def _determine_level(
        self,
        hard_passed: bool,
        soft_score: float,
        p0_count: int
    ) -> QualityLevel:
        """根据分数确定质量等级"""
        if not hard_passed:
            # 如果硬性验证失败，返回最低等级
            return QualityLevel.BRONZE

        if soft_score >= 0.95 and p0_count == 0:
            return QualityLevel.PLATINUM
        elif soft_score >= 0.90:
            return QualityLevel.GOLD
        elif soft_score >= 0.75:
            return QualityLevel.SILVER
        else:
            return QualityLevel.BRONZE

    def check(self, content: str, context: Dict[str, Any]) -> QualityResult:
        """
        检查内容质量

        返回 QualityResult:
        - level: QualityLevel
        - hard_passed: bool
        - soft_score: float
        - issues: List[str]
        """
        # 1. 运行硬性验证器
        hard_passed, issues, p0_count = self._run_hard_validators(content, context)

        # 2. 如果硬性验证失败，直接返回
        if not hard_passed:
            return QualityResult(
                level=QualityLevel.BRONZE,
                hard_passed=False,
                soft_score=0.0,
                issues=issues,
                p0_count=p0_count
            )

        # 3. 运行软性评分器
        soft_score = self._run_soft_scorers(content, context)

        # 4. 确定质量等级
        level = self._determine_level(hard_passed, soft_score, p0_count)

        return QualityResult(
            level=level,
            hard_passed=True,
            soft_score=soft_score,
            issues=issues,
            p0_count=p0_count
        )