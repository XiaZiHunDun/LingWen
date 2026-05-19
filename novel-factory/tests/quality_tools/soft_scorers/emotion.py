"""情感评分器 - 方向H质量工具集"""

from typing import Any, Dict

from soft_scorers.base import BaseScorer, ScoredResult


class EmotionScorer(BaseScorer):
    """情感评分 - 评估情感共鸣强度"""

    weight = 1.0

    def score(self, content: str, context: Dict[str, Any]) -> ScoredResult:
        """
        评估情感表达

        高情感特征：
        - 情感词丰富
        - 内心独白
        - 感官描写
        - 情绪变化
        """
        score = 50
        reasons = []

        # 检查情感词
        emotion_words = [
            "悲伤", "愤怒", "喜悦", "恐惧", "惊讶", "心疼",
            "感动", "激动", "难过", "开心", "快乐", "痛苦",
            "绝望", "希望", "担忧", "焦虑", "无奈", "心酸"
        ]
        emotion_count = sum(1 for word in emotion_words if word in content)

        if emotion_count >= 5:
            score += 20
            reasons.append("情感词汇丰富")
        elif emotion_count >= 2:
            score += 10
            reasons.append("有一定情感表达")
        else:
            score -= 10
            reasons.append("情感表达较少")

        # 检查内心独白
        internal_markers = ["心想", "想着", "心里想", "暗自", "自问"]
        internal_count = sum(1 for word in internal_markers if word in content)
        if internal_count >= 2:
            score += 15
            reasons.append("内心独白充沛")
        elif internal_count == 1:
            score += 5

        # 检查感官描写
        sensory_words = ["看见", "听到", "闻到", "感受到", "触摸"]
        sensory_count = sum(1 for word in sensory_words if word in content)
        if sensory_count >= 3:
            score += 10
            reasons.append("感官描写丰富")

        # 限制分数范围
        score = max(0, min(100, score))

        return ScoredResult(
            score=score,
            reason="; ".join(reasons) if reasons else "情感评分完成"
        )