"""场景目的评分器 - 方向H质量工具集"""

from typing import Any, Dict, List

from quality_tools.soft_scorers.base import BaseScorer, ScoredResult


class ScenePurposeScorer(BaseScorer):
    """场景目的评分 - 评估每个场景是否有目的"""

    weight = 1.0

    def score(self, content: str, context: Dict[str, Any]) -> ScoredResult:
        """
        评估场景目的性

        有目的的特征：
        - 每个场景有明确作用
        - 推进剧情/揭示角色/渲染氛围
        - 无无意义场景
        """
        score = 50
        reasons = []

        # 获取章节目的
        chapter_purpose = context.get("chapter_purpose", "")

        if chapter_purpose:
            # 检查目的是否在内容中得到体现
            if self._check_purpose_fulfilled(content, chapter_purpose):
                score += 30
                reasons.append("章节目的充分体现")
            else:
                score -= 10
                reasons.append("章节目的体现不足")
        else:
            score += 10
            reasons.append("无明确章节目的约束")

        # 检查场景要素
        scene_elements = self._analyze_scene_elements(content)
        if scene_elements["has_conflict"]:
            score += 15
            reasons.append("场景包含冲突")
        if scene_elements["has_development"]:
            score += 10
            reasons.append("场景有发展")
        if scene_elements["has_revelation"]:
            score += 10
            reasons.append("场景有信息揭示")

        # 检查无意义场景
        if self._check_empty_scenes(content):
            score -= 15
            reasons.append("存在无意义场景")

        # 限制分数范围
        score = max(0, min(100, score))

        return ScoredResult(
            score=score,
            reason="; ".join(reasons) if reasons else "场景目的评分完成"
        )

    def _check_purpose_fulfilled(self, content: str, purpose: str) -> bool:
        """检查章节目的是否达成"""
        purpose_lower = purpose.lower()
        content_lower = content.lower()

        # 简单实现：检查目的关键词是否在内容中出现
        key_words = purpose.split()
        match_count = sum(1 for word in key_words if word in content_lower)

        return match_count >= len(key_words) * 0.5

    def _analyze_scene_elements(self, content: str) -> Dict[str, bool]:
        """分析场景要素"""
        elements = {
            "has_conflict": False,
            "has_development": False,
            "has_revelation": False
        }

        # 检查冲突
        conflict_markers = ["冲突", "矛盾", "争吵", "对立", "战斗"]
        elements["has_conflict"] = any(marker in content for marker in conflict_markers)

        # 检查发展
        development_markers = ["于是", "接着", "最终", "结果", "从而"]
        elements["has_development"] = any(marker in content for marker in development_markers)

        # 检查揭示
        revelation_markers = ["原来", "竟然", "发现", "才知道", "揭露"]
        elements["has_revelation"] = any(marker in content for marker in revelation_markers)

        return elements

    def _check_empty_scenes(self, content: str) -> bool:
        """检查是否存在空场景"""
        paragraphs = content.split("\n\n")
        empty_count = 0

        for para in paragraphs:
            # 如果段落太短（<20字符）且只有空白或简单重复，认为是空场景
            stripped = para.strip()
            if len(stripped) < 20:
                words = stripped.split()
                if len(words) <= 5:
                    empty_count += 1

        # 如果超过20%的段落是空场景，认为有问题
        return empty_count > len(paragraphs) * 0.2 if paragraphs else False