"""
LLM软评分器

迁移自 infra/quality_tools/soft_scorers/
"""

from .base import LLMScorer, ScoredResult

__all__ = ["LLMScorer", "ScoredResult"]
