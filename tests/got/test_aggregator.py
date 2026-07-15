"""Tests for got.aggregator (JudgmentAggregator).

Phase 1.4.g — RED tests for JudgmentAggregator.

设计约束 (per Doc 4 v1.0):
- QualityReport: issues (list[Issue]) + verdict (str) + score (float)
- Issue: severity (P0/P1/P2/P3) + message + location
- JudgmentAggregator.aggregate(reports):
  - P0/P1: 严格并集 (任一报告有 → 输出有)
  - P2/P3: 并集
  - verdict: 取最严格 (FAIL > WARN > PASS)
  - score: 取最低
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pytest


# 简化的 Issue + QualityReport (本地定义,避免依赖 infra/quality)
@dataclass(frozen=True)
class Issue:
    severity: str  # "P0" / "P1" / "P2" / "P3"
    message: str
    location: str = ""


@dataclass(frozen=True)
class QualityReport:
    issues: tuple[Issue, ...] = ()
    verdict: str = "PASS"  # PASS / WARN / FAIL
    score: float = 1.0


def _p0(msg: str) -> Issue:
    return Issue(severity="P0", message=msg)


def _p1(msg: str) -> Issue:
    return Issue(severity="P1", message=msg)


def _p2(msg: str) -> Issue:
    return Issue(severity="P2", message=msg)


def _warn_report(*issues: Issue) -> QualityReport:
    return QualityReport(issues=tuple(issues), verdict="WARN", score=0.7)


def _fail_report(*issues: Issue) -> QualityReport:
    return QualityReport(issues=tuple(issues), verdict="FAIL", score=0.3)


def _pass_report() -> QualityReport:
    return QualityReport(issues=(), verdict="PASS", score=1.0)


class TestAggregatorBasics:
    def test_empty_reports(self):
        from infra.got.aggregator import JudgmentAggregator

        agg = JudgmentAggregator()
        result = agg.aggregate([])
        assert result.verdict == "PASS"
        assert result.issues == ()
        assert result.score == 1.0

    def test_single_pass_report(self):
        from infra.got.aggregator import JudgmentAggregator

        agg = JudgmentAggregator()
        result = agg.aggregate([_pass_report()])
        assert result.verdict == "PASS"
        assert result.issues == ()

    def test_single_fail_report(self):
        from infra.got.aggregator import JudgmentAggregator

        agg = JudgmentAggregator()
        result = agg.aggregate([_fail_report(_p0("crash"))])
        assert result.verdict == "FAIL"
        assert len(result.issues) == 1
        assert result.issues[0].severity == "P0"


class TestAggregatorVerdict:
    def test_strictest_verdict_wins(self):
        """verdict: FAIL > WARN > PASS"""
        from infra.got.aggregator import JudgmentAggregator

        agg = JudgmentAggregator()
        result = agg.aggregate([
            _pass_report(),
            _warn_report(_p1("warning")),
            _fail_report(_p0("critical")),
        ])
        assert result.verdict == "FAIL"

    def test_warn_overrides_pass(self):
        from infra.got.aggregator import JudgmentAggregator

        agg = JudgmentAggregator()
        result = agg.aggregate([_pass_report(), _warn_report(_p2("minor"))])
        assert result.verdict == "WARN"


class TestAggregatorIssues:
    def test_p0_strict_union(self):
        """P0 严格并集:任一报告有 → 输出有"""
        from infra.got.aggregator import JudgmentAggregator

        agg = JudgmentAggregator()
        result = agg.aggregate([
            _fail_report(_p0("error1")),
            _pass_report(),
        ])
        p0s = [i for i in result.issues if i.severity == "P0"]
        assert len(p0s) == 1
        assert p0s[0].message == "error1"

    def test_p0_from_multiple_reports(self):
        from infra.got.aggregator import JudgmentAggregator

        agg = JudgmentAggregator()
        result = agg.aggregate([
            _fail_report(_p0("e1"), _p0("e2")),
            _fail_report(_p0("e3")),
        ])
        p0s = [i for i in result.issues if i.severity == "P0"]
        assert len(p0s) == 3
        messages = sorted(p.message for p in p0s)
        assert messages == ["e1", "e2", "e3"]

    def test_p1_union_with_p0(self):
        from infra.got.aggregator import JudgmentAggregator

        agg = JudgmentAggregator()
        result = agg.aggregate([
            _fail_report(_p0("e1")),
            _warn_report(_p1("w1"), _p2("m1")),
        ])
        severities = sorted(i.severity for i in result.issues)
        assert severities == ["P0", "P1", "P2"]

    def test_no_duplicate_issues(self):
        """完全相同的 issue 不应重复出现"""
        from infra.got.aggregator import JudgmentAggregator

        agg = JudgmentAggregator()
        result = agg.aggregate([
            _warn_report(_p1("dup"), _p1("dup")),
            _warn_report(_p1("dup")),
        ])
        p1s = [i for i in result.issues if i.severity == "P1"]
        assert len(p1s) == 1


class TestAggregatorScore:
    def test_minimum_score_wins(self):
        """score: 取最低 (最严格)"""
        from infra.got.aggregator import JudgmentAggregator

        agg = JudgmentAggregator()
        result = agg.aggregate([
            _pass_report(),      # 1.0
            _warn_report(_p1("x")),  # 0.7
            _fail_report(_p0("y")),  # 0.3
        ])
        assert result.score == 0.3

    def test_pass_score_1(self):
        from infra.got.aggregator import JudgmentAggregator

        agg = JudgmentAggregator()
        result = agg.aggregate([_pass_report(), _pass_report()])
        assert result.score == 1.0


class TestAggregatorEdgeCases:
    def test_aggregate_returns_quality_report(self):
        from infra.got.aggregator import JudgmentAggregator

        agg = JudgmentAggregator()
        result = agg.aggregate([_warn_report(_p2("minor"))])
        assert isinstance(result, QualityReport)

    def test_custom_severity_order(self):
        """支持自定义严重度顺序 (P0 > P1 > P2 > P3)"""
        from infra.got.aggregator import JudgmentAggregator

        agg = JudgmentAggregator()
        # 仅 P3 应不影响 verdict (还是 WARN if 有 P2)
        result = agg.aggregate([
            _warn_report(
                Issue(severity="P3", message="low"),
            ),
            _pass_report(),
        ])
        assert result.verdict == "WARN"  # 因为有 P3
