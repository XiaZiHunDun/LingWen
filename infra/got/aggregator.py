"""灵文 GoT · JudgmentAggregator

Phase 1.4 — Doc 4 (GoT 适配设计 v1.0) §5: 多 review 合并。

设计原则 (per Doc 4):
- P0/P1: 严格并集 (任一报告有 → 输出有)
- P2/P3: 并集
- verdict: 取最严格 (FAIL > WARN > PASS)
- score: 取最低
- issues: 去重 (按 severity + message + location)

不实施 (后续阶段):
- 加权评分 / 自定义 severity order
- LLM 仲裁冲突 (P0/P1 互相对立时)
"""
from __future__ import annotations

from typing import Any, Optional

# Verdict severity ranking (Doc 4 §5)
_VERDICT_RANK: dict[str, int] = {
    "PASS": 0,
    "WARN": 1,
    "FAIL": 2,
}


class JudgmentAggregator:
    """合并多个 QualityReport → 一个 QualityReport

    用法:
        agg = JudgmentAggregator()
        final = agg.aggregate([report1, report2, report3])

    返回类型与输入 reports 同构 (使用 type(reports[0]) 构造结果),
    支持 duck-typed QualityReport (issues/verdict/score 三字段)。
    """

    def __init__(self) -> None:
        pass

    def aggregate(self, reports: list[Any]) -> Any:
        """合并 N 个 QualityReport → 1 个

        Args:
            reports: QualityReport 列表。每个对象有:
                - issues: tuple[Issue, ...]
                - verdict: "PASS" / "WARN" / "FAIL"
                - score: float [0, 1]

        Returns:
            QualityReport: 合并后的报告 (类型与 reports[0] 同构)

        规则:
        - verdict: max(verdict_severity) — 严格性最高的胜出
        - score: min(reports.score) — 最低分胜出
        - issues: union, 去重 (按 severity+message+location)
        - 空 reports → PASS / 1.0 / () (用 _QualityReportShim 兜底)
        """
        if not reports:
            return self._empty_report()

        # 1. 合并 verdict: max severity
        verdict = max(
            (r.verdict for r in reports),
            key=lambda v: _VERDICT_RANK.get(v, 0),
        )

        # 2. 合并 score: min
        score = min(r.score for r in reports)

        # 3. 合并 issues: union + dedup (severity+message+location)
        seen: set[tuple[str, str, str]] = set()
        merged_issues: list[Any] = []
        for r in reports:
            for issue in r.issues:
                key = (issue.severity, issue.message, issue.location)
                if key in seen:
                    continue
                seen.add(key)
                merged_issues.append(issue)

        # 用 reports[0] 的类型构造,保持 isinstance 兼容
        return self._build_report(
            reports[0], issues=tuple(merged_issues), verdict=verdict, score=score
        )

    def _empty_report(self) -> Any:
        return _QualityReportShim(issues=(), verdict="PASS", score=1.0)

    def _build_report(
        self,
        template: Any,
        issues: tuple,
        verdict: str,
        score: float,
    ) -> Any:
        """用 template 报告的类构造新报告

        优先尝试 dataclass 构造 (最常见),失败则用 dict 协议。
        """
        cls = type(template)
        try:
            # dataclass 构造 (frozen 或 mutable 都支持)
            return cls(issues=issues, verdict=verdict, score=score)
        except (TypeError, ValueError):
            # 兜底: 用 shim
            return _QualityReportShim(
                issues=issues, verdict=verdict, score=score
            )


# === Shim: 兜底,用于空 reports 场景 ===
class _QualityReportShim:
    """最小可序列化 QualityReport 替身

    满足 duck-typed 接口 (issues/verdict/score),在空 reports
    场景下作为默认返回。正常场景下,aggregator 优先用输入
    reports 的类构造结果,以保持 isinstance 兼容。
    """

    __slots__ = ("issues", "verdict", "score")

    def __init__(self, issues: tuple, verdict: str, score: float) -> None:
        self.issues = issues
        self.verdict = verdict
        self.score = score

    def __repr__(self) -> str:
        return (
            f"QualityReport(issues={len(self.issues)}, "
            f"verdict={self.verdict!r}, score={self.score})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _QualityReportShim):
            return NotImplemented
        return (
            self.issues == other.issues
            and self.verdict == other.verdict
            and self.score == other.score
        )

    def __hash__(self) -> int:
        return hash((self.issues, self.verdict, self.score))


__all__ = ["JudgmentAggregator"]
