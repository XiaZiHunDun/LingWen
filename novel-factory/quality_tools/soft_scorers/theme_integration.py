"""主题整合评分器 - 方向H质量工具集"""

from typing import Any, Dict, List, Set

from quality_tools.soft_scorers.base import BaseScorer, ScoredResult


class ThemeIntegrationScorer(BaseScorer):
    """主题整合评分 - 评估主题是否贯穿"""

    weight = 0.8

    def score(self, content: str, context: Dict[str, Any]) -> ScoredResult:
        """
        评估主题整合

        高整合度特征：
        - 主题关键词贯穿全文
        - 无割裂感
        - 主题有递进/呼应
        """
        score = 50
        reasons = []

        # 获取设定的主题
        themes = context.get("themes", [])
        if not themes:
            # 如果没有设定，尝试从内容中提取
            themes = self._extract_themes(content)

        if themes:
            # 检查主题词出现次数
            theme_occurrences = self._count_theme_occurrences(content, themes)

            # 计算主题覆盖度
            coverage = len(theme_occurrences) / len(themes) if themes else 0

            if coverage >= 0.8:
                score += 25
                reasons.append("主题贯穿充分")
            elif coverage >= 0.5:
                score += 15
                reasons.append("主题有一定贯穿")
            else:
                score -= 10
                reasons.append("主题贯穿不足")

            # 检查主题递进/呼应
            if self._check_theme_progression(content, themes):
                score += 15
                reasons.append("主题有递进或呼应")
        else:
            score += 10
            reasons.append("无明确主题约束")

        # 限制分数范围
        score = max(0, min(100, score))

        return ScoredResult(
            score=score,
            reason="; ".join(reasons) if reasons else "主题整合评分完成"
        )

    def _extract_themes(self, content: str) -> List[str]:
        """从内容中提取主题词（简化实现）"""
        # 这里应该用 NLP 或 LLM 来提取
        # 简化实现返回空列表
        return []

    def _count_theme_occurrences(self, content: str, themes: List[str]) -> Set[str]:
        """统计主题词出现情况"""
        found = set()
        content_lower = content.lower()

        for theme in themes:
            if theme.lower() in content_lower:
                found.add(theme)

        return found

    def _check_theme_progression(self, content: str, themes: List[str]) -> bool:
        """检查主题是否有递进或呼应"""
        # 简化实现：检查主题词是否在开头和结尾都出现
        if len(themes) < 2:
            return True

        first_100 = content[:100].lower()
        last_100 = content[-100:].lower()

        themes_in_intro = sum(1 for t in themes if t.lower() in first_100)
        themes_in_conclusion = sum(1 for t in themes if t.lower() in last_100)

        # 如果首尾都有主题词，认为有呼应
        return themes_in_intro > 0 and themes_in_conclusion > 0