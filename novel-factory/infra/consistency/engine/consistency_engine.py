#!/usr/bin/env python3
"""
一致性引擎主类

整合所有检查器，提供统一的一致性检查接口
与记忆系统集成，通过 MemoryGateway 获取上下文
"""

import time
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional

from .data_structures import (
    Issue, ConsistencyReport, CheckerResult, QualityDimension,
    CheckScope, IssueSeverity, CheckerType
)
from .checker_inspector import CheckerInspector
from .consistency_arbitrator import ConsistencyArbitrator

# 上下文配置文件路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CONTEXT_DIR = PROJECT_ROOT / "context"
CHARACTER_PROFILES_PATH = CONTEXT_DIR / "character_profiles.yaml"
SCENE_TYPES_PATH = CONTEXT_DIR / "scene_types.yaml"
from .report_generator import ReportGenerator
from ..checkers.character_checker import CharacterChecker
from ..checkers.character_state import CharacterStateChecker
from ..checkers.item_checker import ItemChecker
from ..checkers.timeline_checker import TimelineChecker
from ..checkers.ability_checker import AbilityChecker
from ..checkers.personality_checker import PersonalityChecker
from ..checkers.foreshadow_checker import ForeshadowChecker
from ..checkers.outline_checker import OutlineChecker
from ..checkers.ai_gloss_checker import AIGlossChecker
from ..checkers.scene_pattern_repeat import ScenePatternRepeatChecker
from ..checkers.foreshadow_quality import ForeshadowQualityChecker
from ..checkers.character_agency import CharacterAgencyChecker
from ..checkers.timeline_age import TimelineAgeConsistencyChecker
from ..checkers.battle_visualization import BattleVisualizationChecker


