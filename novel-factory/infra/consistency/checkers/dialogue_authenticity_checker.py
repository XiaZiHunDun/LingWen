#!/usr/bin/env python3
"""
对话真实性检测器 - 检测AI化对话

评估标准：
- 对话应符合角色性格
- 不应有过多正式/书面化表达
- 应有口语化/角色特色表达
"""

import re
from typing import List, Dict, Optional

from .base_checker import BaseChecker
from ..engine.data_structures import Issue, IssueSeverity, IssueLocation, CheckerType


class DialogueAuthenticityChecker(BaseChecker):
    """对话真实性检测器"""

    def __init__(self):
        super().__init__(CheckerType.AI_GLOSS)

        # AI对话特征词
        self.ai_patterns = [
            r'我相信',
            r'毫无疑问',
            r'必须承认',
            r'从某种意义上',
            r'事实上',
            r'总的来说',
            r'毫无疑问',
            r'不言而喻',
            r'显而易见',
            r'众所周知'
        ]

        # 正式/书面化表达
        self.formal_patterns = [
            r'因此', r'然而', r'但是', r'所以',
            r'由于', r'既然', r'倘若', r'虽然'
        ]

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict] = None
    ) -> List[Issue]:
        issues = []

        # 检测AI特征词
        ai_matches = self._find_ai_patterns(chapter_content)
        if len(ai_matches) > 3:
            issues.append(Issue(
                id=f"dialogue_ai_{chapter_num}",
                severity=IssueSeverity.P2,
                checker_type=CheckerType.AI_GLOSS,
                issue_type="对话AI化",
                title="检测到AI化对话表达",
                description=f"检测到{len(ai_matches)}处AI化对话表达",
                location=IssueLocation(chapter=chapter_num),
                evidence=f"特征词: {', '.join(set(ai_matches))}"
            ))

        # 检测连续正式表达
        formal_count = self._count_formal_expressions(chapter_content)
        total_dialogue = self._estimate_dialogue_ratio(chapter_content)

        if total_dialogue > 0 and formal_count / total_dialogue > 0.5:
            issues.append(Issue(
                id=f"dialogue_formal_{chapter_num}",
                severity=IssueSeverity.P3,
                checker_type=CheckerType.AI_GLOSS,
                issue_type="对话过于正式",
                title="对话中正式表达占比过高",
                description="对话中正式表达占比过高，不够口语化",
                location=IssueLocation(chapter=chapter_num)
            ))

        return issues

    def _find_ai_patterns(self, content: str) -> List[str]:
        """找出所有AI特征词"""
        matches = []
        for pattern in self.ai_patterns:
            found = re.findall(pattern, content)
            matches.extend(found)
        return matches

    def _count_formal_expressions(self, content: str) -> int:
        """统计正式表达数量"""
        count = 0
        for pattern in self.formal_patterns:
            count += len(re.findall(pattern, content))
        return count

    def _estimate_dialogue_ratio(self, content: str) -> float:
        """估算对话占比"""
        dialogue_marks = content.count('「') + content.count('"')
        return dialogue_marks / 2  # 每段对话有开始和结束