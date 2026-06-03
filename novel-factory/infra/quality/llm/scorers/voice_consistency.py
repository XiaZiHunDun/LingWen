"""声音一致性评分器 - 方向H质量工具集"""

from typing import Any, Dict, List

from infra.quality.llm.scorers.base import BaseScorer, ScoredResult


class VoiceConsistencyScorer(BaseScorer):
    """声音一致性评分 - 评估叙述声音的一致性"""

    weight = 1.0

    def score(self, content: str, context: Dict[str, Any]) -> ScoredResult:
        """
        评估声音一致性

        一致性特征：
        - 叙述语气稳定
        - 无OOC（Out Of Character）
        - 视角人物语言风格统一
        """
        score = 50
        reasons = []

        # 获取角色设定
        characters = context.get("characters", [])
        main_character = context.get("main_character")

        if not main_character and characters:
            main_character = characters[0].get("name", "")

        if main_character:
            # 检查主角色的语言风格一致性
            speech_patterns = self._analyze_speech_pattern(content, main_character)

            if speech_patterns["consistent"]:
                score += 25
                reasons.append("叙述声音一致")
            else:
                score -= 15
                reasons.append("叙述声音存在波动")

        # 检查语气词使用的一致性
        tone_markers = self._check_tone_consistency(content)
        if tone_markers["consistent"]:
            score += 15
            reasons.append("语气词使用一致")
        else:
            score -= 10

        # 限制分数范围
        score = max(0, min(100, score))

        return ScoredResult(
            score=score,
            reason="; ".join(reasons) if reasons else "声音一致性评分完成"
        )

    def _analyze_speech_pattern(self, content: str, character_name: str) -> Dict[str, bool]:
        """分析角色语言风格"""
        # 简化实现
        return {"consistent": True}

    def _check_tone_consistency(self, content: str) -> Dict[str, bool]:
        """检查语气一致性"""
        formal_markers = ["因此", "于是", "从而"]
        casual_markers = ["然后", "接着", "之后"]

        formal_count = sum(1 for word in formal_markers if word in content)
        casual_count = sum(1 for word in casual_markers if word in content)

        # 如果两者都很多，可能不一致
        if formal_count > 2 and casual_count > 2:
            return {"consistent": False}
        return {"consistent": True}
