#!/usr/bin/env python3
"""
一致性引擎主类

整合所有检查器，提供统一的一致性检查接口
与记忆系统集成，通过 MemoryGateway 获取上下文
"""

import logging
import time
from typing import Any, Dict, List, Optional

from ..checkers.base_checker import CheckerRegistry
from .checker_inspector import CheckerInspector
from .consistency_arbitrator import ConsistencyArbitrator
from .consistency_engine_context import ConsistencyEngineContextMixin
from .consistency_engine_scoring import ConsistencyEngineScoringMixin
from .data_structures import (
    CheckerType,
    CheckScope,
    ConsistencyReport,
    Issue,
)
from .report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class ConsistencyEngine(
    ConsistencyEngineContextMixin,
    ConsistencyEngineScoringMixin,
):
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
        """初始化所有检查器（从 CheckerRegistry 自动加载）"""
        return CheckerRegistry.instantiate_all()

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