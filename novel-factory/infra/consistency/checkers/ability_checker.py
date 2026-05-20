#!/usr/bin/env python3
"""
能力一致性检查器

检查角色能力使用是否与设定一致

检测维度：
1. 能力使用冲突：不会武功的角色使用武功
2. 能力强度矛盾：能力突然变强/变弱无合理解释
3. 学习曲线矛盾：刚学的能力就能熟练使用
"""

from typing import List, Dict, Any, Optional

from ..engine.data_structures import Issue, IssueSeverity, CheckerType, IssueLocation
from .base_checker import BaseChecker


class AbilityChecker(BaseChecker):
    """能力一致性检查器"""

    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        super().__init__(CheckerType.ABILITY)
        self.rules = rules or {}
        self._ability_log: Dict[str, List[str]] = {}  # 角色 -> 能力使用记录

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        检查能力一致性

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 上下文，包含：
                - character_abilities: Dict[str, List[str]] 角色能力列表
                - ability_boundaries: Dict[str, Dict] 能力边界设定

        Returns:
            Issue列表
        """
        issues = []
        context = context or {}
        character_abilities = context.get("character_abilities", {})

        # 检查能力使用冲突
        issues.extend(self._check_ability_usage(
            chapter_content, chapter_num, character_abilities
        ))

        # 检查能力强度矛盾
        issues.extend(self._check_ability_strength(
            chapter_content, chapter_num, character_abilities
        ))

        # 检查学习曲线
        issues.extend(self._check_learning_curve(
            chapter_content, chapter_num, character_abilities
        ))

        return issues

    def _check_ability_usage(
        self,
        content: str,
        chapter_num: int,
        character_abilities: Dict[str, List[str]]
    ) -> List[Issue]:
        """检查能力使用冲突"""
        issues = []

        # 定义能力冲突规则
        conflicts = {
            "不会武": ["舞剑", "出招", "运功", "内力", "真气", "灵力"],
            "不识字": ["阅读", "看书", "写字", "辨认文字"],
            "不懂医": ["诊治", "诊断", "开方", "把脉"],
            "不懂阵法": ["布阵", "破阵", "阵法", "阵眼"],
        }

        for char_name, abilities in character_abilities.items():
            for limit, triggers in conflicts.items():
                if limit in abilities:
                    for trigger in triggers:
                        if trigger in content and char_name in content:
                            issues.append(Issue(
                                id=f"ability_{chapter_num}_{char_name}_使用冲突",
                                severity=IssueSeverity.P1,
                                checker_type=CheckerType.ABILITY,
                                issue_type="能力使用冲突",
                                title=f"能力与行为冲突",
                                description=f"角色{char_name}设定为\"{limit}\"，但执行了\"{trigger}\"",
                                location=IssueLocation(chapter=chapter_num),
                                evidence=f"角色设定：{limit}",
                                suggestion=f"修改行为或补充角色学习经过",
                                character=char_name
                            ))

        return issues

    def _check_ability_strength(
        self,
        content: str,
        chapter_num: int,
        character_abilities: Dict[str, List[str]]
    ) -> List[Issue]:
        """检查能力强度矛盾"""
        issues = []

        # 检测能力突然变强的模式
        strength_patterns = [
            (r"突然.*实力大涨", "实力突然提升"),
            (r"瞬间.*突破", "瞬间突破"),
            (r"毫无征兆.*爆发", "无预警爆发"),
        ]

        for char_name in character_abilities.keys():
            for pattern, desc in strength_patterns:
                if char_name in content:
                    import re
                    if re.search(pattern, content):
                        issues.append(Issue(
                            id=f"ability_{chapter_num}_{char_name}_强度矛盾",
                            severity=IssueSeverity.P2,
                            checker_type=CheckerType.ABILITY,
                            issue_type="能力强度矛盾",
                            title=f"能力强度突变",
                            description=f"角色{char_name}的能力出现突然变化（{desc}），缺乏铺垫",
                            location=IssueLocation(chapter=chapter_num),
                            evidence=f"文本描述：{desc}",
                            suggestion="补充能力变化的合理原因或过渡描写",
                            character=char_name
                        ))

        return issues

    def _check_learning_curve(
        self,
        content: str,
        chapter_num: int,
        character_abilities: Dict[str, List[str]]
    ) -> List[Issue]:
        """检查学习曲线矛盾"""
        issues = []

        # 检测"刚学就熟练使用"的模式
        learning_patterns = [
            r"刚刚学会.*(立刻|马上|随即).*(使用|施展|运用)",
            r"第一次.*(使用|施展).*(就|竟然)",
        ]

        for char_name in character_abilities.keys():
            for pattern in learning_patterns:
                import re
                if re.search(pattern, content) and char_name in content:
                    issues.append(Issue(
                        id=f"ability_{chapter_num}_{char_name}_学习曲线",
                        severity=IssueSeverity.P2,
                        checker_type=CheckerType.ABILITY,
                        issue_type="学习曲线矛盾",
                        title="能力学习缺乏过渡",
                        description=f"角色{char_name}刚学习的能力就被熟练使用",
                        location=IssueLocation(chapter=chapter_num),
                        evidence="刚学就熟练使用",
                        suggestion="增加学习过程的描写或说明学习背景",
                        character=char_name
                    ))

        return issues

    def check_realtime(self, text: str, **kwargs) -> List[Issue]:
        """实时检查（简化版）"""
        return []