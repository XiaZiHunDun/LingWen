#!/usr/bin/env python3
"""
节奏检测器 - 检测章节节奏问题

评估标准：
- 高潮/动作段不应过于密集
- 应有合理的缓冲和铺垫
- 战斗节奏应有张弛
"""

import re
from collections import Counter
from typing import TYPE_CHECKING, Dict, List, Optional, Protocol

from ..engine.data_structures import CheckerType, Issue, IssueLocation, IssueSeverity
from .base_checker import BaseChecker
from .text_utils import split_chinese_sentences

if TYPE_CHECKING:
    from infra.world_model.data_structures import Ripple


class _RippleRegistryLike(Protocol):
    """Ripple Registry 最小接口 (Protocol 解耦)

    PacingChecker 实际需要: list_active + get_ripple
    """

    def list_active(self) -> tuple: ...
    def get_ripple(self, ripple_id: str) -> Optional["Ripple"]: ...


class PacingChecker(BaseChecker):
    """节奏检测器"""
    _checker_type = CheckerType.PACING


    def __init__(self):
        super().__init__(self._checker_type)

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
        sentences = split_chinese_sentences(content)

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
        sentences = split_chinese_sentences(content)
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
        sentences = split_chinese_sentences(content)

        if len(sentences) < 3:
            return 0.0

        # 前1/3为铺垫区
        setup_sentences = sentences[:len(sentences) // 3]
        foreshadow_count = sum(
            1 for s in setup_sentences
            if any(kw in s for kw in self.foreshadow_keywords)
        )

        return foreshadow_count / max(1, len(setup_sentences))

    # ============ Phase 2.4 — Ripple 密度检测 ============

    def check_ripple_density(
        self,
        ripple_registry: _RippleRegistryLike,
        current_ch: int,
        active_threshold: int = 6,
        convergence_threshold: int = 3,
    ) -> List[Issue]:
        """章节涟漪密度检测 (Phase 2.4)

        检测两类问题:
        1. 密度过高:active ripple 数 > active_threshold → P2 issue
        2. 集中爆发:同一章节 wavefront 出现 > convergence_threshold 次 → P1 issue

        Args:
            ripple_registry: 实现 list_active + get_ripple 的对象
            current_ch: 当前章节号 (用于过滤未来章节)
            active_threshold: 活跃 ripple 上限 (默认 6)
            convergence_threshold: 单章节集中上限 (默认 3)

        Returns:
            Issue 列表 (空 = 无问题)
        """
        issues: List[Issue] = []

        # 1. 收集活跃 ripple
        active_ripples = ripple_registry.list_active()
        active_count = len(active_ripples)

        # 2. 密度检测
        if active_count > active_threshold:
            issues.append(Issue(
                id=f"ripple_density_{current_ch}",
                severity=IssueSeverity.P2,
                checker_type=CheckerType.PACING,
                issue_type="涟漪密度过高",
                title=f"章节涟漪密度过高 ({active_count} > {active_threshold})",
                description=(
                    f"活跃涟漪数 {active_count} 超过阈值 {active_threshold},"
                    f"读者可能感到伏笔负担过重"
                ),
                location=IssueLocation(chapter=current_ch),
                evidence=f"active_count={active_count}, threshold={active_threshold}",
                suggestion="考虑提前平复部分涟漪 (resolve) 或暂缓新涟漪注册",
            ))

        # 3. 集中检测 (wavefront 章节分布)
        #    用 get_active_wavefront 过滤未来章节 → 统计每章出现次数
        chapter_counter: Counter = Counter()
        for ripple in active_ripples:
            # 优先用 registry.get_ripple (可能含最新 wavefront)
            r = ripple_registry.get_ripple(ripple.ripple_id) or ripple
            active_wave = self._filter_active_wavefront(r, current_ch)
            for ch in active_wave:
                chapter_counter[ch] += 1

        # 找集中爆发的章节 (> convergence_threshold)
        convergence_chapters = [
            (ch, count) for ch, count in chapter_counter.items()
            if count > convergence_threshold
        ]
        for ch, count in convergence_chapters:
            issues.append(Issue(
                id=f"ripple_convergence_{current_ch}_{ch}",
                severity=IssueSeverity.P1,
                checker_type=CheckerType.PACING,
                issue_type="涟漪集中爆发",
                title=f"ch{ch} 涟漪集中爆发 ({count} 个)",
                description=(
                    f"ch{ch} 出现 {count} 个 ripple wavefront,"
                    f"超过集中阈值 {convergence_threshold},"
                    f"读者可能感到信息过载"
                ),
                location=IssueLocation(chapter=ch),
                evidence=f"ch{ch}: {count} ripples",
                suggestion="考虑将部分 ripple 推到后续章节展开",
            ))

        return issues

    @staticmethod
    def _filter_active_wavefront(ripple, current_ch: int) -> tuple:
        """过滤 ripple.wavefront 中 ≤ current_ch 的章节

        复用 RippleEngine.get_active_wavefront 逻辑
        (避免直接 import engine 造成依赖)
        """
        return tuple(
            w for w in ripple.wavefront
            if ripple.origin_ch <= w <= current_ch
        )
