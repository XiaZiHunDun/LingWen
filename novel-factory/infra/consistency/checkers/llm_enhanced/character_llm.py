#!/usr/bin/env python3
"""
LLM增强角色检测器

角色检测器的LLM增强版本，用于检测需要LLM判断的角色相关段落
"""

import re
from typing import List, Dict, Any

from .base import LLMEnhancedChecker


class LLMEnhancedCharacterChecker(LLMEnhancedChecker):
    """角色检测器的LLM增强版本"""

    def __init__(self):
        from ..character_checker import CharacterChecker
        from ...llm_service.base import LLMService

        super().__init__(
            base_checker=CharacterChecker(),
            llm_service=LLMService(),
            checker_type="character"
        )

    def _find_uncertain_regions(self, content: str, context: dict) -> List[dict]:
        """找出需要LLM判断的角色相关段落"""
        uncertain = []

        character_patterns = [
            r"性情大变",
            r"突然[的]?(暴怒|狂笑|哭泣|冷漠)",
            r"仿佛换了一个人",
            r"完全不像他",
            r"判若两人",
        ]

        for pattern in character_patterns:
            for m in re.finditer(pattern, content):
                uncertain.append({
                    "type": "character_uncertain",
                    "text": m.group(),
                    "start": m.start(),
                    "end": m.end(),
                    "context": content[max(0, m.start()-50):m.end()+50]
                })

        return uncertain