"""
软性评分器基类

LLM软评分器 - 适用于需要语义理解的质量评估
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ScoredResult:
    """评分结果"""
    score: float           # 0-100
    reason: str = ""


class LLMScorer(ABC):
    """
    LLM软评分器基类

    适用于需要语义理解的质量评估，如情感共鸣、节奏等
    """

    weight: float = 1.0  # 默认权重

    @abstractmethod
    def score(self, content: str, context: Dict[str, Any]) -> ScoredResult:
        """
        对内容评分

        Args:
            content: 待评分的内容
            context: 上下文信息

        Returns:
            ScoredResult: 评分结果（0-100）
        """
        raise NotImplementedError


# Backward compatibility alias
BaseScorer = LLMScorer