class ConsistencyEngine:
    """
    一致性引擎

    整合8个检查器，提供统一的一致性检查接口
    支持与记忆系统集成，获取角色状态历史、相似情节等上下文

    Usage:
        # Without memory integration
        engine = ConsistencyEngine()
        report = engine.check_chapter(
            chapter_num=25,
            chapter_content="章节内容...",
            context={"character_profiles": [...]}
        )

        # With memory integration
        engine = ConsistencyEngine(memory_gateway=gateway)
        report = engine.check_chapter(
            chapter_num=25,
            chapter_content="章节内容..."
        )
        # Memory data (character states, similar plots) auto-injected into context
    """

    def __init__(
        self,
        config_dir: Optional[str] = None,
        scope: CheckScope = CheckScope.ALL,
        memory_gateway: Optional[Any] = None
    ):
        """
        初始化一致性引擎

        Args:
            config_dir: 配置文件目录
            scope: 默认检查范围
            memory_gateway: MemoryGateway 实例，用于获取记忆上下文
        """
        self.scope = scope
        self.memory_gateway = memory_gateway
        self.checkers = self._init_checkers()
        self.report_generator = ReportGenerator()
        self.checker_inspector = CheckerInspector()
        self.arbitrator = ConsistencyArbitrator()
        self.use_arbitration = True

    def _init_checkers(self) -> Dict[CheckerType, Any]:
        """初始化所有检查器"""
        return {
            CheckerType.CHARACTER: CharacterChecker(),
            CheckerType.CHARACTER_STATE: CharacterStateChecker(),
            CheckerType.ITEM: ItemChecker(),
            CheckerType.TIMELINE: TimelineChecker(),
            CheckerType.ABILITY: AbilityChecker(),
            CheckerType.PERSONALITY: PersonalityChecker(),
            CheckerType.FORESHADOW: ForeshadowChecker(),
            CheckerType.OUTLINE: OutlineChecker(),
            CheckerType.AI_GLOSS: AIGlossChecker(),
            CheckerType.SCENE_PATTERN: ScenePatternRepeatChecker(),
            CheckerType.FORESHADOW_QUALITY: ForeshadowQualityChecker(),
            CheckerType.CHARACTER_AGENCY: CharacterAgencyChecker(),
            CheckerType.TIMELINE_AGE: TimelineAgeConsistencyChecker(),
            CheckerType.BATTLE_VISUALIZATION: BattleVisualizationChecker(),
        }

    def _enrich_context_from_memory(
        self,
        chapter_num: int,
        chapter_content: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        从记忆系统获取上下文并 enriched context

        获取以下信息：
        1. 角色状态历史（从 CharacterTracker）
        2. 相似情节段落（通过向量检索）

        Args:
            chapter_num: 章节号
            chapter_content: 章节内容
            context: 已有上下文

        Returns:
            丰富后的上下文字典
        """
        if self.memory_gateway is None:
            return context

        enriched = context.copy()

        # 1. 获取角色状态历史
        if "character_states" not in enriched:
            enriched["character_states"] = {}

        all_characters = self.memory_gateway.get_all_characters()
        if all_characters:
            enriched["character_states"] = all_characters

        # 2. 获取待回收伏笔
        if "pending_foreshadows" not in enriched:
            pending_foreshadows = self.memory_gateway.get_pending_foreshadows()
            enriched["pending_foreshadows"] = pending_foreshadows

        # 3. 通过向量检索查找相似情节
        if "similar_segments" not in enriched:
            similar_segments = self._find_similar_plots(chapter_content)
            enriched["similar_segments"] = similar_segments

        # 4. 获取自动推送上下文（包含角色状态、伏笔、最近事件等）
        auto_context = self.memory_gateway.auto_push_context(chapter_num)
        if auto_context:
            # 合并到 enriched 中，但不覆盖已有数据
            for key, value in auto_context.items():
                # 只在key不存在或值为None时覆盖，空列表/空dict是有效值
                if key not in enriched or enriched[key] is None:
                    enriched[key] = value

        # 5. 加载角色档案（用于 CharacterChecker 置信度计算）
        if "character_profiles" not in enriched:
            enriched["character_profiles"] = self._load_character_profiles()

        # 6. 加载场景类型（用于 TimelineChecker 误报规避）
        if "scene_type" not in enriched:
            enriched["scene_type"] = self._get_scene_type(chapter_num)

        return enriched

    def _inject_scene_and_age_context(
        self,
        chapter_num: int,
        chapter_content: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        注入场景标签和角色年龄上下文

        Args:
            chapter_num: 章节号
            chapter_content: 章节内容
            context: 已有上下文

        Returns:
            注入后的上下文
        """
        enriched = context.copy()

        # 获取场景类型（用于白名单判断）
        if "scene_type" not in enriched:
            enriched["scene_type"] = self._get_scene_type(chapter_num)

        # 获取前三章场景标签（用于ScenePatternRepeatChecker）
        if "recent_scene_labels" not in enriched:
            enriched["recent_scene_labels"] = []

        # 检测当前章节场景标签
        current_label = self._detect_current_scene_label(chapter_content)
        if current_label:
            recent_labels = enriched["recent_scene_labels"]
            # 添加当前标签到历史
            enriched["recent_scene_labels"] = recent_labels[-2:] + [current_label] if recent_labels else [current_label]

        # 获取角色年龄上下文（用于TimelineAgeConsistencyChecker）
        if "character_ages" not in enriched:
            enriched["character_ages"] = self._get_character_ages_context(chapter_num, enriched)

        return enriched

    def _detect_current_scene_label(self, content: str) -> Optional[str]:
        """检测当前章节的场景标签"""
        from ..checkers.scene_pattern_repeat import ScenePatternRepeatChecker
        checker = ScenePatternRepeatChecker()
        return checker.get_scene_label(content)

    def _get_character_ages_context(
        self,
        chapter_num: int,
        context: Dict[str, Any]
    ) -> Dict[str, Dict[int, int]]:
        """获取角色年龄上下文"""
        # 从context或记忆系统获取角色年龄历史
        if "character_ages" in context:
            return context["character_ages"]

        # 默认返回林夜的关键年龄节点
        return {
            "林夜": {1: 7, 24: 22}
        }

    def _load_character_profiles(self) -> Dict[str, Any]:
        """加载角色档案"""
        if not CHARACTER_PROFILES_PATH.exists():
            return {}
        try:
            with open(CHARACTER_PROFILES_PATH, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data.get("characters", {})
        except Exception:
            return {}

    def _get_scene_type(self, chapter_num: int) -> Dict[str, Any]:
        """获取章节场景类型"""
        if not SCENE_TYPES_PATH.exists():
            return {}
        try:
            with open(SCENE_TYPES_PATH, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                scene_registry = data.get("scene_registry", {})
                ch_key = f"ch{chapter_num:03d}"
                return scene_registry.get(ch_key, {})
        except Exception:
            return {}

    def _find_similar_plots(
        self,
        chapter_content: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        通过向量检索查找相似情节

        Args:
            chapter_content: 章节内容
            top_k: 返回的最相似情节数量

        Returns:
            相似情节列表
        """
        if self.memory_gateway is None:
            return []

        try:
            # 使用记忆系统的 query 功能进行向量检索
            # 提取章节内容的摘要作为查询
            query = self._extract_plot_query(chapter_content)
            if not query:
                return []

            results = self.memory_gateway.query(
                query=query,
                scope="all",
                top_k=top_k
            )
            return results
        except Exception:
            return []

    def _extract_plot_query(self, content: str) -> str:
        """
        从章节内容中提取用于向量检索的查询字符串

        提取策略：
        1. 取前200字符作为主要情节描述
        2. 去除语气词和描述性文字，保留核心事件

        Args:
            content: 章节内容

        Returns:
            查询字符串
        """
        # 简单策略：取前200字符，去除多余空白
        query = content[:200].strip()
        # 去除多余空白
        query = " ".join(query.split())
        return query

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
                - recent_scene_labels: 前三章场景标签列表
                - character_ages: 角色年龄历史

        Returns:
            ConsistencyReport: 一致性检查报告
        """
        context = context or {}
        scope = scope or self.scope

        # 如果有记忆网关，先从记忆系统获取上下文
        if self.memory_gateway is not None:
            context = self._enrich_context_from_memory(
                chapter_num, chapter_content, context
            )

        # 注入场景标签和角色年龄上下文
        context = self._inject_scene_and_age_context(chapter_num, chapter_content, context)

        report = ConsistencyReport(
            chapter=chapter_num,
            check_scope=scope,
            metadata={
                "content_length": len(chapter_content),
                "checker_count": len(self.checkers),
                "memory_enriched": self.memory_gateway is not None
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

        # 仲裁过滤：如果开启了仲裁且有问题
        if issues and self.use_arbitration:
            arbitration_result = self.arbitrator.arbitrate(issues)
            filtered_issues = arbitration_result.resolved_issues
            # 使用仲裁后过滤的问题列表更新report
            report.issues = filtered_issues

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
        """运行单个检查器（集成白名单机制）"""
        try:
            # 使用 check_with_whitelist 方法集成白名单机制
            return checker.check_with_whitelist(
                chapter_content=chapter_content,
                chapter_num=chapter_num,
                context=context
            )
        except Exception as e:
            # 检查器出错时返回空列表，记录日志
            logger.error(f"Checker {checker.get_checker_type()} failed: {e}")
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
            issues.extend(character_checker.check_realtime(content, character=character))

        return issues

    def get_checker(self, checker_type: CheckerType) -> Any:
        """获取指定检查器"""
        return self.checkers.get(checker_type)

    def get_character_state_from_memory(
        self,
        character: str
    ) -> Optional[Dict[str, Any]]:
        """
        从记忆系统获取角色状态

        Args:
            character: 角色名称

        Returns:
            角色状态字典，如果角色不存在或无记忆系统则返回 None
        """
        if self.memory_gateway is None:
            return None

        return self.memory_gateway.get_character_state(character)

    def query_similar_plots(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        查询相似情节

        Args:
            query: 查询字符串
            top_k: 返回结果数量

        Returns:
            相似情节列表
        """
        if self.memory_gateway is None:
            return []

        return self.memory_gateway.query(query=query, scope="all", top_k=top_k)