"""冗余检测评分器 - 方向H质量工具集"""

from typing import Any, Dict, List, Set

from soft_scorers.base import BaseScorer, ScoredResult


class RedundancyScorer(BaseScorer):
    """冗余检测评分 - 评估是否有重复表达"""

    weight = 0.7

    def score(self, content: str, context: Dict[str, Any]) -> ScoredResult:
        """
        评估冗余程度

        低冗余特征：
        - 无重复表达
        - 无信息重复
        - 无语义重复
        """
        score = 80  # 基准分较高，因为冗余是减分项
        reasons = []

        words = content.split()
        if not words:
            return ScoredResult(score=100, reason="内容为空，默认为无冗余")

        # 检查词汇重复
        word_counts: Dict[str, int] = {}
        for word in words:
            if len(word) >= 2:  # 只统计长度>=2的词
                word_counts[word] = word_counts.get(word, 0) + 1

        # 找出过度重复的词
        excessive_repetition = [
            word for word, count in word_counts.items()
            if count >= 5
        ]

        if excessive_repetition:
            score -= len(excessive_repetition) * 5
            reasons.append(f"发现{len(excessive_repetition)}个过度重复词汇")

        # 检查连续重复
        if self._check_consecutive_repetition(content):
            score -= 15
            reasons.append("存在连续重复表达")

        # 检查句式重复
        if self._check_sentence_repetition(content):
            score -= 10
            reasons.append("存在句式重复")

        # 限制分数范围
        score = max(0, min(100, score))

        return ScoredResult(
            score=score,
            reason="; ".join(reasons) if reasons else "冗余检测完成，无明显冗余"
        )

    def _check_consecutive_repetition(self, content: str) -> bool:
        """检查连续重复"""
        import re
        # 检查连续3个相同字符
        return bool(re.search(r'(.)\1{2,}', content))

    def _check_sentence_repetition(self, content: str) -> bool:
        """检查句式重复"""
        sentences = content.split("。")
        if len(sentences) < 3:
            return False

        # 检查是否有完全相同的句子
        sentence_set = set(sentences)
        return len(sentence_set) < len(sentences) - 1