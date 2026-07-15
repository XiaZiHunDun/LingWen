"""过渡流畅度评分器 - 方向H质量工具集"""

import re
from typing import Any, Dict

from infra.quality.llm.scorers.base import BaseScorer, ScoredResult


class TransitionScorer(BaseScorer):
    """过渡流畅度评分 - 评估场景/段落过渡"""

    weight = 0.9

    def score(self, content: str, context: Dict[str, Any]) -> ScoredResult:
        """
        评估过渡流畅度

        高流畅度特征：
        - 过渡词自然
        - 场景切换平滑
        - 无突兀跳转
        """
        score = 50
        reasons = []

        # 检查过渡词使用
        transition_words = [
            "于是", "然后", "接着", "之后", "此时", "与此同时",
            "与此同时", "不一会儿", "没过多久", "片刻之后",
            "然而", "但", "可是", "只是", "没想到"
        ]
        transition_count = sum(1 for word in transition_words if word in content)

        if transition_count >= 3:
            score += 20
            reasons.append("过渡词使用充分")
        elif transition_count >= 1:
            score += 10
            reasons.append("有过渡词使用")
        else:
            score -= 10
            reasons.append("缺乏过渡词")

        # 检查场景切换平滑度
        scene_switch_score = self._check_scene_switch_smoothness(content)
        score += scene_switch_score

        # 检查段落间逻辑连接
        if self._check_paragraph_connection(content):
            score += 15
            reasons.append("段落连接自然")
        else:
            score -= 10
            reasons.append("段落连接略显突兀")

        # 限制分数范围
        score = max(0, min(100, score))

        return ScoredResult(
            score=score,
            reason="; ".join(reasons) if reasons else "过渡流畅度评分完成"
        )

    def _check_scene_switch_smoothness(self, content: str) -> int:
        """检查场景切换平滑度"""
        # 检测场景切换标记
        scene_switch_markers = [
            "来到", "进入", "走到", "穿过", "回到",
            "此时", "下一刻", "转瞬间"
        ]
        count = sum(1 for marker in scene_switch_markers if marker in content)

        if count >= 2:
            return 15
        elif count == 1:
            return 5
        return 0

    def _check_paragraph_connection(self, content: str) -> bool:
        """检查段落连接"""
        paragraphs = content.split("\n\n")
        if len(paragraphs) < 2:
            return True

        # 检查段落之间是否有连接词
        connection_markers = ["他", "她", "但是", "然而", "因此", "于是"]
        connected_count = 0

        for i in range(len(paragraphs) - 1):
            next_para = paragraphs[i + 1]
            if any(marker in next_para for marker in connection_markers):
                connected_count += 1

        # 如果超过一半的段落间有连接词，认为连接良好
        return connected_count >= (len(paragraphs) - 1) / 2
