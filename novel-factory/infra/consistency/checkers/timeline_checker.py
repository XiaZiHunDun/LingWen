#!/usr/bin/env python3
"""
时间线合理性检查器

检查时间线表达、时间流逝是否合理

检测维度：
1. 时间表达一致性：前文与本文时间描述矛盾
2. 时间流逝矛盾：一天内事件超过24小时
3. 历史记忆矛盾：回忆未发生的事件
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from ..engine.data_structures import Issue, IssueSeverity, CheckerType, IssueLocation
from .base_checker import BaseChecker


@dataclass
class TimelinePoint:
    """时间点"""
    chapter: int
    time_expr: str  # 原始时间表达
    parsed_time: str  # 解析后时间
    relative_day: int  # 相对天数
    is_distorted_time: bool = False  # 是否是扭曲时间（修真/游戏/梦境场景）


class TimelineChecker(BaseChecker):
    """时间线合理性检查器"""
    _checker_type = CheckerType.TIMELINE


    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        super().__init__(self._checker_type)
        self.rules = rules or {}
        self._timeline: List[TimelinePoint] = []

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        检查时间线合理性

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 上下文，包含：
                - timeline: List[TimelinePoint] 已有时间线
                - previous_summary: str 前文摘要

        Returns:
            Issue列表
        """
        issues = []
        context = context or {}

        # 提取本章时间表达
        time_exprs = self._extract_time_expressions(chapter_content)
        for time_expr in time_exprs:
            parsed = self._parse_time_expr(time_expr, chapter_num)

            # 检查与前文矛盾
            issues.extend(self._check_time_conflicts(
                parsed, chapter_num, context.get("timeline", [])
            ))

            # 记录时间点
            self._timeline.append(parsed)

        # 检查时间流逝合理性
        issues.extend(self._check_time_flow(chapter_content, chapter_num))

        return issues

    def _extract_time_expressions(self, content: str) -> List[str]:
        """提取时间表达"""
        patterns = [
            # 基础天数表达
            r"第\d+天",
            r"次日",
            r"前一日",
            r"三天后",
            r"三天前",
            r"一周后",
            r"数日后",
            # 模糊时间表达（修真世界常用）
            r"良久",
            r"片刻之后",
            r"不久",
            r"与此同时",
            r"同一时刻",
            r"夜幕降临",
            r"旭日东升",
            r"正午时分",
            r"深夜",
            # 长时间表达 - 需要特殊处理（可能跨越大量章节）
            r"百年后",
            r"千年后",
            r"百年之前",
            r"千年之前",
            r"数百年后",
            r"数千年后",
            r"弹指间",
            r"瞬息之间",
            r"一晃[数天]?[多月]?",
            r"匆匆[数月]?[多年]?",
            r"光阴似箭",
            r"日月如梭",
            r"斗转星移",
            r"星移斗转",
            # 修行相关时间表达
            r"修炼了?\d+年",
            r"修行了?\d+年",
            r"闭关[数月]?[多年]?",
            r"沉睡[数月]?[多年]?",
            r"长眠[数月]?[多年]?",
            # 特殊场景时间（游戏/梦境）
            r"游戏中?[的]?时间",
            r"意识空间",
            r"梦境中",
        ]

        time_exprs = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            time_exprs.extend(matches)

        return time_exprs

    def _parse_time_expr(self, expr: str, chapter: int) -> TimelinePoint:
        """解析时间表达"""
        relative_day = 0
        is_distorted_time = False  # 是否是扭曲时间（修真/游戏/梦境场景）

        # 检查是否是扭曲时间表达
        distorted_patterns = ["百年", "千年", "数百年", "数千年", "弹指间", "瞬息", "一晃", "匆匆",
                           "光阴似箭", "日月如梭", "斗转星移", "星移斗转", "闭关", "沉睡", "长眠",
                           "游戏中", "意识空间", "梦境"]
        if any(p in expr for p in distorted_patterns):
            is_distorted_time = True
            # 这些时间表达跨度太大，不做增量计算
            relative_day = 0

        if "第" in expr and "天" in expr:
            match = re.search(r"第(\d+)天", expr)
            if match:
                relative_day = int(match.group(1))
        elif "次日" in expr or "第二日" in expr:
            relative_day = 1
        elif "前一日" in expr or "前一天" in expr:
            relative_day = -1
        elif "后" in expr:
            match = re.search(r"(\d+)天后", expr)
            if match:
                relative_day = int(match.group(1))

        return TimelinePoint(
            chapter=chapter,
            time_expr=expr,
            parsed_time=expr,
            relative_day=relative_day,
            is_distorted_time=is_distorted_time
        )

    def _check_time_conflicts(
        self,
        current_point: TimelinePoint,
        chapter_num: int,
        existing_timeline: List[TimelinePoint]
    ) -> List[Issue]:
        """检查时间冲突"""
        issues = []

        # 扭曲时间（如百年后、千年后）不做时间线冲突检查
        if current_point.is_distorted_time:
            return issues

        for point in existing_timeline:
            # 检查同一章节内的时间矛盾
            if point.chapter == chapter_num:
                if (point.relative_day > 0 and current_point.relative_day == 0) or \
                   (point.relative_day == 0 and current_point.relative_day > 0):
                    if "次日" in current_point.time_expr and "天" in point.time_expr:
                        issues.append(Issue(
                            id=f"timeline_{chapter_num}_时间矛盾",
                            severity=IssueSeverity.P1,
                            checker_type=CheckerType.TIMELINE,
                            issue_type="时间表达冲突",
                            title="时间线矛盾",
                            description=f"前文说\"{point.time_expr}\"，这里却说\"{current_point.time_expr}\"",
                            location=IssueLocation(chapter=chapter_num),
                            evidence=f"前文：{point.time_expr}",
                            suggestion="统一时间表达",
                            character=None
                        ))

        return issues

    def _check_time_flow(self, content: str, chapter_num: int) -> List[Issue]:
        """检查时间流逝"""
        issues = []

        # 检测"一天内发生太多事件"的模式
        day_pattern = r"这一?天|当天|同一日"
        if re.search(day_pattern, content):
            event_count = content.count("。")
            if event_count > 50:  # 超过50句，暗示时间可能不够
                # 进一步检查是否有明显的时间跳跃表达
                if not any(kw in content for kw in ["转天", "第二天", "次日"]):
                    issues.append(Issue(
                        id=f"timeline_{chapter_num}_时间流逝",
                        severity=IssueSeverity.P2,
                        checker_type=CheckerType.TIMELINE,
                        issue_type="时间流逝矛盾",
                        title="事件密度过高",
                        description="章节内事件密度较高，可能存在时间流逝不合理的问题",
                        location=IssueLocation(chapter=chapter_num),
                        evidence=f"章节句数：{event_count}",
                        suggestion="检查事件时间安排是否合理",
                        character=None
                    ))

        return issues

    def check_realtime(self, text: str, **kwargs) -> List[Issue]:
        """实时检查（简化版）"""
        return []

    def get_timeline(self) -> List[TimelinePoint]:
        """获取时间线"""
        return self._timeline

    def reset_timeline(self):
        """重置时间线"""
        self._timeline = []