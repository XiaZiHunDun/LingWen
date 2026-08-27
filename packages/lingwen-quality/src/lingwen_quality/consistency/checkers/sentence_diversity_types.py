"""SentenceDiversityChecker 公共数据类（拆分自 sentence_diversity_checker.py）。

包含：
- ``DiversityIssue`` — 章节级句式多样性评分结果
- ``TemplateSentence`` — 模板句命中详情
- ``PatternRatio`` — 句式占比信息

下游消费者统一从 ``lingwen_quality.consistency.checkers.sentence_diversity_checker``
导入（re-export），保持兼容性。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class DiversityIssue:
    chapter: str
    score: float
    severity: str
    description: str


@dataclass
class TemplateSentence:
    """模板句检测结果"""
    pattern_name: str
    template_example: str
    count: int
    percentage: float
    replacement_suggestions: List[str] = field(default_factory=list)


@dataclass
class PatternRatio:
    """句式占比信息"""
    pattern_name: str
    count: int
    percentage: float
    is_template: bool = False


__all__ = [
    "DiversityIssue",
    "TemplateSentence",
    "PatternRatio",
]
