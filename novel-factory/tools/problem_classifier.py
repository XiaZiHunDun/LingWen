#!/usr/bin/env python3
"""
问题分类器 - 区分检测器问题和真实内容问题
解决40%误报问题
"""

import sys
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.quality import Issue


class ProblemClassifier:
    """
    问题分类器

    检测器存在固有局限，本分类器用于区分：
    - CONTENT_ISSUE: 真实内容问题，需要修复
    - DETECTOR_ISSUE: 检测器局限导致的误报，应忽略
    - NEEDS_CONTEXT: 需要更多上下文才能判断
    """

    # 检测器已知的局限类型
    DETECTOR_LIMITATIONS = {
        "时间线矛盾": {
            "patterns": ["宇宙级", "跨维度", "时间跳跃", "星际", "光年", "亿万年"],
            "description": "宇宙级场景的时间线检测器容易误报"
        },
        "角色一致性": {
            "patterns": ["character_profiles缺失", "跨章节引用"],
            "description": "缺少角色档案时的角色一致性检测不准确"
        },
        "伏笔回收": {
            "patterns": ["需要前文铺垫", "伏笔首次出现", "悬念"],
            "description": "单章节无法判断伏笔回收，需要跨章节上下文"
        },
        "视角混乱": {
            "patterns": ["全知视角", "第三人称", "叙述者"],
            "description": "科幻/奇幻小说的特殊叙事方式可能被误判"
        },
        "逻辑矛盾": {
            "patterns": ["设定冲突", "世界观矛盾"],
            "description": "需要完整世界观设定才能判断"
        }
    }

    # 关键词映射到问题类型
    KEYWORD_TO_ISSUE = {
        "宇宙": "DETECTOR_LIMITATION",
        "维度": "DETECTOR_LIMITATION",
        "星际": "DETECTOR_LIMITATION",
        "光年": "DETECTOR_LIMITATION",
        "亿万年": "DETECTOR_LIMITATION",
        "创世": "DETECTOR_LIMITATION",
        "角色档案": "NEEDS_CONTEXT",
        "前文": "NEEDS_CONTEXT",
        "伏笔": "NEEDS_CONTEXT",
        "悬念": "NEEDS_CONTEXT",
    }

    def classify(self, issue: Issue, chapter_content: str = "") -> str:
        """
        分类问题

        Args:
            issue: 问题对象
            chapter_content: 章节内容（可选，用于更精确的判断）

        Returns:
            str: CONTENT_ISSUE / DETECTOR_ISSUE / NEEDS_CONTEXT
        """
        issue_type = issue.issue_type
        description = issue.description.lower()
        evidence = issue.evidence.lower()
        content = chapter_content.lower() if chapter_content else ""

        # 0. 先检查关键词中是否有明确的检测器局限关键词
        # 如果有明确的检测器局限关键词(如"亿万年"、"光年"、"宇宙"等)，
        # 直接返回 DETECTOR_ISSUE，不需要进一步分析
        for keyword, classification in self.KEYWORD_TO_ISSUE.items():
            if keyword in description or keyword in evidence:
                if classification == "DETECTOR_LIMITATION":
                    return "DETECTOR_ISSUE"
                elif classification == "NEEDS_CONTEXT":
                    # 需要上下文的关键词，暂标记为需要上下文
                    pass  # 继续后续检查

        # 1. 检查问题类型是否是已知的检测器局限
        for limit_type, config in self.DETECTOR_LIMITATIONS.items():
            if limit_type in issue_type:
                # 检查evidence或description中是否包含特定模式
                for pattern in config["patterns"]:
                    if pattern in description or pattern in evidence:
                        # 已经在步骤0中检查过明确的检测器局限关键词
                        # 这里处理的是需要更多上下文才能判断的情况
                        return "NEEDS_CONTEXT"

        # 2. 检查关键词
        for keyword, classification in self.KEYWORD_TO_ISSUE.items():
            if keyword in description or keyword in evidence:
                if classification == "DETECTOR_LIMITATION":
                    return "DETECTOR_ISSUE"
                elif classification == "NEEDS_CONTEXT":
                    return "NEEDS_CONTEXT"

        # 3. 检查内容长度（过短的内容容易误判）
        if len(chapter_content) < 500:
            if "矛盾" in issue_type or "逻辑" in issue_type:
                return "NEEDS_CONTEXT"

        # 4. 检查是否是状态/角色/逻辑等核心问题
        core_issues = ["状态矛盾", "角色行为逻辑", "逻辑矛盾", "因果逻辑"]
        for core in core_issues:
            if core in issue_type:
                return "CONTENT_ISSUE"

        # 5. 默认认为是真实问题
        return "CONTENT_ISSUE"

    def classify_batch(self, issues: List[Issue], chapter_contents: dict = None) -> dict:
        """
        批量分类

        Args:
            issues: 问题列表
            chapter_contents: chapter_num -> content 的映射

        Returns:
            dict: {
                "CONTENT_ISSUE": [...],  # 需要修复的问题
                "DETECTOR_ISSUE": [...],  # 误报问题
                "NEEDS_CONTEXT": [...],   # 需要更多上下文
            }
        """
        results = {
            "CONTENT_ISSUE": [],
            "DETECTOR_ISSUE": [],
            "NEEDS_CONTEXT": []
        }

        for issue in issues:
            content = chapter_contents.get(issue.chapter, "") if chapter_contents else ""
            classification = self.classify(issue, content)
            results[classification].append(issue)

        return results

    def get_fix_priority(self, issue: Issue) -> int:
        """
        获取修复优先级（1最高，5最低）

        Args:
            issue: 问题对象

        Returns:
            int: 优先级
        """
        # P0/P1问题优先级最高
        if issue.severity in ["P0", "P1"]:
            # 核心问题优先级更高
            if "状态矛盾" in issue.issue_type:
                return 1
            if "角色行为逻辑" in issue.issue_type:
                return 2
            if "逻辑矛盾" in issue.issue_type:
                return 2
            if "因果逻辑" in issue.issue_type:
                return 3
            return 3

        # P2/P3问题优先级较低
        return 4

    def filter_fixable_issues(self, issues: List[Issue], chapter_contents: dict = None) -> List[Issue]:
        """
        过滤出需要修复的问题（排除检测器局限问题）

        Args:
            issues: 问题列表
            chapter_contents: chapter_num -> content 的映射

        Returns:
            List[Issue]: 只包含需要修复的问题
        """
        content_issues = []
        for issue in issues:
            content = chapter_contents.get(issue.chapter, "") if chapter_contents else ""
            classification = self.classify(issue, content)
            if classification == "CONTENT_ISSUE":
                content_issues.append(issue)

        # 按优先级排序
        return sorted(content_issues, key=lambda x: self.get_fix_priority(x))


if __name__ == "__main__":
    # 测试
    classifier = ProblemClassifier()

    test_issues = [
        Issue(chapter=1, dimension="一致性", issue_type="时间线矛盾",
              severity="P1", description="宇宙级场景的时间矛盾", evidence="亿万年时间跨度"),
        Issue(chapter=2, dimension="一致性", issue_type="状态矛盾",
              severity="P0", description="角色状态前后不一致", evidence="前文说死了，后文活着"),
        Issue(chapter=3, dimension="一致性", issue_type="角色行为逻辑",
              severity="P1", description="角色行为不符合设定", evidence="性格突变"),
    ]

    for issue in test_issues:
        result = classifier.classify(issue, "")
        priority = classifier.get_fix_priority(issue)
        print(f"ch{issue.chapter}: {issue.issue_type} -> {result} (优先级:{priority})")