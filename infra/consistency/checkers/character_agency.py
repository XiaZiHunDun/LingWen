#!/usr/bin/env python3
"""
角色能动性检测器

检测角色被动情感反应 vs 主动行动的问题
评分标准（S7主角魅力 + S8人物弧光）：
- 优秀: 主动行动占比 > 30%
- 触发P1: 主动:被动 < 0.3
"""

import re
from typing import Any, Dict, List, Optional

from ..engine.data_structures import CheckerType, Issue, IssueLocation, IssueSeverity
from .base_checker import BaseChecker


class CharacterAgencyChecker(BaseChecker):
    """
    角色能动性检测器

    检测角色是否具有主动行动还是被动情感反应：
    - 被动模式：情感反应、眼眶泛红、静静地看着
    - 主动模式：站起来、走向、决定、攻击

    计算主动:被动比率，低于阈值时报告问题
    """
    _checker_type = CheckerType.CHARACTER_AGENCY


    # 被动情感反应模式
    REACTIVE_PATTERNS = [
        "眼眶泛红",
        "眼中含泪",
        "泪水模糊",
        "静静地看着",
        "默默地",
        "轻轻地",
        "微微一笑",
        "嘴角微扬",
        "低下头",
        "沉默",
        "叹息",
        "叹气",
        "咬紧嘴唇",
        "紧握拳头",
        "身体颤抖",
        "心中一紧",
        "心头一沉",
        "感到",
        "觉得",
        "似乎",
        "仿佛",
    ]

    # 主动行动模式
    ACTIVE_PATTERNS = [
        "站起来",
        "站起身",
        "走向",
        "走向前",
        "冲过去",
        "冲上去",
        "攻击",
        "出击",
        "动手",
        "决定",
        "下定决心",
        "毫不犹豫",
        "径直",
        "大步",
        "抬起手",
        "伸出手",
        "迈步",
        "跨步",
        "挣脱",
        "摆脱",
        "开始",
        "着手",
        "推进",
        "带领",
        "指挥",
        "命令",
        "质问",
        "追问",
        "要求",
        "核对",
        "翻看",
        "摊开",
        "收起",
        "敲",
        "拨",
        "喊",
        "问",
        "答",
        "打开",
        "关上",
        "推",
        "拉",
        "跑",
        "跳",
        "爬",
        "写",
        "记",
        "查",
        "找",
    ]

    # 能动性比率阈值
    AGENCY_RATIO_THRESHOLD = 0.3
    # 至少 N 次被动命中才评估，避免短章/偶发词误报（Phase 11.23）
    MIN_REACTIVE_HITS = 3

    def __init__(self):
        super().__init__(self._checker_type)

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        检查角色能动性

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 上下文信息

        Returns:
            Issue列表
        """
        issues = []
        context = context or {}

        if "target_characters" not in context:
            from infra.paths import ProjectPaths
            from infra.project_characters import load_agency_target_characters

            target_characters = load_agency_target_characters(
                ProjectPaths.get(),
                chapter_content=chapter_content,
            )
        else:
            target_characters = context["target_characters"]

        for character in target_characters:
            active_count = self._count_patterns(chapter_content, character, self.ACTIVE_PATTERNS)
            reactive_count = self._count_patterns(chapter_content, character, self.REACTIVE_PATTERNS)

            if reactive_count == 0:
                continue

            if reactive_count < self.MIN_REACTIVE_HITS:
                continue

            ratio = active_count / reactive_count if reactive_count > 0 else 0

            # P1: 能动性比率过低
            if ratio < self.AGENCY_RATIO_THRESHOLD:
                severity = IssueSeverity.P1 if ratio < 0.2 else IssueSeverity.P2

                issue = Issue(
                    id=f"character_agency_{chapter_num}_{character}",
                    severity=severity,
                    checker_type=CheckerType.CHARACTER_AGENCY,
                    issue_type="low_character_agency",
                    title=f"{character}能动性过低：比率{ratio:.2f}",
                    description=f"{character}在第{chapter_num}章主动行动{active_count}次，被动情感反应{reactive_count}次，比率{ratio:.2f}低于阈值{self.AGENCY_RATIO_THRESHOLD}。",
                    location=IssueLocation(chapter=chapter_num),
                    evidence=f"主动:{active_count}次，被动:{reactive_count}次",
                    suggestion=f"增加{character}的主动行动描写，减少情感反应。让角色主动推动情节而非被动反应。",
                    character=character,
                )
                issues.append(issue)

        return issues

    def _count_patterns(self, content: str, character: str, patterns: List[str]) -> int:
        """
        统计角色在文本中匹配的模式数量

        Args:
            content: 章节内容
            character: 角色名
            patterns: 模式列表

        Returns:
            匹配数量
        """
        count = 0

        # 角色相关段落过滤
        character_paragraphs = self._get_character_paragraphs(content, character)

        for para in character_paragraphs:
            for pattern in patterns:
                count += len(re.findall(pattern, para))

        return count

    def _get_character_paragraphs(self, content: str, character: str) -> List[str]:
        """
        获取角色相关的段落

        Args:
            content: 章节内容
            character: 角色名

        Returns:
            包含角色的段落列表
        """
        paragraphs = content.split('\n\n')
        relevant = []

        for para in paragraphs:
            if character in para:
                relevant.append(para)

        return relevant if relevant else [content]

    def calculate_agency_ratio(self, content: str, character: str) -> float:
        """
        计算角色能动性比率

        Args:
            content: 章节内容
            character: 角色名

        Returns:
            能动性比率
        """
        active_count = self._count_patterns(content, character, self.ACTIVE_PATTERNS)
        reactive_count = self._count_patterns(content, character, self.REACTIVE_PATTERNS)

        if reactive_count == 0:
            return 1.0 if active_count > 0 else 0.0

        return active_count / reactive_count
