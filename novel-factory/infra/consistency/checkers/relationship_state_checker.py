#!/usr/bin/env python3
"""
关系状态突变检测器

检测角色之间的关系状态发生剧烈变化但缺乏过渡描述的情况
例如：从"不信任"突然变为"信任"但没有过渡词
"""

import re
from typing import List, Dict, Any, Optional

from ..engine.data_structures import (
    Issue, IssueLocation, CheckerType, IssueSeverity
)
from .base_checker import BaseChecker


class RelationshipStateChecker(BaseChecker):
    """关系状态突变检测器"""

    # 负面关系词汇（信任度低）
    NEGATIVE_TRUST_WORDS = [
        "不信任", "怀疑", "警惕", "敌意", "仇恨", "敌视",
        "不信任他", "不信任她", "不会信任", "无法信任"
    ]

    # 正面关系词汇（信任度高）
    POSITIVE_TRUST_WORDS = [
        "信任", "相信", "托付", "依赖",
        "信任他", "信任她", "信任你", "深信不疑"
    ]

    # 负面情感词汇
    NEGATIVE_EMOTIONAL_WORDS = [
        "讨厌", "憎恨", "厌恶", "痛恨", "厌恶地",
        "讨厌他", "讨厌她", "憎恨他", "憎恨她"
    ]

    # 正面情感词汇
    POSITIVE_EMOTIONAL_WORDS = [
        "喜欢", "爱", "关心", "在乎",
        "喜欢他", "喜欢她", "深爱", "爱她", "爱他"
    ]

    # 过渡词（关系变化前的铺垫）
    TRANSITION_WORDS = [
        "经过", "几天后", "一个月后", "最终", "慢慢",
        "渐渐地", "终于", "逐渐", "多次", "生死考验",
        "渐渐地", "慢慢地", "随着时间", "日复一日",
        "从那以后", "此后", "后来", "一段时间后"
    ]

    # 突变关键词（表示关系突然变化）
    SUDDEN_CHANGE_PATTERNS = [
        r"突然[的]?(?:变|变?得)",
        r"瞬间",
        r"下一秒",
        r"刹那间",
        r"霎时",
        r"猝然",
        r"骤然",
        r"一下子",
        r"立刻",
        r"立即",
    ]

    def __init__(self):
        super().__init__(CheckerType.RELATIONSHIP_STATE)

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        检测章节中的关系状态突变

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 上下文信息

        Returns:
            Issue列表
        """
        issues = []

        # 检测信任状态突变
        trust_issues = self._check_trust_state_change(chapter_content, chapter_num)
        issues.extend(trust_issues)

        # 检测情感状态突变
        emotional_issues = self._check_emotional_state_change(chapter_content, chapter_num)
        issues.extend(emotional_issues)

        return issues

    def _check_trust_state_change(
        self,
        chapter_content: str,
        chapter_num: int
    ) -> List[Issue]:
        """检测信任状态突变"""
        issues = []

        # 统计负面和正面信任词
        negative_count = self._count_words(chapter_content, self.NEGATIVE_TRUST_WORDS)
        positive_count = self._count_words(chapter_content, self.POSITIVE_TRUST_WORDS)

        # 如果同时出现正面和负面词，可能有突变
        if negative_count > 0 and positive_count > 0:
            # 检查是否有过渡词
            has_transition = self._has_transition_word(chapter_content)
            if not has_transition:
                issues.append(self._create_issue(
                    change_type="trust",
                    evidence=f"负面信任词{negative_count}个, 正面信任词{positive_count}个",
                    chapter_num=chapter_num,
                    description="信任关系发生剧烈变化但无过渡描述"
                ))

        return issues

    def _check_emotional_state_change(
        self,
        chapter_content: str,
        chapter_num: int
    ) -> List[Issue]:
        """检测情感状态突变"""
        issues = []

        # 统计负面和正面情感词
        negative_count = self._count_words(chapter_content, self.NEGATIVE_EMOTIONAL_WORDS)
        positive_count = self._count_words(chapter_content, self.POSITIVE_EMOTIONAL_WORDS)

        # 如果同时出现正面和负面词，可能有突变
        if negative_count > 0 and positive_count > 0:
            # 检查是否有过渡词
            has_transition = self._has_transition_word(chapter_content)
            if not has_transition:
                issues.append(self._create_issue(
                    change_type="emotional",
                    evidence=f"负面情感词{negative_count}个, 正面情感词{positive_count}个",
                    chapter_num=chapter_num,
                    description="情感关系发生剧烈变化但无过渡描述"
                ))

        return issues

    def _count_words(self, content: str, word_list: List[str]) -> int:
        """统计词在内容中出现的次数"""
        count = 0
        for word in word_list:
            # 使用正则表达式进行更准确的匹配
            pattern = re.escape(word)
            count += len(re.findall(pattern, content))
        return count

    def _has_transition_word(self, content: str) -> bool:
        """检查内容是否包含过渡词"""
        for word in self.TRANSITION_WORDS:
            if word in content:
                return True
        return False

    def _has_sudden_change_pattern(self, content: str) -> bool:
        """检查内容是否包含突变模式"""
        for pattern in self.SUDDEN_CHANGE_PATTERNS:
            if re.search(pattern, content):
                return True
        return False

    def _create_issue(
        self,
        change_type: str,
        evidence: str,
        chapter_num: int,
        description: str = ""
    ) -> Issue:
        """创建Issue"""
        return Issue(
            id=f"RS_{chapter_num:03d}_{change_type}",
            severity=IssueSeverity.P1,
            checker_type=CheckerType.RELATIONSHIP_STATE,
            issue_type="relationship_state_change",
            title=f"关系状态突变: {change_type}",
            description=description or f"关系发生剧烈变化但无过渡描述",
            location=IssueLocation(chapter=chapter_num),
            evidence=f"证据: {evidence}",
            suggestion="需要加入过渡描述（如：经过、几天后、终于、渐渐地等）来说明关系是如何变化的"
        )

    def check_realtime(self, text: str, **kwargs) -> List[Issue]:
        """
        实时检查（轻量级）

        用于写作过程中即时预警
        """
        issues = []

        # 统计关系词汇
        negative_trust = self._count_words(text, self.NEGATIVE_TRUST_WORDS)
        positive_trust = self._count_words(text, self.POSITIVE_TRUST_WORDS)
        negative_emotional = self._count_words(text, self.NEGATIVE_EMOTIONAL_WORDS)
        positive_emotional = self._count_words(text, self.POSITIVE_EMOTIONAL_WORDS)

        # 如果同时出现正负两面词，且有过渡词，则可能有问题
        if (negative_trust > 0 and positive_trust > 0) or \
           (negative_emotional > 0 and positive_emotional > 0):
            if not self._has_transition_word(text):
                # 可能存在关系突变
                pass  # 实时检查不创建Issue，仅记录

        return issues