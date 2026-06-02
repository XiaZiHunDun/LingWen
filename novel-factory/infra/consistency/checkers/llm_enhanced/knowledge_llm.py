# novel-factory/infra/consistency/checkers/llm_enhanced/knowledge_llm.py
import re
from typing import List, Dict, Any
from .base import LLMEnhancedChecker


class LLMEnhancedKnowledgeTracker(LLMEnhancedChecker):
    """知识追踪检测器的LLM增强版本"""

    def __init__(self):
        from ..knowledge_tracker import KnowledgeTracker
        from ...llm_service.base import LLMService

        super().__init__(
            base_checker=KnowledgeTracker(),
            llm_service=LLMService(),
            checker_type="knowledge"
        )

    def _find_uncertain_regions(self, content: str, context: dict) -> List[dict]:
        """找出需要LLM判断的信息知晓相关段落"""
        uncertain = []

        knowledge_patterns = [
            r"明明知道",
            r"假装不知道",
            r"却装作不知",
            r"心知肚明",
            r"应该记得",
        ]

        for pattern in knowledge_patterns:
            for m in re.finditer(pattern, content):
                uncertain.append({
                    "type": "knowledge_uncertain",
                    "text": m.group(),
                    "start": m.start(),
                    "end": m.end(),
                    "context": content[max(0, m.start()-50):m.end()+50]
                })

        return uncertain