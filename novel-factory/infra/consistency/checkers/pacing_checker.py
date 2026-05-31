#!/usr/bin/env python3
"""
节奏检测器 - 检测章节节奏问题

评估标准：
- 高潮/动作段不应过于密集
- 应有合理的缓冲和铺垫
- 战斗节奏应有张弛
"""

import re
from typing import List, Dict, Optional

from .base_checker import BaseChecker
from ..engine.data_structures import Issue, IssueSeverity, IssueLocation, CheckerType


class PacingChecker(BaseChecker):
    """节奏检测器"""

    def __init__(self):
        super().__init__(CheckerType.PACING)

        # 高潮/动作关键词
        self.action_keywords = [
            "战斗", "攻击", "冲击", "爆发", "爆炸", "碰撞",
            "厮杀", "搏斗", "对决", "交锋", "对抗"
        ]

        # 缓冲/过渡关键词
        self.cooldown_keywords = [
            "沉默", "叹息", "思考", "回忆", "休息", "等待",
            "观察", "警惕", "戒备", "喘息", "平静"
        ]

        # 铺垫关键词
        self.foreshadow_keywords = [
            "预感", "觉得", "似乎", "可能", "也许", "将要",
            "即将", "准备", "预感", "担忧"
        ]

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict] = None
    ) -> List[Issue]:
        issues = []

        # 检测高潮密度
        action_count = self._count_action_segments(chapter_content)
        total_segments = self._estimate_total_segments(chapter_content)

        if total_segments > 0:
            action_ratio = action_count / total_segments

            # 动作段超过60%认为节奏过密
            if action_ratio > 0.6 and action_count > 5:
                issues.append(Issue(
                    id=f"pacing_density_{chapter_num}",
                    severity=IssueSeverity.P2,
                    checker_type=CheckerType.PACING,
                    issue_type="节奏过密",
                    title="章节节奏过于密集",
                    description=f"章节中动作/冲突段过于密集（{action_count}处，占比{action_ratio:.0%}）",
                    location=IssueLocation(chapter=chapter_num),
                    evidence=f"动作段: {action_count}, 总段: {total_segments}"
                ))

        # 检测高潮后是否有缓冲
        if self._has_climax_without_cooldown(chapter_content):
            issues.append(Issue(
                id=f"pacing_cooldown_{chapter_num}",
                severity=IssueSeverity.P2,
                checker_type=CheckerType.SCENE_PATTERN,
                issue_type="高潮后缺少缓冲",
                title="连续高潮后缺少缓冲",
                description="连续高潮后缺少缓冲段读者会疲劳",
                location=IssueLocation(chapter=chapter_num)
            ))

        # 检测是否有过长铺垫
        setup_length = self._measure_foreshadow_length(chapter_content)
        if setup_length > 0.4:  # 铺垫超过40%
            issues.append(Issue(
                id=f"pacing_setup_{chapter_num}",
                severity=IssueSeverity.P3,
                checker_type=CheckerType.SCENE_PATTERN,
                issue_type="铺垫过长",
                title="章节前期铺垫过长",
                description="章节前期铺垫过长可能让读者失去耐心",
                location=IssueLocation(chapter=chapter_num)
            ))

        return issues

    def _count_action_segments(self, content: str) -> int:
        """统计动作段数量"""
        count = 0
        sentences = content.split('。')

        for sentence in sentences:
            action_count = sum(1 for kw in self.action_keywords if kw in sentence)
            if action_count >= 2:  # 一句中有2个以上动作词
                count += 1

        return count

    def _estimate_total_segments(self, content: str) -> int:
        """估算总段数（简单按句号计数）"""
        return max(1, content.count('。') + content.count('！') + content.count('？'))

    def _has_climax_without_cooldown(self, content: str) -> bool:
        """检测高潮后是否有缓冲"""
        sentences = content.split('。')
        recent_actions = 0
        recent_cooldowns = 0

        # 从后向前检测最近10句
        for sentence in reversed(sentences[-10:]):
            action_count = sum(1 for kw in self.action_keywords if kw in sentence)
            cooldown_count = sum(1 for kw in self.cooldown_keywords if kw in sentence)

            if action_count >= 2:
                recent_actions += 1
            if cooldown_count >= 1:
                recent_cooldowns += 1

        # 连续3个以上动作段但没有缓冲
        return recent_actions >= 3 and recent_cooldowns == 0

    def _measure_foreshadow_length(self, content: str) -> float:
        """测量铺垫长度占比"""
        sentences = content.split('。')

        if len(sentences) < 3:
            return 0.0

        # 前1/3为铺垫区
        setup_sentences = sentences[:len(sentences) // 3]
        foreshadow_count = sum(
            1 for s in setup_sentences
            if any(kw in s for kw in self.foreshadow_keywords)
        )

        return foreshadow_count / max(1, len(setup_sentences))