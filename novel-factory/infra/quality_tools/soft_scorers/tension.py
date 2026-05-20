"""张力评分器 - 方向H质量工具集"""

import re
from typing import Any, Dict

from quality_tools.soft_scorers.base import BaseScorer, ScoredResult


class TensionScorer(BaseScorer):
    """张力评分 - 评估场景的紧张程度"""

    weight = 1.2

    def score(self, content: str, context: Dict[str, Any]) -> ScoredResult:
        """
        评估张力

        高张力特征：
        - 短句密集
        - 动作词频繁
        - 悬念铺设
        - 冲突明显
        """
        score = 50  # 基础分
        reasons = []

        # 检查句子长度（短句多=高张力）
        sentences = content.split("。")
        avg_length = sum(len(s) for s in sentences) / len(sentences) if sentences else 0

        if avg_length < 15:
            score += 20
            reasons.append("短句密集，张力充沛")
        elif avg_length > 30:
            score -= 10
            reasons.append("句子偏长，节奏较慢")

        # 检查动作词
        action_words = [
            "冲", "打", "杀", "战", "斗", "击", "砍", "劈",
            "逃", "追", "奔", "跑", "跃", "跳"
        ]
        action_count = sum(1 for word in action_words if word in content)
        if action_count > 5:
            score += 15
            reasons.append("动作描写密集")
        elif action_count < 2:
            score -= 10
            reasons.append("动作描写不足")

        # 检查悬念词
        suspense_words = ["突然", "然而", "可是", "却", "意外", "危机"]
        suspense_count = sum(1 for word in suspense_words if word in content)
        if suspense_count >= 3:
            score += 15
            reasons.append("悬念铺设充分")
        elif suspense_count == 0:
            score -= 10
            reasons.append("缺乏悬念铺垫")

        # 限制分数范围
        score = max(0, min(100, score))

        return ScoredResult(
            score=score,
            reason="; ".join(reasons) if reasons else "张力评分完成"
        )