#!/usr/bin/env python3
"""
误报过滤器 - 过滤检测器局限导致的误报
"""

import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.quality import Issue
from tools.problem_classifier import ProblemClassifier


class FalsePositiveFilter:
    """
    误报过滤器

    使用 ProblemClassifier 区分：
    - CONTENT_ISSUE: 真实问题，保留
    - DETECTOR_ISSUE: 检测器局限，过滤
    - NEEDS_CONTEXT: 需要上下文，暂保留
    """

    def __init__(self):
        self.classifier = ProblemClassifier()

    def filter(self, issues: List[Issue], chapter_content: str = "") -> List[Issue]:
        """
        过滤误报

        Args:
            issues: 问题列表
            chapter_content: 章节内容

        Returns:
            过滤后的问题列表
        """
        filtered = []

        for issue in issues:
            classification = self.classifier.classify(issue, chapter_content)

            if classification == "CONTENT_ISSUE":
                filtered.append(issue)
            elif classification == "NEEDS_CONTEXT":
                filtered.append(issue)  # 保守策略，暂保留
            # DETECTOR_ISSUE 直接过滤

        return filtered

    def filter_batch(self, issues_by_chapter: dict, chapter_contents: dict = None) -> dict:
        """批量过滤误报"""
        result = {}
        for chapter, issues in issues_by_chapter.items():
            content = chapter_contents.get(chapter, "") if chapter_contents else ""
            filtered = self.filter(issues, content)
            if filtered:
                result[chapter] = filtered
        return result