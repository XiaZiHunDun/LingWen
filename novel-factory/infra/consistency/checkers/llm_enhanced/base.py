# novel-factory/infra/consistency/checkers/llm_enhanced/base.py
from typing import List, Dict, Any, Optional

from ...engine.data_structures import Issue, IssueLocation, IssueSeverity
from ...llm_service.base import LLMService
from ...llm_service.prompts import (
    ABILITY_LLM_PROMPT, CHARACTER_LLM_PROMPT, RELATIONSHIP_LLM_PROMPT,
    FORESHADOW_LLM_PROMPT, BATTLE_LLM_PROMPT, PERSONALITY_LLM_PROMPT, KNOWLEDGE_LLM_PROMPT
)
from ...llm_service.chapter_content import LLMIssue
from ..base_checker import BaseChecker


class LLMEnhancedChecker(BaseChecker):
    """LLM增强检测器基类"""

    PROMPT_MAP = {
        "ability": ABILITY_LLM_PROMPT,
        "character": CHARACTER_LLM_PROMPT,
        "relationship": RELATIONSHIP_LLM_PROMPT,
        "foreshadow": FORESHADOW_LLM_PROMPT,
        "battle": BATTLE_LLM_PROMPT,
        "personality": PERSONALITY_LLM_PROMPT,
        "knowledge": KNOWLEDGE_LLM_PROMPT,
    }

    def __init__(
        self,
        base_checker: BaseChecker,
        llm_service: LLMService,
        checker_type: str
    ):
        super().__init__(base_checker.checker_type)
        self.base_checker = base_checker
        self.llm_service = llm_service
        self.checker_type = checker_type
        self.prompt_template = self.PROMPT_MAP.get(checker_type, "")

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        # Step 1: 规则检测
        rule_issues = self.base_checker.check(chapter_content, chapter_num, context)

        # Step 2: 找出模糊区域
        uncertain_regions = self._find_uncertain_regions(chapter_content, context)

        # Step 3: 累积到批次
        if uncertain_regions:
            self.llm_service.add_to_batch(chapter_num, chapter_content, uncertain_regions)

        # Step 4: 批次达标时执行LLM检测
        llm_issues = self.llm_service.check_batch(self.checker_type, self.prompt_template)

        # Step 5: 转换LLMIssue为Issue
        return rule_issues + self._convert_llm_issues(llm_issues, chapter_num)

    def _find_uncertain_regions(self, content: str, context: dict) -> List[dict]:
        """由子类实现：找出需要LLM判断的模糊区域"""
        return []

    def _convert_llm_issues(self, llm_issues: list, default_chapter: int) -> List[Issue]:
        """将LLMIssue转换为Issue"""
        issues = []
        for llm_issue in llm_issues:
            severity = IssueSeverity.P0 if llm_issue.severity == "P0" else (
                IssueSeverity.P1 if llm_issue.severity == "P1" else IssueSeverity.P2
            )
            issues.append(Issue(
                id=f"LLM_{llm_issue.chapter or default_chapter:03d}_{llm_issue.type}",
                severity=severity,
                checker_type=self.base_checker.checker_type,
                issue_type=llm_issue.type,
                title=f"LLM检测-{llm_issue.type}: {llm_issue.description[:30]}",
                description=llm_issue.description,
                location=IssueLocation(chapter=llm_issue.chapter or default_chapter),
                evidence=llm_issue.evidence,
                suggestion=llm_issue.suggestion
            ))
        return issues