"""象征约束评分器 - 方向H质量工具集"""

from typing import Any, Dict, List, Set

from soft_scorers.base import BaseScorer, ScoredResult


class SymbolismScorer(BaseScorer):
    """象征约束评分 - 评估象征元素使用"""

    weight = 0.6

    def score(self, content: str, context: Dict[str, Any]) -> ScoredResult:
        """
        评估象征使用

        好的象征使用：
        - 象征元素贯穿
        - 不过度
        - 有深意
        """
        score = 60  # 基准分
        reasons = []

        # 获取设定的象征元素
        symbols = context.get("symbols", [])
        if not symbols:
            # 如果没有设定，使用空列表
            symbols = []

        if symbols:
            # 检查设定的象征是否出现
            symbol_occurrences = self._check_symbol_occurrences(content, symbols)

            if symbol_occurrences["found"]:
                score += 20
                reasons.append("象征元素运用得当")
            else:
                score -= 10
                reasons.append("象征元素未体现")

            # 检查象征是否贯穿
            if symbol_occurrences["progressive"]:
                score += 10
                reasons.append("象征元素有递进")
        else:
            score += 10
            reasons.append("无明确象征约束")

        # 检查是否过度使用
        if self._check_excessive_symbolism(content):
            score -= 15
            reasons.append("象征使用过于频繁")

        # 限制分数范围
        score = max(0, min(100, score))

        return ScoredResult(
            score=score,
            reason="; ".join(reasons) if reasons else "象征约束评分完成"
        )

    def _check_symbol_occurrences(
        self,
        content: str,
        symbols: List[str]
    ) -> Dict[str, bool]:
        """检查象征元素出现情况"""
        content_lower = content.lower()
        found_symbols = []
        progressive = False

        for symbol in symbols:
            symbol_lower = symbol.lower()
            count = content_lower.count(symbol_lower)
            if count > 0:
                found_symbols.append(symbol)
                if count >= 3:
                    progressive = True

        return {
            "found": len(found_symbols) >= len(symbols) * 0.5 if symbols else False,
            "progressive": progressive
        }

    def _check_excessive_symbolism(self, content: str) -> bool:
        """检查是否过度使用象征"""
        # 检测同一象征词出现次数
        # 如果超过5次，认为过度
        words = content.split()
        word_counts: Dict[str, int] = {}

        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1

        excessive_count = sum(1 for count in word_counts.values() if count >= 5)
        return excessive_count >= 2