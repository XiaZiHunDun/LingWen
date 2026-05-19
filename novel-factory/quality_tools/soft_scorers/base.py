"""软性评分器基类 - 方向H质量工具集"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ScoredResult:
    """评分结果"""
    score: float           # 0-100
    reason: str = ""


class BaseScorer(ABC):
    """软性评分器基类"""

    weight: float = 1.0  # 默认权重

    @abstractmethod
    def score(self, content: str, context: Dict[str, Any]) -> ScoredResult:
        """对内容评分

        Args:
            content: 待评分的内容
            context: 上下文信息

        Returns:
            ScoredResult: 评分结果（0-100）
        """
        raise NotImplementedError