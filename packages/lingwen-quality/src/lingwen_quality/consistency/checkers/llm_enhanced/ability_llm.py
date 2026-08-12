#!/usr/bin/env python3
"""
LLM增强能力检测器

能力检测器的LLM增强版本，用于检测需要LLM判断的能力相关段落
"""

import re
from typing import Any, Dict, List

from .base import LLMEnhancedChecker


class LLMEnhancedAbilityChecker(LLMEnhancedChecker):
    """能力检测器的LLM增强版本"""

    def __init__(self):
        from ...llm_service.base import LLMService
        from ..ability_checker import AbilityChecker

        super().__init__(
            base_checker=AbilityChecker(),
            llm_service=LLMService(),
            checker_type="ability"
        )

    def _find_uncertain_regions(self, content: str, context: dict) -> List[dict]:
        """找出需要LLM判断的能力相关段落"""
        uncertain = []

        ability_patterns = [
            r"突然.{0,10}实力大涨",
            r"竟然.{0,10}使出了",
            r"明明刚学会",
            r"毫无征兆.{0,10}突破",
            r"一夜之间.{0,10}实力",
        ]

        for pattern in ability_patterns:
            for m in re.finditer(pattern, content):
                uncertain.append({
                    "type": "ability_uncertain",
                    "text": m.group(),
                    "start": m.start(),
                    "end": m.end(),
                    "context": content[max(0, m.start()-50):m.end()+50]
                })

        return uncertain
