#!/usr/bin/env python3
"""
LLM增强关系状态检测器

关系状态检测器的LLM增强版本，用于检测需要LLM判断的关系相关段落
"""

import re
from typing import Any, Dict, List

from .base import LLMEnhancedChecker


class LLMEnhancedRelationshipStateChecker(LLMEnhancedChecker):
    """关系状态检测器的LLM增强版本"""

    def __init__(self):
        from ...llm_service.base import LLMService
        from ..relationship_state_checker import RelationshipStateChecker

        super().__init__(
            base_checker=RelationshipStateChecker(),
            llm_service=LLMService(),
            checker_type="relationship"
        )

    def _find_uncertain_regions(self, content: str, context: dict) -> List[dict]:
        """找出需要LLM判断的关系突变相关段落"""
        uncertain = []

        relationship_patterns = [
            r"突然和解",
            r"瞬间成为朋友",
            r"从敌人变成",
            r"一夜之间反目成仇",
            r"竟然相信了",
        ]

        for pattern in relationship_patterns:
            for m in re.finditer(pattern, content):
                uncertain.append({
                    "type": "relationship_uncertain",
                    "text": m.group(),
                    "start": m.start(),
                    "end": m.end(),
                    "context": content[max(0, m.start()-50):m.end()+50]
                })

        return uncertain
