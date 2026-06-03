#!/usr/bin/env python3
"""
空间位置突兀转移检测器

检测角色在空间中突兀转移的问题（如瞬移、瞬间出现在某地等）

评估标准：
- 空间转移应有过渡描述
- 使用"穿过"、"走过"、"来到"等过渡词
- 不应有"突然出现在"、"瞬间来到"等突兀模式
"""

import re
from typing import Any, Dict, List, Optional

from ..engine.data_structures import CheckerType, Issue, IssueLocation, IssueSeverity
from .base_checker import BaseChecker


class SpatialTransitionChecker(BaseChecker):
    """空间位置突兀转移检测器"""
    _checker_type = CheckerType.SPATIAL_TRANSITION


    SUDDEN_TRANSITION_PATTERNS = [
        r"突然出现在([^，。、。！\n]+)",
        r"瞬间来到([^，。、。！\n]+)",
        r"一闪来到([^，。、。！\n]+)",
        r"直接到了([^，。、。！\n]+)",
        r"下一秒出现在([^，。、。！\n]+)",
        r"眨眼间出现在([^，。、。！\n]+)",
        r"直接出现在([^，。、。！\n]+)",
        r"瞬间出现在([^，。、。！\n]+)",
    ]

    TRANSITION_WORDS = [
        "穿过", "走过", "经过", "来到", "走进", "进入",
        "离开", "走出", "前往", "迂回", "绕到",
        "腾空而起", "御剑飞行", "瞬移", "传送",
        "转身", "迈步", "步行", "奔跑", "冲刺",
        "腾跃", "跳跃", "攀爬", "降落",
    ]

    COMMON_CHARACTERS = [
        "林夜", "苏琳", "莫言", "陈", "王",
        "剑尘子", "星陨", "月华", "暗皇",
    ]

    def __init__(self):
        super().__init__(self._checker_type)

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        检测空间突兀转移

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 上下文信息

        Returns:
            Issue列表
        """
        issues = []

        # 获取角色位置上下文
        character_locations = self._get_character_locations(context)

        for pattern in self.SUDDEN_TRANSITION_PATTERNS:
            for m in re.finditer(pattern, chapter_content):
                new_location = m.group(1)
                match_start = m.start()

                # 获取匹配前的100个字符作为前文
                before_text = chapter_content[max(0, match_start - 100):match_start]

                # 检查前文是否有过渡词
                if self._has_transition_word(before_text):
                    continue

                # 提取角色名
                character = self._extract_character(before_text)

                # 获取该角色之前的位置
                prev_location = None
                if character and character in character_locations:
                    prev_location = character_locations[character]

                # 创建问题
                issues.append(self._create_issue(
                    character=character or "未知角色",
                    prev_location=prev_location or "未知地点",
                    new_location=new_location,
                    evidence=m.group(),
                    chapter_num=chapter_num
                ))

        return issues

    def _get_character_locations(
        self,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        """从context获取角色位置"""
        if not context:
            return {}

        locations = {}

        # 从 character_states 中提取位置
        character_states = context.get("character_states", {})
        if isinstance(character_states, dict):
            for char_name, state in character_states.items():
                if isinstance(state, dict) and "location" in state:
                    locations[char_name] = state["location"]

        return locations

    def _has_transition_word(self, text: str) -> bool:
        """检查文本中是否有过渡词"""
        for word in self.TRANSITION_WORDS:
            if word in text:
                return True
        return False

    def _extract_character(self, text: str) -> Optional[str]:
        """从文本中提取角色名"""
        for name in self.COMMON_CHARACTERS:
            if name in text:
                return name
        return None

    def _create_issue(
        self,
        character: str,
        prev_location: str,
        new_location: str,
        evidence: str,
        chapter_num: int
    ) -> Issue:
        """创建空间转移问题"""
        return Issue(
            id=f"ST_{chapter_num:03d}_{character}",
            severity=IssueSeverity.P1,
            checker_type=CheckerType.SPATIAL_TRANSITION,
            issue_type="spatial_transition",
            title=f"空间突兀转移: {character}从{prev_location}到{new_location}",
            description=f"角色'{character}'从'{prev_location}'直接出现在'{new_location}'，无过渡描述",
            location=IssueLocation(chapter=chapter_num),
            evidence=f"匹配: {evidence[:50]}",
            suggestion="需要加入过渡描述（走过、穿过、来到等）"
        )
