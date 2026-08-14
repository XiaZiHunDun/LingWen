"""写审分离流程测试"""

import pytest
from infra.agent_system.reviewer import (
    ReviewerSession,
    ReviewFinding,
    ReviewResult,
    review_chapter,
    MAX_REVIEW_CYCLES,
    STOP_THRESHOLD,
)


class TestReviewFinding:
    """ReviewFinding 数据类测试"""

    def test_create_finding(self):
        finding = ReviewFinding(
            category="plot_hole",
            severity="critical",
            description="主角在第3章已死亡，第5章又出现",
            location="第5章第3段",
            suggested_fix="检查时间线或添加复活解释",
        )
        assert finding.category == "plot_hole"
        assert finding.severity == "critical"

    def test_to_dict(self):
        finding = ReviewFinding(
            category="style_issue",
            severity="minor",
            description="句子过长",
            location="第1段",
            suggested_fix="拆分为短句",
        )
        d = finding.to_dict()
        assert d["category"] == "style_issue"
        assert d["severity"] == "minor"
        assert d["description"] == "句子过长"
        assert d["location"] == "第1段"
        assert d["suggested_fix"] == "拆分为短句"

    def test_empty_defaults(self):
        finding = ReviewFinding(
            category="test",
            severity="info",
            description="测试",
        )
        assert finding.location == ""
        assert finding.suggested_fix == ""


class TestReviewResult:
    """ReviewResult 数据类测试"""

    def test_default_passed(self):
        result = ReviewResult()
        assert result.passed
        assert result.findings == []
        assert result.cycles_used == 0
        assert result.summary == ""

    def test_critical_count(self):
        findings = [
            ReviewFinding(category="a", severity="critical", description="d1"),
            ReviewFinding(category="b", severity="major", description="d2"),
            ReviewFinding(category="c", severity="critical", description="d3"),
        ]
        result = ReviewResult(findings=findings)
        assert result.critical_count == 2
        assert result.total_findings == 3

    def test_passed_with_critical(self):
        findings = [
            ReviewFinding(category="a", severity="critical", description="d1"),
        ]
        result = ReviewResult(findings=findings)
        assert result.total_findings == 1
        assert result.critical_count == 1

    def test_to_dict(self):
        findings = [
            ReviewFinding(category="plot_hole", severity="critical", description="d1"),
        ]
        result = ReviewResult(
            passed=False,
            findings=findings,
            cycles_used=2,
            summary="发现严重问题",
            suggested_fixes=["修复时间线"],
        )
        d = result.to_dict()
        assert d["passed"] is False
        assert d["cycles_used"] == 2
        assert d["summary"] == "发现严重问题"
        assert d["critical_count"] == 1
        assert d["total_findings"] == 1
        assert len(d["findings"]) == 1


class TestReviewerSession:
    """ReviewerSession 测试"""

    def test_fallback_mode(self):
        """无 router 时进入 fallback 模式"""
        session = ReviewerSession(router=None)

        result = session.review(
            chapter_content="测试章节内容",
            story_contract={"outline": "测试大纲"},
            world_model={"rules": []},
        )

        assert result.passed
        assert result.findings == []
        assert result.cycles_used == 0
        assert "FALLBACK" in result.summary

    def test_not_available_in_fallback(self):
        session = ReviewerSession(router=None)
        assert not session.is_available

    def test_is_available_with_router(self):
        mock_router = object()
        session = ReviewerSession(router=mock_router)
        assert session.is_available

    def test_default_max_cycles(self):
        session = ReviewerSession()
        assert session.max_cycles == MAX_REVIEW_CYCLES

    def test_custom_max_cycles(self):
        session = ReviewerSession(max_cycles=5)
        assert session.max_cycles == 5

    def test_default_stop_threshold(self):
        session = ReviewerSession()
        assert session.stop_threshold == STOP_THRESHOLD

    def test_reset(self):
        session = ReviewerSession()
        session._cycle_count = 3
        session.reset()
        assert session.cycles_used == 0

    def test_cycles_used_property(self):
        session = ReviewerSession()
        session._cycle_count = 2
        assert session.cycles_used == 2

    def test_review_system_prompt_present(self):
        assert ReviewerSession.REVIEW_SYSTEM_PROMPT
        assert "审稿编辑" in ReviewerSession.REVIEW_SYSTEM_PROMPT


class TestReviewChapterFunction:
    """review_chapter 便捷函数测试"""

    def test_fallback_review(self):
        result = review_chapter(
            chapter_content="测试内容",
            story_contract={},
            world_model={},
            router=None,
        )
        assert result.passed
        assert "FALLBACK" in result.summary

    def test_review_creates_independent_session(self):
        """每次调用创建独立的 ReviewerSession"""
        result1 = review_chapter("内容A", {}, {}, router=None)
        result2 = review_chapter("内容B", {}, {}, router=None)
        assert result1.cycles_used == 0
        assert result2.cycles_used == 0