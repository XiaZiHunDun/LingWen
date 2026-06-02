#!/usr/bin/env python3
"""
LLM增强性格检测器

性格检测器的LLM增强版本，用于检测需要LLM判断的性格相关段落
"""

import re
from typing import List, Dict, Any

from .base import LLMEnhancedChecker


class LLMEnhancedPersonalityChecker(LLMEnhancedChecker):
    """性格检测器的LLM增强版本"""

    def __init__(self):
        from ..personality_checker import PersonalityChecker
        from ...llm_service.base import LLMService

        super().__init__(
            base_checker=PersonalityChecker(),
            llm_service=LLMService(),
            checker_type="personality"
        )

    def _find_uncertain_regions(self, content: str, context: dict) -> List[dict]:
        """找出需要LLM判断的性格突变相关段落"""
        uncertain = []

        personality_patterns = [
            r"变得残忍",
            r"性情大变",
            r"判若两人",
            r"完全变了一个人",
            r"核心性格发生",
        ]

        for pattern in personality_patterns:
            for m in re.finditer(pattern, content):
                uncertain.append({
                    "type": "personality_uncertain",
                    "text": m.group(),
                    "start": m.start(),
                    "end": m.end(),
                    "context": content[max(0, m.start()-50):m.end()+50]
                })

        return uncertain