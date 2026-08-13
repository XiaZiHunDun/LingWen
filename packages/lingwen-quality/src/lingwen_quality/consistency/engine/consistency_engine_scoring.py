"""ConsistencyEngine 评分 Mixin（拆分自 consistency_engine.py）。

提供 ``ConsistencyEngineScoringMixin``：
- 单个 checker 得分计算（``_calculate_checker_result``）
- 检查器选择（``_get_checkers_for_scope``）
- S1-S8 质量维度评分（``_calculate_quality``）
- 报告总分（``_calculate_total_score``）
- 修改建议生成（``_generate_suggestions``）

被 ``ConsistencyEngine`` 通过多继承挂载。
"""

from __future__ import annotations

from typing import Any, Dict, List

from .data_structures import (
    CheckerResult,
    CheckerType,
    CheckScope,
    ConsistencyReport,
    Issue,
    IssueSeverity,
    QualityDimension,
)


class ConsistencyEngineScoringMixin:
    """评分/汇总 Mixin。

    需要混入对象实现：
    - ``checkers`` 属性 — ``Dict[CheckerType, Any]``
    """

    checkers: Dict[CheckerType, Any]

    def _run_checker(
        self,
        checker: Any,
        chapter_content: str,
        chapter_num: int,
        context: Dict[str, Any],
        propagate_errors: bool = False
    ) -> List[Issue]:
        """运行单个检查器（集成白名单机制）

        Args:
            checker: 检查器实例
            chapter_content: 章节内容
            chapter_num: 章节编号
            context: 上下文
            propagate_errors: 是否传播异常（默认 False：吞掉+日志，
                让其他 checkers 继续跑；True：让上层决定如何处理）

        Returns:
            检查器产出的 Issue 列表
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            # 使用 check_with_whitelist 方法集成白名单机制
            return checker.check_with_whitelist(
                chapter_content=chapter_content,
                chapter_num=chapter_num,
                context=context
            )
        except Exception as e:
            logger.error(
                f"Checker {checker.get_checker_type()} failed: {e}",
                exc_info=True
            )
            if propagate_errors:
                raise
            return []

    def _get_checkers_for_scope(self, scope: CheckScope) -> List[CheckerType]:
        """根据检查范围获取要运行的检查器"""
        if scope == CheckScope.ALL:
            return list(CheckerType)
        elif scope == CheckScope.CRITICAL:
            return [CheckerType.CHARACTER, CheckerType.ABILITY, CheckerType.TIMELINE_AGE]
        elif scope == CheckScope.IMPORTANT:
            return [
                CheckerType.CHARACTER, CheckerType.ABILITY,
                CheckerType.TIMELINE, CheckerType.ITEM, CheckerType.OUTLINE,
                CheckerType.SCENE_PATTERN, CheckerType.TIMELINE_AGE
            ]
        elif scope == CheckScope.STANDARD:
            return [
                CheckerType.CHARACTER, CheckerType.ITEM,
                CheckerType.TIMELINE, CheckerType.ABILITY,
                CheckerType.PERSONALITY, CheckerType.FORESHADOW,
                CheckerType.SCENE_PATTERN, CheckerType.FORESHADOW_QUALITY
            ]
        return list(CheckerType)

    def _calculate_checker_result(
        self,
        checker_type: CheckerType,
        issues: List[Issue],
        duration_ms: float
    ) -> CheckerResult:
        """计算检查器结果"""
        result = CheckerResult(
            checker_type=checker_type,
            issues=issues,
            check_duration_ms=duration_ms
        )

        # 计算得分
        base_score = 100
        deductions = 0

        for issue in issues:
            if issue.severity == IssueSeverity.P0:
                deductions += 50
            elif issue.severity == IssueSeverity.P1:
                deductions += 20
            elif issue.severity == IssueSeverity.P2:
                deductions += 5
            elif issue.severity == IssueSeverity.P3:
                deductions += 1

        result.score = max(0, base_score - deductions)
        return result

    def _calculate_quality(
        self,
        checker_results: List[CheckerResult],
        context: Dict[str, Any]
    ) -> QualityDimension:
        """计算质量维度评分"""
        quality = QualityDimension()

        # 根据检查器结果调整评分
        for result in checker_results:
            if result.checker_type == CheckerType.CHARACTER:
                quality.s2_logic_consistency -= (100 - result.score) * 0.05
                quality.s7_protagonist_charm -= (100 - result.score) * 0.05
            elif result.checker_type == CheckerType.TIMELINE:
                quality.s2_logic_consistency -= (100 - result.score) * 0.05
                quality.s5_pacing_control -= (100 - result.score) * 0.03
            elif result.checker_type == CheckerType.ABILITY:
                quality.s2_logic_consistency -= (100 - result.score) * 0.05
            elif result.checker_type == CheckerType.AI_GLOSS:
                quality.s3_writing_style -= (100 - result.score) * 0.03

        # 确保评分在有效范围内
        def clamp(val):
            return max(1, min(5, val))

        return QualityDimension(
            s1_plot_completeness=clamp(quality.s1_plot_completeness),
            s2_logic_consistency=clamp(quality.s2_logic_consistency),
            s3_writing_style=clamp(quality.s3_writing_style),
            s4_emotional_resonance=clamp(quality.s4_emotional_resonance),
            s5_pacing_control=clamp(quality.s5_pacing_control),
            s6_readability=clamp(quality.s6_readability),
            s7_protagonist_charm=clamp(quality.s7_protagonist_charm),
            s8_character_arc=clamp(quality.s8_character_arc),
        )

    def _calculate_total_score(self, report: ConsistencyReport) -> float:
        """计算总分"""
        base_score = 100

        # 根据问题扣分
        p0_penalty = report.p0_count * 30
        p1_penalty = report.p1_count * 15
        p2_penalty = report.p2_count * 3
        p3_penalty = report.p3_count * 1

        total_deduction = p0_penalty + p1_penalty + p2_penalty + p3_penalty
        return max(0, base_score - total_deduction)

    def _generate_suggestions(self, report: ConsistencyReport) -> List[str]:
        """生成修改建议"""
        suggestions = []

        # 根据问题生成建议
        for issue in report.issues[:10]:  # 最多10条
            if issue.suggestion:
                suggestions.append(f"[{issue.checker_type.value}] {issue.suggestion}")

        return suggestions


__all__ = ["ConsistencyEngineScoringMixin"]