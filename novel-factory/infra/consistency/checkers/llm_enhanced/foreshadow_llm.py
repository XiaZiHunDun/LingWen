# novel-factory/infra/consistency/checkers/llm_enhanced/foreshadow_llm.py
import re
from typing import List, Dict, Any
from .base import LLMEnhancedChecker


class LLMEnhancedForeshadowChecker(LLMEnhancedChecker):
    """伏笔检测器的LLM增强版本"""

    def __init__(self):
        from ..foreshadow_checker import ForeshadowChecker
        from ...llm_service.base import LLMService

        super().__init__(
            base_checker=ForeshadowChecker(),
            llm_service=LLMService(),
            checker_type="foreshadow"
        )

    def _find_uncertain_regions(self, content: str, context: dict) -> List[dict]:
        """找出需要LLM判断的伏笔回收相关段落"""
        uncertain = []

        foreshadow_patterns = [
            r"原来.{0,20}(是|就是|竟是)",
            r"真相.{0,10}(揭晓|揭露|浮出水面)",
            r"一切都说得通了",
            r"直到现在才明白",
            r"所有谜题揭晓",
        ]

        for pattern in foreshadow_patterns:
            for m in re.finditer(pattern, content):
                uncertain.append({
                    "type": "foreshadow_uncertain",
                    "text": m.group(),
                    "start": m.start(),
                    "end": m.end(),
                    "context": content[max(0, m.start()-100):m.end()+100]
                })

        return uncertain