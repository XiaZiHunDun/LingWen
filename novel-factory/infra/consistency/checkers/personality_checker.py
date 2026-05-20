#!/usr/bin/env python3
"""
人设稳定性检查器

检查角色核心性格、行为动机、语言风格是否稳定

检测维度：
1. 核心性格变化：性格发生重大变化无过渡
2. 行为动机不一致：行为与角色目标不符
3. 语言风格变化：角色说话方式突然改变
"""

from typing import List, Dict, Any, Optional

from consistency.engine.data_structures import Issue, IssueSeverity, CheckerType, IssueLocation
from consistency.checkers.base_checker import BaseChecker


class PersonalityChecker(BaseChecker):
    """人设稳定性检查器"""

    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        super().__init__(CheckerType.PERSONALITY)
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
        character_profiles = context.get("character_profiles", {})

        # 检查核心性格变化
        issues.extend(self._check_personality_change(
            chapter_content, chapter_num, character_profiles
        ))

        # 检查行为动机一致性
        issues.extend(self._check_motivation_consistency(
            chapter_content, chapter_num, character_profiles
        ))

        # 检查语言风格一致性
        issues.extend(self._check_speech_style_change(
            chapter_content, chapter_num, character_profiles
        ))

        return issues

    def _check_personality_change(
        self,
        content: str,
        chapter_num: int,
        character_profiles: Dict[str, Dict]
    ) -> List[Issue]:
        """检查核心性格变化"""
        issues = []

        # 定义重大性格转变的反义词对
        major_opposites = {
            "善良": ["邪恶", "狠毒", "残忍"],
            "正直": ["奸诈", "阴险", "虚伪"],
            "信任": ["怀疑", "猜忌"],
            "勇敢": ["怯懦", "胆小"],
            "乐观": ["悲观", "消沉"],
        }

        for char_name, profile in character_profiles.items():
            core_personality = profile.get("core_personality", [])
            speech_style = profile.get("speech_style", "")

            for personality in core_personality:
                opposites = major_opposites.get(personality, [])
                for opposite in opposites:
                    if opposite in content:
                        # 检查是否有转变铺垫
                        transition_keywords = ["变得", "转变为", "终于", "最终"]
                        has_transition = any(kw in content for kw in transition_keywords)

                        if not has_transition:
                            issues.append(Issue(
                                id=f"personality_{chapter_num}_{char_name}_变化",
                                severity=IssueSeverity.P2,
                                checker_type=CheckerType.PERSONALITY,
                                issue_type="核心性格变化",
                                title=f"人设突然转变",
                                description=f"角色{char_name}的核心性格\"{personality}\"发生变化，缺乏过渡",
                                location=IssueLocation(chapter=chapter_num),
                                evidence=f"出现\"{opposite}\"描述",
                                suggestion="增加性格转变的过渡描写",
                                character=char_name
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
                                title=f"行为与目标矛盾",
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