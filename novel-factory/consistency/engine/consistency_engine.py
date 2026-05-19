#!/usr/bin/env python3
"""
一致性引擎主类

整合所有检查器，提供统一的一致性检查接口
"""

import time
from typing import List, Dict, Any, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from consistency.engine.data_structures import (
    Issue, ConsistencyReport, CheckerResult, QualityDimension,
    CheckScope, IssueSeverity, CheckerType
)
from consistency.engine.report_generator import ReportGenerator
from consistency.checkers.character_checker import CharacterChecker
from consistency.checkers.item_checker import ItemChecker
from consistency.checkers.timeline_checker import TimelineChecker
from consistency.checkers.ability_checker import AbilityChecker
from consistency.checkers.personality_checker import PersonalityChecker
from consistency.checkers.foreshadow_checker import ForeshadowChecker
from consistency.checkers.outline_checker import OutlineChecker
from consistency.checkers.ai_gloss_checker import AIGlossChecker


class ConsistencyEngine:
    """
    一致性引擎

    整合8个检查器，提供统一的一致性检查接口

    Usage:
        engine = ConsistencyEngine()
        report = engine.check_chapter(
            chapter_num=25,
            chapter_content="章节内容...",
            context={"character_profiles": [...]}
        )
    """

    def __init__(
        self,
        config_dir: Optional[str] = None,
        scope: CheckScope = CheckScope.ALL
    ):
        """
        初始化一致性引擎

        Args:
            config_dir: 配置文件目录
            scope: 默认检查范围
        """
        self.scope = scope
        self.checkers = self._init_checkers()
        self.report_generator = ReportGenerator()

    def _init_checkers(self) -> Dict[CheckerType, Any]:
        """初始化所有检查器"""
        return {
            CheckerType.CHARACTER: CharacterChecker(),
            CheckerType.ITEM: ItemChecker(),
            CheckerType.TIMELINE: TimelineChecker(),
            CheckerType.ABILITY: AbilityChecker(),
            CheckerType.PERSONALITY: PersonalityChecker(),
            CheckerType.FORESHADOW: ForeshadowChecker(),
            CheckerType.OUTLINE: OutlineChecker(),
            CheckerType.AI_GLOSS: AIGlossChecker(),
        }

    def check_chapter(
        self,
        chapter_num: int,
        chapter_content: str,
        scope: Optional[CheckScope] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ConsistencyReport:
        """
        检查章节一致性

        Args:
            chapter_num: 章节号
            chapter_content: 章节内容
            scope: 检查范围（默认使用引擎初始化时的范围）
            context: 上下文信息，包含：
                - character_profiles: 角色设定列表
                - item_history: 物品状态历史
                - timeline: 时间线
                - plot_threads: 伏笔列表
                - outline: 大纲

        Returns:
            ConsistencyReport: 一致性检查报告
        """
        context = context or {}
        scope = scope or self.scope

        report = ConsistencyReport(
            chapter=chapter_num,
            check_scope=scope,
            metadata={
                "content_length": len(chapter_content),
                "checker_count": len(self.checkers)
            }
        )

        # 确定要运行的检查器
        checkers_to_run = self._get_checkers_for_scope(scope)

        # 运行各项检查
        for checker_type in checkers_to_run:
            checker = self.checkers.get(checker_type)
            if checker is None:
                continue

            start_time = time.time()
            issues = self._run_checker(
                checker, chapter_content, chapter_num, context
            )
            duration = (time.time() - start_time) * 1000  # 毫秒

            # 计算检查器得分
            checker_result = self._calculate_checker_result(
                checker_type, issues, duration
            )
            report.checker_results.append(checker_result)
            report.issues.extend(issues)

        # 计算质量维度评分
        report.quality = self._calculate_quality(report.checker_results, context)

        # 计算总分
        report.total_score = self._calculate_total_score(report)

        # 生成判定
        report.make_verdict()

        # 生成建议
        report.suggestions = self._generate_suggestions(report)

        return report

    def _run_checker(
        self,
        checker: Any,
        chapter_content: str,
        chapter_num: int,
        context: Dict[str, Any]
    ) -> List[Issue]:
        """运行单个检查器"""
        try:
            return checker.check(
                chapter_content=chapter_content,
                chapter_num=chapter_num,
                context=context
            )
        except Exception as e:
            # 检查器出错时返回空列表，记录日志
            print(f"Checker {checker.get_checker_type()} failed: {e}")
            return []

    def _get_checkers_for_scope(self, scope: CheckScope) -> List[CheckerType]:
        """根据检查范围获取要运行的检查器"""
        if scope == CheckScope.ALL:
            return list(CheckerType)
        elif scope == CheckScope.CRITICAL:
            return [CheckerType.CHARACTER, CheckerType.ABILITY]
        elif scope == CheckScope.IMPORTANT:
            return [
                CheckerType.CHARACTER, CheckerType.ABILITY,
                CheckerType.TIMELINE, CheckerType.ITEM, CheckerType.OUTLINE
            ]
        elif scope == CheckScope.STANDARD:
            return [
                CheckerType.CHARACTER, CheckerType.ITEM,
                CheckerType.TIMELINE, CheckerType.ABILITY,
                CheckerType.PERSONALITY, CheckerType.FORESHADOW
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

    def realtime_check(
        self,
        content: str,
        character: Optional[str] = None
    ) -> List[Issue]:
        """
        实时检查（轻量级）

        用于写作过程中即时预警

        Args:
            content: 待检查文本
            character: 指定角色名

        Returns:
            实时问题列表
        """
        issues = []

        # 只运行轻量级检查
        ai_checker = self.checkers.get(CheckerType.AI_GLOSS)
        if ai_checker:
            issues.extend(ai_checker.check_realtime(content))

        character_checker = self.checkers.get(CheckerType.CHARACTER)
        if character_checker:
            issues.extend(character_checker.check_realtime(content, character))

        return issues

    def get_checker(self, checker_type: CheckerType) -> Any:
        """获取指定检查器"""
        return self.checkers.get(checker_type)