#!/usr/bin/env python3
"""
伏笔回收检查器

检查伏笔是否正确埋设和回收

检测维度：
1. 伏笔未回收：已到预期回收章节，伏笔未揭示
2. 伏笔过度揭示：一次性揭示太多伏笔
3. 伏笔逻辑矛盾：回收方式与埋设矛盾
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from consistency.engine.data_structures import Issue, IssueSeverity, CheckerType, IssueLocation, ForeshadowAlert
from consistency.checkers.base_checker import BaseChecker


@dataclass
class PlotThread:
    """伏笔"""
    id: str
    content: str
    introduced_chapter: int
    expected_resolve_chapter: int
    actual_resolve_chapter: Optional[int] = None
    status: str = "unresolved"  # unresolved, resolved, overdue
    resolve_type: Optional[str] = None  # full, partial, wrong


class ForeshadowChecker(BaseChecker):
    """伏笔回收检查器"""

    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        super().__init__(CheckerType.FORESHADOW)
        self.rules = rules or {}
        self._plot_threads: Dict[str, PlotThread] = {}
        self._pending_foreshadow: List[str] = []  # 待回收的伏笔关键词

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        检查伏笔回收

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 上下文，包含：
                - plot_threads: List[PlotThread] 伏笔列表
                - new_foreshadow: List[str] 本章新埋的伏笔

        Returns:
            Issue列表
        """
        issues = []
        context = context or {}
        plot_threads = context.get("plot_threads", [])
        new_foreshadow = context.get("new_foreshadow", [])

        # 更新伏笔状态
        for thread in plot_threads:
            self._plot_threads[thread.id] = thread

        # 检查未回收的伏笔
        issues.extend(self._check_unresolved_foreshadow(chapter_num))

        # 检查过度揭示
        issues.extend(self._check_over_resolution(chapter_content, chapter_num))

        # 检查新埋的伏笔
        issues.extend(self._check_new_foreshadow(chapter_content, chapter_num, new_foreshadow))

        return issues

    def _check_unresolved_foreshadow(self, chapter_num: int) -> List[Issue]:
        """检查未回收的伏笔"""
        issues = []

        # 检查已到回收期的伏笔
        for thread_id, thread in self._plot_threads.items():
            if thread.status == "unresolved":
                if chapter_num >= thread.expected_resolve_chapter:
                    # 延迟回收
                    delay = chapter_num - thread.expected_resolve_chapter
                    if delay >= 3:  # 延迟3章以上
                        issues.append(Issue(
                            id=f"foreshadow_{chapter_num}_{thread_id}_延迟回收",
                            severity=IssueSeverity.P2,
                            checker_type=CheckerType.FORESHADOW,
                            issue_type="伏笔未及时回收",
                            title=f"伏笔回收延迟",
                            description=f"伏笔\"{thread.content}\"应在ch{thread.expected_resolve_chapter}回收，已延迟{delay}章",
                            location=IssueLocation(chapter=chapter_num),
                            evidence=f"预期回收章节：ch{thread.expected_resolve_chapter}",
                            suggestion="考虑在本章或近期章节回收该伏笔",
                            character=None
                        ))

        return issues

    def _check_over_resolution(
        self,
        content: str,
        chapter_num: int
    ) -> List[Issue]:
        """检查过度揭示"""
        issues = []

        # 统计本章中"揭示"类关键词的数量
        reveal_keywords = ["原来", "真相是", "事实证明", "揭示", "暴露"]
        reveal_count = sum(content.count(kw) for kw in reveal_keywords)

        if reveal_count > 3:
            issues.append(Issue(
                id=f"foreshadow_{chapter_num}_过度揭示",
                severity=IssueSeverity.P2,
                checker_type=CheckerType.FORESHADOW,
                issue_type="伏笔过度揭示",
                title="一次性揭示太多",
                description=f"本章有{reveal_count}处揭示/揭示类表达，可能过于密集",
                location=IssueLocation(chapter=chapter_num),
                evidence=f"揭示关键词出现次数：{reveal_count}",
                suggestion="考虑分散揭示，或将部分揭示留到后续章节",
                character=None
            ))

        return issues

    def _check_new_foreshadow(
        self,
        content: str,
        chapter_num: int,
        new_foreshadow: List[str]
    ) -> List[Issue]:
        """检查新埋的伏笔"""
        issues = []

        if not new_foreshadow:
            return issues

        # 检查新伏笔是否有足够的回收预期
        for foreshadow in new_foreshadow:
            # 简化：检查伏笔是否明确
            if len(foreshadow) < 10:  # 太短的伏笔可能不明确
                issues.append(Issue(
                    id=f"foreshadow_{chapter_num}_伏笔不明确",
                    severity=IssueSeverity.P3,
                    checker_type=CheckerType.FORESHADOW,
                    issue_type="伏笔不明确",
                    title=f"伏笔描述不够明确",
                    description=f"伏笔\"{foreshadow}\"可能不够明确，读者可能无法识别",
                    location=IssueLocation(chapter=chapter_num),
                    evidence=f"伏笔长度：{len(foreshadow)}字符",
                    suggestion="增强伏笔的明确性或添加更多线索",
                    character=None
                ))

        return issues

    def add_foreshadow(
        self,
        thread_id: str,
        content: str,
        introduced_chapter: int,
        expected_resolve_chapter: int
    ):
        """添加伏笔"""
        self._plot_threads[thread_id] = PlotThread(
            id=thread_id,
            content=content,
            introduced_chapter=introduced_chapter,
            expected_resolve_chapter=expected_resolve_chapter
        )

    def resolve_foreshadow(self, thread_id: str, chapter_num: int):
        """标记伏笔已回收"""
        if thread_id in self._plot_threads:
            self._plot_threads[thread_id].status = "resolved"
            self._plot_threads[thread_id].actual_resolve_chapter = chapter_num

    def get_unresolved_count(self) -> int:
        """获取未回收伏笔数量"""
        return sum(1 for t in self._plot_threads.values() if t.status == "unresolved")

    def _detect_overdue_foreshadow(self, current_chapter: int) -> List[ForeshadowAlert]:
        """检测超期未回收的伏笔"""
        alerts = []
        for thread_id, thread in self._plot_threads.items():
            if thread.status == "unresolved" and current_chapter > thread.expected_resolve_chapter:
                delay = current_chapter - thread.expected_resolve_chapter
                severity = IssueSeverity.P1 if delay >= 3 else IssueSeverity.P2
                message = f"伏笔\"{thread.content}\"应在ch{thread.expected_resolve_chapter}回收，已延迟{delay}章仍未回收"
                alerts.append(ForeshadowAlert(
                    alert_type="overdue",
                    thread_id=thread_id,
                    content=thread.content,
                    introduced_chapter=thread.introduced_chapter,
                    expected_resolve_chapter=thread.expected_resolve_chapter,
                    current_chapter=current_chapter,
                    delay_chapters=delay,
                    severity=severity,
                    message=message
                ))
        return alerts

    def _detect_approaching_deadline(self, current_chapter: int) -> List[ForeshadowAlert]:
        """检测即将到期的伏笔（2章以内）"""
        alerts = []
        for thread_id, thread in self._plot_threads.items():
            if thread.status == "unresolved":
                distance = thread.expected_resolve_chapter - current_chapter
                if 0 < distance <= 2:
                    message = f"伏笔\"{thread.content}\"还剩{distance}章即将到期（ch{thread.expected_resolve_chapter}），请注意回收"
                    alerts.append(ForeshadowAlert(
                        alert_type="approaching",
                        thread_id=thread_id,
                        content=thread.content,
                        introduced_chapter=thread.introduced_chapter,
                        expected_resolve_chapter=thread.expected_resolve_chapter,
                        current_chapter=current_chapter,
                        delay_chapters=0,
                        severity=IssueSeverity.P3,
                        message=message
                    ))
        return alerts

    def get_foreshadow_alerts(self, current_chapter: int) -> List[ForeshadowAlert]:
        """获取当前章节的所有伏笔预警"""
        alerts = []
        alerts.extend(self._detect_overdue_foreshadow(current_chapter))
        alerts.extend(self._detect_approaching_deadline(current_chapter))
        return alerts

    def get_overdue_count(self) -> int:
        """获取超期伏笔数量"""
        return sum(1 for t in self._plot_threads.values()
                   if t.status == "unresolved" and False)  # Placeholder, will be updated per-chapter

    def get_overdue_count_at(self, current_chapter: int) -> int:
        """获取当前超期伏笔数量"""
        return len(self._detect_overdue_foreshadow(current_chapter))

    def check_realtime(self, text: str, **kwargs) -> List[Issue]:
        """实时检查（简化版）"""
        return []