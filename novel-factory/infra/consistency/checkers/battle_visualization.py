#!/usr/bin/env python3
"""
战斗描写具象化检测器

检测战斗描写中抽象概念 vs 具象描写的比例
评分标准（S3文笔风格）：
- 优秀: 具象描写 > 40%
- 触发P2: 抽象占比 > 60%
"""

import re
from typing import List, Optional, Dict, Any

from .base_checker import BaseChecker
from .vocabulary import (
    ABSTRACT_CULTIVATION,
    CONCRETE_VISUAL,
    CONCRETE_ACTION,
)
from ..engine.data_structures import Issue, IssueLocation, IssueSeverity, CheckerType


class BattleVisualizationChecker(BaseChecker):
    """
    战斗描写具象化检测器

    检测战斗场景中抽象概念与具象描写的比例：
    - 抽象概念：星辰能量、能量波动、灵气、虚无
    - 具象描写：光芒、火焰、血、碎片、声响

    抽象占比过高会降低战斗场景的可读性和视觉冲击力
    """
    _checker_type = CheckerType.BATTLE_VISUALIZATION

    # R2-012: 词汇表已迁出至 vocabulary.py — 共享给其他 checker
    # 保留类属性引用,API 零变化 (外部仍写 self.ABSTRACT_CULTIVATION)
    ABSTRACT_CULTIVATION = ABSTRACT_CULTIVATION
    CONCRETE_VISUAL = CONCRETE_VISUAL
    CONCRETE_ACTION = CONCRETE_ACTION

    # 抽象占比阈值
    ABSTRACT_RATIO_THRESHOLD = 0.6

    def __init__(self):
        super().__init__(self._checker_type)

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        检查战斗描写具象化程度

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 上下文信息

        Returns:
            Issue列表
        """
        issues = []
        context = context or {}

        # 检查是否包含战斗场景
        if not self._is_battle_scene(chapter_content):
            return []

        # 提取战斗段落
        battle_paragraphs = self._extract_battle_paragraphs(chapter_content)

        if not battle_paragraphs:
            return []

        # 统计抽象和具象描写(去重:同一处被多个重叠 pattern 命中只算 1 次)
        abstract_count = 0
        concrete_count = 0

        for para in battle_paragraphs:
            abstract_count += self._count_unique_matches(self.ABSTRACT_CULTIVATION, para)
            concrete_count += self._count_unique_matches(
                self.CONCRETE_VISUAL + self.CONCRETE_ACTION, para
            )

        total = abstract_count + concrete_count
        if total == 0:
            return []

        abstract_ratio = abstract_count / total

        # P2: 抽象占比过高
        if abstract_ratio > self.ABSTRACT_RATIO_THRESHOLD:
            issue = Issue(
                id=f"battle_visual_{chapter_num}",
                severity=IssueSeverity.P2,
                checker_type=CheckerType.BATTLE_VISUALIZATION,
                issue_type="excessive_abstract_battle",
                title=f"战斗描写抽象化过高：{abstract_ratio*100:.0f}%",
                description=f"第{chapter_num}章战斗描写中抽象概念占{abstract_ratio*100:.0f}%，超过阈值60%。",
                location=IssueLocation(chapter=chapter_num),
                evidence=f"抽象:{abstract_count}处，具象:{concrete_count}处",
                suggestion="增加具象描写，用具体视觉和动作替代抽象概念。如「能量波动」改为「火星四溅」，「星辰能量」改为「剑身发出炽白光」。",
            )
            issues.append(issue)

        return issues

    def _is_battle_scene(self, content: str) -> bool:
        """
        判断是否为战斗场景

        Args:
            content: 章节内容

        Returns:
            是否为战斗场景
        """
        battle_indicators = [
            "战斗",
            "交锋",
            "对峙",
            "激战",
            "厮杀",
            "出招",
            "招式",
            "攻击",
            "防守",
            "剑",
            "刀",
            "拳",
        ]

        for indicator in battle_indicators:
            if indicator in content:
                return True

        return False

    def _extract_battle_paragraphs(self, content: str) -> List[str]:
        """
        提取战斗相关段落

        Args:
            content: 章节内容

        Returns:
            战斗段落列表
        """
        paragraphs = content.split('\n\n')
        battle_paragraphs = []

        for para in paragraphs:
            # 包含战斗关键词的段落
            battle_keywords = ["战斗", "交锋", "招式", "剑", "拳", "刀", "攻击"]
            if any(kw in para for kw in battle_keywords):
                battle_paragraphs.append(para)

        return battle_paragraphs if battle_paragraphs else [content]

    def calculate_abstract_ratio(self, content: str) -> float:
        """
        计算抽象描写占比

        Args:
            content: 章节内容

        Returns:
            抽象占比
        """
        abstract_count = self._count_unique_matches(self.ABSTRACT_CULTIVATION, content)
        concrete_count = self._count_unique_matches(
            self.CONCRETE_VISUAL + self.CONCRETE_ACTION, content
        )

        total = abstract_count + concrete_count
        if total == 0:
            return 0.0

        return abstract_count / total

    @staticmethod
    def _count_unique_matches(patterns, content: str) -> int:
        """去重计数:同一段文本被多个重叠 pattern 命中只算 1 次

        为什么需要:
        ABSTRACT_CULTIVATION 含 '能量波动' / '能量' / '能量汇聚' 等重叠子串。
        简单 `for p in patterns: re.findall(p, content)` 会让 '能量波动剧烈' 同时
        被 '能量波动' (1) 和 '能量' (1) 命中,同 1 处算 2 次,虚高抽象占比。

        修复:把所有 pattern 合并成一个 alternation regex,按长度倒序排列 →
        长的优先匹配,sub-string 没机会被重复数。
        `re.findall` 在 alternation 上是非重叠的、最左最长,正好契合需求。
        """
        if not patterns or not content:
            return 0
        # 按长度倒序:长的 pattern 排前面,alternation 时优先匹配
        sorted_patterns = sorted(patterns, key=len, reverse=True)
        combined = "|".join(re.escape(p) for p in sorted_patterns)
        return len(re.findall(combined, content))