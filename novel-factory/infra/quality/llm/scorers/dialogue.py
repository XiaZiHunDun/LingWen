"""对话质量评分器 - 方向H质量工具集"""

import re
from typing import Any, Dict, List

from infra.quality.llm.scorers.base import BaseScorer, ScoredResult


class DialogueScorer(BaseScorer):
    """对话质量评分 - 评估对话的自然度和信息量"""

    weight = 1.0

    def score(self, content: str, context: Dict[str, Any]) -> ScoredResult:
        """
        评估对话质量

        高质量对话特征：
        - 对话自然，无说教感
        - 有信息增量
        - 揭示角色性格
        - 推进剧情
        """
        score = 50
        reasons = []

        # 提取对话内容
        dialogues = self._extract_dialogues(content)

        if not dialogues:
            score -= 20
            reasons.append("缺少对话内容")
            return ScoredResult(
                score=max(0, min(100, score)),
                reason="; ".join(reasons)
            )

        # 检查对话数量
        dialogue_ratio = len(" ".join(dialogues)) / len(content)
        if dialogue_ratio > 0.5:
            score += 10
            reasons.append("对话占比适中")
        elif dialogue_ratio < 0.1:
            score -= 10
            reasons.append("对话占比偏低")

        # 检查对话自然度
        natural_score = self._check_dialogue_naturalness(dialogues)
        score += natural_score

        # 检查是否揭示角色信息
        if self._check_character_revelation(dialogues):
            score += 15
            reasons.append("对话揭示了角色信息")

        # 检查是否有信息量
        if self._check_information_content(dialogues):
            score += 10
            reasons.append("对话包含有效信息")
        else:
            score -= 10
            reasons.append("对话信息量不足")

        # 限制分数范围
        score = max(0, min(100, score))

        return ScoredResult(
            score=score,
            reason="; ".join(reasons) if reasons else "对话质量评分完成"
        )

    def _extract_dialogues(self, content: str) -> List[str]:
        """提取对话内容"""
        # 匹配引号内的内容
        patterns = [
            r'"([^"]*)"',
            r'"([^"]*)"',
            r"'([^']*)'",
        ]
        dialogues = []
        for pattern in patterns:
            dialogues.extend(re.findall(pattern, content))
        return dialogues

    def _check_dialogue_naturalness(self, dialogues: List[str]) -> int:
        """检查对话自然度"""
        score = 0

        # 检查说教式表达
        preachy_markers = ["我们应该", "你必须", "大家都知道", "事实上"]
        for dialogue in dialogues:
            for marker in preachy_markers:
                if marker in dialogue:
                    score -= 10
                    break

        # 检查问句和答句的匹配
        questions = sum(1 for d in dialogues if "？" in d or "?" in d)
        if questions > 0:
            score += 5

        return score

    def _check_character_revelation(self, dialogues: List[str]) -> bool:
        """检查是否揭示角色信息"""
        # 检查对话中是否包含角色背景、情感、意图
        revelation_markers = ["因为", "所以", "我想", "我感觉", "其实"]
        return any(
            any(marker in dialogue for marker in revelation_markers)
            for dialogue in dialogues
        )

    def _check_information_content(self, dialogues: List[str]) -> bool:
        """检查对话是否有信息量"""
        # 简单实现：如果对话平均长度超过10个字，认为有信息量
        avg_length = sum(len(d) for d in dialogues) / len(dialogues) if dialogues else 0
        return avg_length > 10
