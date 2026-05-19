#!/usr/bin/env python3
"""
大纲偏离度检查器

检查章节内容是否偏离既定大纲

检测维度：
1. 情节偏离：章节发生的事件与大纲不符
2. 角色偏离：角色行动与大纲设计不符
3. 节奏偏离：节奏与大纲规划严重不符
"""

from typing import List, Dict, Any, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from consistency.engine.data_structures import Issue, IssueSeverity, CheckerType, IssueLocation
from consistency.checkers.base_checker import BaseChecker


class OutlineChecker(BaseChecker):
    """大纲偏离度检查器"""

    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        super().__init__(CheckerType.OUTLINE)
        self.rules = rules or {}
        self._outline: Dict[str, Any] = {}

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        检查大纲偏离度

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 上下文，包含：
                - outline: Dict 大纲数据
                - chapter_outline: Dict 本章大纲

        Returns:
            Issue列表
        """
        issues = []
        context = context or {}
        outline = context.get("outline", {})
        chapter_outline = context.get("chapter_outline", {})

        self._outline = outline

        # 检查情节偏离
        issues.extend(self._check_plot_alignment(
            chapter_content, chapter_num, chapter_outline
        ))

        # 检查角色偏离
        issues.extend(self._check_character_alignment(
            chapter_content, chapter_num, chapter_outline
        ))

        # 检查节奏偏离
        issues.extend(self._check_pacing_alignment(
            chapter_content, chapter_num, chapter_outline
        ))

        return issues

    def _check_plot_alignment(
        self,
        content: str,
        chapter_num: int,
        chapter_outline: Dict[str, Any]
    ) -> List[Issue]:
        """检查情节偏离"""
        issues = []

        required_plot_points = chapter_outline.get("required_plot_points", [])

        for plot_point in required_plot_points:
            if plot_point not in content:
                issues.append(Issue(
                    id=f"outline_{chapter_num}_情节偏离",
                    severity=IssueSeverity.P1,
                    checker_type=CheckerType.OUTLINE,
                    issue_type="情节偏离",
                    title="大纲要求的情节未出现",
                    description=f"大纲要求本章应包含\"{plot_point}\"，但未在正文中出现",
                    location=IssueLocation(chapter=chapter_num),
                    evidence="大纲要求",
                    suggestion="在正文中加入该情节点",
                    character=None
                ))

        return issues

    def _check_character_alignment(
        self,
        content: str,
        chapter_num: int,
        chapter_outline: Dict[str, Any]
    ) -> List[Issue]:
        """检查角色偏离"""
        issues = []

        required_character_actions = chapter_outline.get("required_character_actions", {})

        for char_name, actions in required_character_actions.items():
            for action in actions:
                if char_name in content and action not in content:
                    issues.append(Issue(
                        id=f"outline_{chapter_num}_{char_name}_角色偏离",
                        severity=IssueSeverity.P2,
                        checker_type=CheckerType.OUTLINE,
                        issue_type="角色行动偏离",
                        title=f"角色{char_name}的行动偏离大纲",
                        description=f"大纲要求{char_name}执行\"{action}\"，但未在正文中出现",
                        location=IssueLocation(chapter=chapter_num),
                        evidence=f"大纲要求：{action}",
                        suggestion="在正文中加入该角色行动",
                        character=char_name
                    ))

        return issues

    def _check_pacing_alignment(
        self,
        content: str,
        chapter_num: int,
        chapter_outline: Dict[str, Any]
    ) -> List[Issue]:
        """检查节奏偏离"""
        issues = []

        expected_pacing = chapter_outline.get("expected_pacing", "normal")
        actual_word_count = len(content)

        # 根据预期节奏检查字数
        if expected_pacing == "slow" and actual_word_count > 5000:
            issues.append(Issue(
                id=f"outline_{chapter_num}_节奏偏离",
                severity=IssueSeverity.P2,
                checker_type=CheckerType.OUTLINE,
                issue_type="节奏偏离",
                title="节奏过慢",
                description="大纲规划本章节奏较慢，但实际字数超过5000字",
                location=IssueLocation(chapter=chapter_num),
                evidence=f"实际字数：{actual_word_count}",
                suggestion="检查是否有过多的背景描写或支线内容",
                character=None
            ))
        elif expected_pacing == "fast" and actual_word_count < 2000:
            issues.append(Issue(
                id=f"outline_{chapter_num}_节奏偏离",
                severity=IssueSeverity.P2,
                checker_type=CheckerType.OUTLINE,
                issue_type="节奏偏离",
                title="节奏过快",
                description="大纲规划本章节奏较快，但实际字数不足2000字",
                location=IssueLocation(chapter=chapter_num),
                evidence=f"实际字数：{actual_word_count}",
                suggestion="检查是否缺少必要的情节推进",
                character=None
            ))

        return issues

    def set_outline(self, outline: Dict[str, Any]):
        """设置大纲"""
        self._outline = outline

    def get_outline(self) -> Dict[str, Any]:
        """获取大纲"""
        return self._outline

    def check_realtime(self, text: str, **kwargs) -> List[Issue]:
        """实时检查（简化版）"""
        return []