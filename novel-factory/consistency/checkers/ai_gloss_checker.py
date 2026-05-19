#!/usr/bin/env python3
"""
AI痕迹检测器

检测AI写作的常见痕迹

检测维度：
1. 过度总结：使用"总之"、"可以看出"等
2. 机械过渡：使用"首先"、"其次"、"然后"、"最后"
3. 格式化：使用"第一点"、"第二点"
4. AI特有表达：某些AI特有的句式结构
"""

from typing import List, Dict, Any, Optional, Tuple

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from consistency.engine.data_structures import Issue, IssueSeverity, CheckerType, IssueLocation
from consistency.checkers.base_checker import BaseChecker


class AIGlossChecker(BaseChecker):
    """AI痕迹检测器"""

    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        super().__init__(CheckerType.AI_GLOSS)
        self.rules = rules or self._default_rules()

    def _default_rules(self) -> Dict[str, Any]:
        """默认规则"""
        return {
            "patterns": {
                "over_summary": [
                    "总之", "可以看出", "由此可见", "不难发现",
                    "值得注意的是", "从某种意义上说", "客观来说",
                    "总的来说", "综合来看", "事实证明"
                ],
                "mechanical_transition": [
                    "首先", "其次", "然后", "最后", "第一", "第二", "第三",
                    "一方面", "另一方面", "与此同时", "在此基础上"
                ],
                "formatting": [
                    "第一点", "第二点", "第三点", "以下几点",
                    "具体来说", "包括以下几点", "主要表现在"
                ],
                "ai_phrases": [
                    "作为一个AI", "我作为一个语言模型",
                    "从技术角度来说", "从理论上来讲"
                ]
            },
            "severity": {
                "P3_count_threshold": 3,
                "density_threshold": 0.05
            }
        }

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        检测AI痕迹

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 上下文

        Returns:
            Issue列表
        """
        issues = []
        patterns = self.rules.get("patterns", {})

        # 检查过度总结
        issues.extend(self._check_over_summary(
            chapter_content, chapter_num, patterns.get("over_summary", [])
        ))

        # 检查机械过渡
        issues.extend(self._check_mechanical_transition(
            chapter_content, chapter_num, patterns.get("mechanical_transition", [])
        ))

        # 检查格式化表达
        issues.extend(self._check_formatting(
            chapter_content, chapter_num, patterns.get("formatting", [])
        ))

        # 检查AI特有表达
        issues.extend(self._check_ai_phrases(
            chapter_content, chapter_num, patterns.get("ai_phrases", [])
        ))

        return issues

    def _check_over_summary(
        self,
        content: str,
        chapter_num: int,
        keywords: List[str]
    ) -> List[Issue]:
        """检查过度总结类表达"""
        issues = []
        severity_rules = self.rules.get("severity", {})

        for keyword in keywords:
            count = content.count(keyword)
            if count >= severity_rules.get("P3_count_threshold", 3):
                issues.append(Issue(
                    id=f"ai_{chapter_num}_over_summary_{keyword}",
                    severity=IssueSeverity.P3,
                    checker_type=CheckerType.AI_GLOSS,
                    issue_type="AI过度总结",
                    title="使用过度总结表达",
                    description=f"文本中\"{keyword}\"出现{count}次，可能是AI写作痕迹",
                    location=IssueLocation(chapter=chapter_num),
                    evidence=f"\"{keyword}\"出现{count}次",
                    suggestion="使用更自然的叙述方式替代",
                    character=None
                ))

        return issues

    def _check_mechanical_transition(
        self,
        content: str,
        chapter_num: int,
        keywords: List[str]
    ) -> List[Issue]:
        """检查机械过渡"""
        issues = []
        severity_rules = self.rules.get("severity", {})

        for keyword in keywords:
            count = content.count(keyword)
            if count >= severity_rules.get("P3_count_threshold", 3):
                issues.append(Issue(
                    id=f"ai_{chapter_num}_mechanical_{keyword}",
                    severity=IssueSeverity.P3,
                    checker_type=CheckerType.AI_GLOSS,
                    issue_type="AI机械过渡",
                    title="使用机械过渡表达",
                    description=f"文本中\"{keyword}\"出现{count}次，可能是AI写作痕迹",
                    location=IssueLocation(chapter=chapter_num),
                    evidence=f"\"{keyword}\"出现{count}次",
                    suggestion="使用更流畅的过渡方式替代",
                    character=None
                ))

        return issues

    def _check_formatting(
        self,
        content: str,
        chapter_num: int,
        keywords: List[str]
    ) -> List[Issue]:
        """检查格式化表达"""
        issues = []

        for keyword in keywords:
            if keyword in content:
                issues.append(Issue(
                    id=f"ai_{chapter_num}_formatting_{keyword}",
                    severity=IssueSeverity.P3,
                    checker_type=CheckerType.AI_GLOSS,
                    issue_type="AI格式化表达",
                    title="使用格式化列表表达",
                    description=f"文本中使用\"{keyword}\"等格式化表达，显得生硬",
                    location=IssueLocation(chapter=chapter_num),
                    evidence=keyword,
                    suggestion="使用自然段落叙述替代列表格式",
                    character=None
                ))

        return issues

    def _check_ai_phrases(
        self,
        content: str,
        chapter_num: int,
        keywords: List[str]
    ) -> List[Issue]:
        """检查AI特有短语"""
        issues = []

        for keyword in keywords:
            if keyword in content:
                issues.append(Issue(
                    id=f"ai_{chapter_num}_phrase_{keyword}",
                    severity=IssueSeverity.P2,
                    checker_type=CheckerType.AI_GLOSS,
                    issue_type="AI特有表达",
                    title="使用AI特有表达",
                    description=f"文本中\"{keyword}\"是AI写作的典型表达",
                    location=IssueLocation(chapter=chapter_num),
                    evidence=keyword,
                    suggestion="改用更自然的人类写作表达",
                    character=None
                ))

        return issues

    def check_density(self, content: str) -> float:
        """计算AI痕迹密度"""
        patterns = self.rules.get("patterns", {})
        all_patterns = []
        for pattern_list in patterns.values():
            all_patterns.extend(pattern_list)

        total_matches = sum(content.count(p) for p in all_patterns)
        density = total_matches / max(len(content), 1)

        return density

    def check_realtime(self, text: str, **kwargs) -> List[Issue]:
        """实时检查（简化版）"""
        issues = []
        patterns = self.rules.get("patterns", {})

        for keyword in patterns.get("ai_phrases", []):
            if keyword in text:
                issues.append(Issue(
                    id=f"ai_realtime_{keyword}",
                    severity=IssueSeverity.P2,
                    checker_type=CheckerType.AI_GLOSS,
                    issue_type="AI特有表达",
                    title="检测到AI写作痕迹",
                    description=f"\"{keyword}\"是AI写作的典型表达",
                    location=IssueLocation(chapter=0),
                    evidence=keyword,
                    suggestion="使用更自然的人类写作表达",
                    character=None
                ))

        return issues