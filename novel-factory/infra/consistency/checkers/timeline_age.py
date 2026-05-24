#!/usr/bin/env python3
"""
时间线年龄一致性检测器

检测角色年龄时间线的矛盾问题
评分标准（S2逻辑自洽）：
- 优秀: 年龄时间线一致，无矛盾
- 触发P0: 年龄计算矛盾（如22岁章节出现"十岁那年"）
"""

import re
from typing import List, Optional, Dict, Any

from .base_checker import BaseChecker
from ..engine.data_structures import Issue, IssueLocation, IssueSeverity, CheckerType


class TimelineAgeConsistencyChecker(BaseChecker):
    """
    时间线年龄一致性检测器

    检测角色年龄时间线的矛盾，包括：
    - 当前年龄与描述矛盾
    - 年龄计算错误（生存时间不一致）
    - "X岁那年"与当前年龄矛盾
    """

    # 林夜年龄时间线关键节点
    LINYE_AGE_RULES = {
        "ch001": 7,    # 父母双亡，起点
        "ch024": 22,   # 15年后
    }

    # 关键角色年龄信息
    CHARACTER_AGES = {
        "林夜": {
            1: 7,
            24: 22,
        },
        "苏琳": {
            1: 19,
        },
        "星月": {
            1: 21,
        },
    }

    def __init__(self):
        super().__init__(CheckerType.TIMELINE_AGE)

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        检查时间线年龄一致性

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 包含 character_ages 的上下文

        Returns:
            Issue列表
        """
        issues = []
        context = context or {}

        # 获取当前章节的预期年龄
        expected_age = self._get_expected_age(chapter_num, "林夜")
        if expected_age is None:
            return []

        # 检测"X岁那年"矛盾
        age_mentions = self._extract_age_mentions(chapter_content, "林夜")
        for mention in age_mentions:
            mentioned_age = mention["age"]
            if mentioned_age > expected_age:
                issue = Issue(
                    id=f"timeline_age_{chapter_num}_{mentioned_age}",
                    severity=IssueSeverity.P0,
                    checker_type=CheckerType.TIMELINE_AGE,
                    issue_type="age_contradiction",
                    title=f"年龄时间线矛盾：{mentioned_age}岁 vs {expected_age}岁",
                    description=f"林夜在第{chapter_num}章年龄为{expected_age}岁，但文中出现「{mentioned_age}岁那年」的时间描述，与当前年龄矛盾。",
                    location=IssueLocation(chapter=chapter_num),
                    evidence=mention["context"],
                    suggestion=f"修正时间描述，避免与当前年龄矛盾。如当前{expected_age}岁，应使用「{expected_age - 5}岁那年」等符合时间线的描述。",
                    character="林夜",
                )
                issues.append(issue)

        # 检测生存时间矛盾（15年生存 vs 22岁）
        if chapter_num == 24:
            if expected_age != 22:
                issue = Issue(
                    id=f"timeline_age_24_22",
                    severity=IssueSeverity.P0,
                    checker_type=CheckerType.TIMELINE_AGE,
                    issue_type="survival_time_contradiction",
                    title="生存时间矛盾：15年生存",
                    description="第24章应为林夜15年生存后的第22岁，如年龄不符则存在矛盾。",
                    location=IssueLocation(chapter=24),
                    evidence=f"ch001:7岁 → ch024:22岁（15年生存）",
                    suggestion="确认第24章林夜年龄为22岁，15年生存时间正确。",
                    character="林夜",
                )
                issues.append(issue)

        return issues

    def _get_expected_age(self, chapter_num: int, character: str) -> Optional[int]:
        """
        获取章节的预期年龄

        Args:
            chapter_num: 章节号
            character: 角色名

        Returns:
            预期年龄，如果无数据返回None
        """
        if character not in self.CHARACTER_AGES:
            return None

        char_ages = self.CHARACTER_AGES[character]

        # 确保chapter_num是int类型
        try:
            chapter_num = int(chapter_num)
        except (ValueError, TypeError):
            # 如果无法转换为int（如传入文件名"ch061.md"），跳过检查
            return []

        # 查找最近的前置章节年龄
        applicable_age = None
        applicable_ch = None
        for ch_str in sorted(char_ages.keys(), key=lambda x: int(x)):
            ch = int(ch_str)
            if ch <= chapter_num:
                applicable_age = char_ages[ch_str]
                applicable_ch = ch
            else:
                break

        if applicable_age is None:
            return None

        # 计算章节间的年龄增长（假设每章约1个月）
        if applicable_ch is not None and applicable_ch != chapter_num:
            # 每章约1个月，所以每12章约1岁
            years_passed = (chapter_num - applicable_ch) / 12
            return int(applicable_age + years_passed)

        return applicable_age

    def _extract_age_mentions(self, content: str, character: str) -> List[Dict[str, Any]]:
        """
        提取文本中角色年龄提及

        Args:
            content: 章节内容
            character: 角色名

        Returns:
            年龄提及列表 [{"age": int, "context": str}]
        """
        mentions = []

        # 匹配"X岁那年"或"X岁时"等模式
        patterns = [
            rf'{character}[^。]*(?P<age>\d+)岁(?:的那年|时|候|那年|的日子)',
            rf'(?P<age>\d+)岁(?:的那年|时|候|那年)',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                age = int(match.group("age"))
                start = max(0, match.start() - 20)
                end = min(len(content), match.end() + 20)
                context = content[start:end]
                mentions.append({
                    "age": age,
                    "context": context,
                })

        return mentions

    def validate_age_timeline(self, character: str, age_map: Dict[int, int]) -> List[Dict[str, Any]]:
        """
        验证角色年龄时间线的一致性

        Args:
            character: 角色名
            age_map: 章节到年龄的映射 {chapter: age}

        Returns:
            矛盾列表
        """
        contradictions = []
        sorted_chapters = sorted(age_map.keys())

        for i in range(len(sorted_chapters) - 1):
            ch1, age1 = sorted_chapters[i], age_map[sorted_chapters[i]]
            ch2, age2 = sorted_chapters[i + 1], age_map[sorted_chapters[i + 1]]

            # 检查时间是否倒流
            if age2 < age1:
                contradictions.append({
                    "type": "age_regression",
                    "chapter1": ch1,
                    "age1": age1,
                    "chapter2": ch2,
                    "age2": age2,
                    "description": f"{character}年龄从ch{ch1}的{age1}岁倒流至ch{ch2}的{age2}岁",
                })

            # 检查年龄增长是否合理（每章约1个月，最多不超过1年）
            chapters_diff = ch2 - ch1
            age_diff = age2 - age1
            if age_diff > chapters_diff:
                contradictions.append({
                    "type": "excessive_age_growth",
                    "chapter1": ch1,
                    "age1": age1,
                    "chapter2": ch2,
                    "age2": age2,
                    "description": f"{character}年龄增长过快：ch{ch1}到ch{ch2}（{chapters_diff}章）年龄增长{age_diff}岁",
                })

        return contradictions