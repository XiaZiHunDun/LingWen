#!/usr/bin/env python3
"""
LLM增强战斗描写检测器

战斗描写检测器的LLM增强版本，用于检测需要LLM判断的战斗相关段落
"""

import re
from typing import Any, Dict, List

from .base import LLMEnhancedChecker


class LLMEnhancedBattleVisualizationChecker(LLMEnhancedChecker):
    """战斗描写检测器的LLM增强版本"""

    def __init__(self):
        from ...llm_service.base import LLMService
        from ..battle_visualization import BattleVisualizationChecker

        super().__init__(
            base_checker=BattleVisualizationChecker(),
            llm_service=LLMService(),
            checker_type="battle"
        )

    def _find_uncertain_regions(self, content: str, context: dict) -> List[dict]:
        """找出需要LLM判断的战斗描写问题段落"""
        uncertain = []

        battle_patterns = [
            r"轻松击败",
            r"瞬间斩杀",
            r"一招毙命",
            r"毫无还手之力",
            r"竟然输了",
        ]

        for pattern in battle_patterns:
            for m in re.finditer(pattern, content):
                uncertain.append({
                    "type": "battle_uncertain",
                    "text": m.group(),
                    "start": m.start(),
                    "end": m.end(),
                    "context": content[max(0, m.start()-50):m.end()+50]
                })

        return uncertain
