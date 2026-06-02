#!/usr/bin/env python3
"""
伏笔质量检测器

区分真伏笔与机械悬念
评分标准（S3文笔风格）：
- 优秀: 伏笔自然植入，无机械悬念标记
- 触发P2: 密度>2/千字 或 机械悬念标记过多
"""

import re
from typing import List, Optional, Dict, Any

from .base_checker import BaseChecker
from ..engine.data_structures import Issue, IssueLocation, IssueSeverity, CheckerType


class ForeshadowQualityChecker(BaseChecker):
    """
    伏笔质量检测器

    区分真伏笔与机械悬念：
    - 真伏笔：自然植入、与情节融合、有回溯价值
    - 机械悬念：套路化结尾、外部标记、"但他不知道的是"等

    检测以下机械悬念模式：
    - "但他不知道的是"
    - "就在这时"
    - "突然"
    - "下一秒"
    - "谁也不知道"
    - "而此刻"
    - "讽刺的是"
    """
    _checker_type = CheckerType.FORESHADOW_QUALITY


    # 机械悬念标记词
    MECHANICAL_SUSPENSE = [
        "但他不知道的是",
        "但她不知道的是",
        "但他们不知道的是",
        "就在这时",
        "就在此时",
        "下一秒",
        "谁也不知道",
        "而此刻",
        "讽刺的是",
        "可笑的是",
        "殊不知",
        "可惜",
        "注定",
    ]

    # 密度阈值（每千字）
    DENSITY_THRESHOLD = 2.0

    def __init__(self):
        super().__init__(self._checker_type)

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        检查伏笔质量

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 上下文信息

        Returns:
            Issue列表
        """
        issues = []
        context = context or {}

        # 计算文本长度（千字）
        content_length = len(chapter_content)
        word_count = content_length / 1000

        if word_count < 0.1:
            return []

        # 检测机械悬念
        mechanical_count = self._count_mechanical_suspense(chapter_content)
        density = mechanical_count / word_count if word_count > 0 else 0

        # P2: 密度过高
        if density > self.DENSITY_THRESHOLD:
            issue = Issue(
                id=f"foreshadow_quality_{chapter_num}_density",
                severity=IssueSeverity.P2,
                checker_type=CheckerType.FORESHADOW_QUALITY,
                issue_type="mechanical_suspense_density",
                title=f"机械悬念密度过高：{density:.1f}/千字",
                description=f"第{chapter_num}章机械悬念密度为{density:.1f}/千字，超过阈值{self.DENSITY_THRESHOLD}/千字。",
                location=IssueLocation(chapter=chapter_num),
                evidence=f"检测到{mechanical_count}处机械悬念标记",
                suggestion="减少机械悬念使用，改用自然伏笔植入。真伏笔应与情节融合，不依赖外部标记。",
            )
            issues.append(issue)

        # P1: 连续使用机械悬念
        consecutive_issues = self._detect_consecutive_mechanical(chapter_content, chapter_num)
        issues.extend(consecutive_issues)

        # P3: 检测具体机械悬念位置
        specific_mentions = self._detect_specific_mechanical(chapter_content, chapter_num)
        if specific_mentions and len(specific_mentions) >= 3:
            examples = [m["context"] for m in specific_mentions[:2]]
            issue = Issue(
                id=f"foreshadow_quality_{chapter_num}_mechanical",
                severity=IssueSeverity.P3,
                checker_type=CheckerType.FORESHADOW_QUALITY,
                issue_type="mechanical_suspense_patterns",
                title=f"机械悬念过多：{len(specific_mentions)}处",
                description=f"第{chapter_num}章检测到{len(specific_mentions)}处机械悬念标记。",
                location=IssueLocation(chapter=chapter_num),
                evidence="；".join(examples),
                suggestion="避免使用「但他不知道的是」「下一秒」「谁也不知道」等套路化表达。",
            )
            issues.append(issue)

        return issues

    def _count_mechanical_suspense(self, content: str) -> int:
        """
        统计机械悬念数量

        Args:
            content: 章节内容

        Returns:
            机械悬念数量
        """
        count = 0
        for pattern in self.MECHANICAL_SUSPENSE:
            count += len(re.findall(pattern, content))
        return count

    def _detect_consecutive_mechanical(self, content: str, chapter_num: int) -> List[Issue]:
        """
        检测连续使用机械悬念

        Args:
            content: 章节内容
            chapter_num: 章节号

        Returns:
            Issue列表
        """
        issues = []

        # 检测连续2段以上使用机械悬念
        paragraphs = content.split('\n\n')
        consecutive_count = 0
        consecutive_start = -1

        for i, para in enumerate(paragraphs):
            has_mechanical = any(p in para for p in self.MECHANICAL_SUSPENSE)
            if has_mechanical:
                if consecutive_start == -1:
                    consecutive_start = i
                consecutive_count += 1
            else:
                if consecutive_count >= 2:
                    issue = Issue(
                        id=f"foreshadow_consecutive_{chapter_num}_{consecutive_start}",
                        severity=IssueSeverity.P1,
                        checker_type=CheckerType.FORESHADOW_QUALITY,
                        issue_type="consecutive_mechanical_suspense",
                        title=f"连续机械悬念：连续{consecutive_count}段",
                        description=f"第{chapter_num}章连续{consecutive_count}段使用机械悬念标记。",
                        location=IssueLocation(chapter=chapter_num, paragraph=consecutive_start),
                        evidence=f"从第{consecutive_start}段开始",
                        suggestion="减少机械悬念使用，避免连续段落依赖外部标记制造悬念。",
                    )
                    issues.append(issue)
                consecutive_count = 0
                consecutive_start = -1

        return issues

    def _detect_specific_mechanical(self, content: str, chapter_num: int) -> List[Dict[str, Any]]:
        """
        检测具体机械悬念位置

        Args:
            content: 章节内容
            chapter_num: 章节号

        Returns:
            机械悬念位置列表
        """
        mentions = []

        for pattern in self.MECHANICAL_SUSPENSE:
            matches = re.finditer(pattern, content)
            for match in matches:
                start = max(0, match.start() - 15)
                end = min(len(content), match.end() + 15)
                context = content[start:end]
                mentions.append({
                    "pattern": pattern,
                    "context": context,
                    "position": match.start(),
                })

        return mentions