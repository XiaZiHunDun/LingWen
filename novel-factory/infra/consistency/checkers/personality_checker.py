#!/usr/bin/env python3
"""
人设稳定性检查器

检查角色**跨章节**的行为动机一致性。

注意 (R2-004)：
"核心性格变化"检测已从本类移除 — 与 character_checker.py 的
personality_opposites 逻辑重叠。character_checker 用窗口机制做
单章节内反义词检测；本类仅保留**单章节 → 角色目标**的
动机一致性检查（独有功能）。
"""

from typing import Any, Dict, List, Optional

from ..engine.data_structures import CheckerType, Issue, IssueLocation, IssueSeverity
from .base_checker import BaseChecker


class PersonalityChecker(BaseChecker):
    """人设稳定性检查器"""
    _checker_type = CheckerType.PERSONALITY


    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        super().__init__(self._checker_type)
        self.rules = rules or {}
        self._personality_history: Dict[str, List[str]] = {}  # 角色 -> 性格记录

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        检查人设稳定性

        仅保留行为动机一致性检测（与 character_checker 不重叠）。
        核心性格变化检测已迁移到 character_checker (R2-004)。

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 上下文，包含：
                - character_profiles: Dict[str, Dict] 角色设定

        Returns:
            Issue列表
        """
        issues = []
        context = context or {}
        # 兼容两种调用方式：直接传character_profiles列表或通过context字典
        if context and isinstance(context, dict):
            raw_profiles = context.get("character_profiles", {})
            # 支持两种格式：list或{"characters": [...]}
            if isinstance(raw_profiles, list):
                character_profiles = {p.get("name", ""): p for p in raw_profiles}
            elif isinstance(raw_profiles, dict):
                character_profiles = {p.get("name", ""): p for p in raw_profiles.get("characters", [])}
            else:
                character_profiles = {}
        else:
            character_profiles = {}

        # 仅检查行为动机一致性（独有功能，不与 character_checker 重复）
        issues.extend(self._check_motivation_consistency(
            chapter_content, chapter_num, character_profiles
        ))

        return issues

    def _check_motivation_consistency(
        self,
        content: str,
        chapter_num: int,
        character_profiles: Dict[str, Dict]
    ) -> List[Issue]:
        """检查行为动机一致性"""
        issues = []

        for char_name, profile in character_profiles.items():
            goals = profile.get("goals", [])
            current_goal = goals[0] if goals else None

            if not current_goal:
                continue

            # 检测角色做出与目标完全相反的行为
            opposite_actions = {
                "复仇": ["原谅", "放下", "宽恕"],
                "守护": ["放弃", "抛弃", "牺牲"],
                "追求力量": ["拒绝", "放弃修炼"],
                "爱情": ["伤害", "背叛"],
            }

            for goal, opposites in opposite_actions.items():
                if goal in str(current_goal):
                    for opposite in opposites:
                        if opposite in content and char_name in content:
                            issues.append(Issue(
                                id=f"personality_{chapter_num}_{char_name}_动机",
                                severity=IssueSeverity.P2,
                                checker_type=CheckerType.PERSONALITY,
                                issue_type="行为动机不一致",
                                title="行为与目标矛盾",
                                description=f"角色{char_name}的目标是\"{goal}\"，却做出了相反的行为",
                                location=IssueLocation(chapter=chapter_num),
                                evidence=f"目标：{current_goal}",
                                suggestion="补充行为动机或调整目标设定",
                                character=char_name
                            ))

        return issues

    def _check_speech_style_change(
        self,
        content: str,
        chapter_num: int,
        character_profiles: Dict[str, Dict]
    ) -> List[Issue]:
        """检查语言风格变化（简化版）"""
        # 语言风格检查需要NLP，这里做基础检测
        return []

    def check_realtime(self, text: str, **kwargs) -> List[Issue]:
        """实时检查（简化版）"""
        return []
