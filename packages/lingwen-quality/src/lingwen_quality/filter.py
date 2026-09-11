"""误报过滤器 - 过滤检测器局限导致的误报

Phase 46 P3-ARCHDEBT: relocated from infra/filter.py (63 LOC).
Now an internal submodule of lingwen_quality (was using sys.path hack to
import from lingwen_quality.quality + tools.problem_classifier).

Architecture note: Both sys.path hacks REMOVED. ProblemClassifier is now
a sibling submodule within lingwen_quality. All imports are clean
relative imports within the package.
"""

from __future__ import annotations

from typing import List

# Phase 46: sys.path hack REMOVED. Relative imports within lingwen_quality package.
from lingwen_quality.quality import Issue
from lingwen_quality.problem_classifier import ProblemClassifier


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


__all__ = ["FalsePositiveFilter"]