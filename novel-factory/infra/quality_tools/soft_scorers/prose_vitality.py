"""散文活力评分器 - 方向H质量工具集"""

import re
from typing import Any, Dict

from quality_tools.soft_scorers.base import BaseScorer, ScoredResult


class ProseVitalityScorer(BaseScorer):
    """散文活力评分 - 评估表达的多样性和活力"""

    weight = 0.8

    def score(self, content: str, context: Dict[str, Any]) -> ScoredResult:
        """
        评估散文活力

        高活力特征：
        - 词汇多样
        - 句式变化
        - 修辞使用
        - 无僵硬表达
        """
        score = 50
        reasons = []

        words = content.split()
        if not words:
            return ScoredResult(score=0, reason="内容为空")

        # 词汇多样性（类型词比）
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio > 0.7:
            score += 20
            reasons.append("词汇多样性高")
        elif unique_ratio > 0.5:
            score += 10
        else:
            score -= 10
            reasons.append("词汇重复较多")

        # 句式变化检查
        sentence_endings = re.findall(r'[，。！？；：""''（）]', content)
        if len(set(sentence_endings)) >= 4:
            score += 15
            reasons.append("句式变化丰富")
        elif len(set(sentence_endings)) >= 2:
            score += 5

        # 检查修辞使用
        rhetorical_markers = ["像", "如同", "仿佛", "如", "若"]
        rhetorical_count = sum(1 for word in rhetorical_markers if word in content)
        if rhetorical_count >= 3:
            score += 15
            reasons.append("修辞手法使用得当")
        elif rhetorical_count >= 1:
            score += 5

        # 检查僵硬表达
        rigid_patterns = [r"是的", r"的确", r"非常", r"十分", r"很"]
        rigid_count = sum(1 for pattern in rigid_patterns if re.search(pattern, content))
        if rigid_count > 5:
            score -= 15
            reasons.append("存在过度使用的僵硬修饰")

        # 限制分数范围
        score = max(0, min(100, score))

        return ScoredResult(
            score=score,
            reason="; ".join(reasons) if reasons else "散文活力评分完成"
        )