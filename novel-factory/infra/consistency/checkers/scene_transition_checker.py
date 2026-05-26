#!/usr/bin/env python3
"""
场景转换检测器 - 检测场景转换问题

评估标准：
- 场景转换应有过渡
- 时间/空间跳跃应合理
- 不应有突兀的视角切换
"""

import re
from typing import List, Dict, Optional

from .base_checker import BaseChecker
from ..engine.data_structures import Issue, IssueSeverity, IssueLocation, CheckerType


class SceneTransitionChecker(BaseChecker):
    """场景转换检测器"""

    def __init__(self):
        super().__init__(CheckerType.SCENE_PATTERN)

        # 突兀转换标记词
        self.abrupt_markers = [
            "忽然", "突然", "下一秒", "就在这时",
            "刹那间", "一瞬", "瞬间", "眨眼间"
        ]

        # 过渡标记词
        self.transitional_markers = [
            "片刻后", "过了一会儿", "不多时",
            "与此同时", "与此同时", "在这期间",
            "时间流逝", "随着"
        ]

        # 场景变换关键词
        self.scene_change_keywords = [
            "来到", "到达", "前往", "进入",
            "离开", "穿越", "传送", "跳跃"
        ]

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict] = None
    ) -> List[Issue]:
        issues = []

        # 检测突兀转换
        abrupt_transitions = self._find_abrupt_transitions(chapter_content)
        transitional_content = self._has_transitional_content(chapter_content)

        if len(abrupt_transitions) > 5 and not transitional_content:
            issues.append(Issue(
                id=f"scene_transition_{chapter_num}",
                severity=IssueSeverity.P2,
                checker_type=CheckerType.SCENE_PATTERN,
                issue_type="场景转换突兀",
                title="场景转换过于频繁且缺少过渡",
                description=f"章节中{len(abrupt_transitions)}处场景转换缺少过渡",
                location=IssueLocation(chapter=chapter_num),
                evidence="频繁使用突然/忽然等词但无过渡描写"
            ))

        # 检测连续空间跳跃
        if self._has_consecutive_space_jumps(chapter_content):
            issues.append(Issue(
                id=f"space_jump_{chapter_num}",
                severity=IssueSeverity.P2,
                checker_type=CheckerType.SCENE_PATTERN,
                issue_type="空间跳跃过频",
                title="短时间内多次空间跳跃缺乏合理性",
                description="短时间内多次空间跳跃缺乏合理性",
                location=IssueLocation(chapter=chapter_num)
            ))

        return issues

    def _find_abrupt_transitions(self, content: str) -> List[str]:
        """找出所有突兀转换"""
        transitions = []
        for marker in self.abrupt_markers:
            if marker in content:
                transitions.append(marker)
        return transitions

    def _has_transitional_content(self, content: str) -> bool:
        """检测是否有过渡内容"""
        for marker in self.transitional_markers:
            if marker in content:
                return True
        return False

    def _has_consecutive_space_jumps(self, content: str) -> bool:
        """检测是否在短距离内有多次空间跳跃"""
        sentences = content.split('。')
        jump_count = 0

        for sentence in sentences[-15:]:  # 检查最近15句
            if any(kw in sentence for kw in self.scene_change_keywords):
                jump_count += 1

        return jump_count >= 3