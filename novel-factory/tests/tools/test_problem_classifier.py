"""Tests for tools.problem_classifier (Phase 11.11 coverage)."""
from __future__ import annotations

from infra.quality import Issue
from tools.problem_classifier import ProblemClassifier


def _issue(**kwargs) -> Issue:
    defaults = {
        "chapter": 1,
        "dimension": "一致性",
        "issue_type": "逻辑矛盾",
        "severity": "P1",
        "description": "test",
        "evidence": "",
    }
    defaults.update(kwargs)
    return Issue(**defaults)


class TestProblemClassifier:
    def setup_method(self) -> None:
        self.classifier = ProblemClassifier()

    def test_detector_issue_for_cosmic_keyword(self) -> None:
        issue = _issue(
            issue_type="时间线矛盾",
            description="宇宙级场景的时间矛盾",
            evidence="亿万年时间跨度",
        )
        assert self.classifier.classify(issue) == "DETECTOR_ISSUE"

    def test_content_issue_for_state_conflict(self) -> None:
        issue = _issue(
            issue_type="状态矛盾",
            severity="P0",
            description="角色状态前后不一致",
        )
        assert self.classifier.classify(issue, "x" * 600) == "CONTENT_ISSUE"

    def test_needs_context_short_chapter_logic(self) -> None:
        issue = _issue(issue_type="逻辑矛盾", description="前后矛盾")
        assert self.classifier.classify(issue, "短") == "NEEDS_CONTEXT"

    def test_classify_batch_groups_issues(self) -> None:
        issues = [
            _issue(issue_type="时间线矛盾", evidence="光年"),
            _issue(issue_type="状态矛盾", chapter=2),
        ]
        grouped = self.classifier.classify_batch(issues, {2: "x" * 600})
        assert len(grouped["DETECTOR_ISSUE"]) == 1
        assert len(grouped["CONTENT_ISSUE"]) == 1

    def test_get_fix_priority_p0_state(self) -> None:
        issue = _issue(issue_type="状态矛盾", severity="P0")
        assert self.classifier.get_fix_priority(issue) == 1

    def test_filter_fixable_issues_excludes_detector(self) -> None:
        issues = [
            _issue(issue_type="时间线矛盾", evidence="星际"),
            _issue(issue_type="角色行为逻辑", chapter=2),
        ]
        fixable = self.classifier.filter_fixable_issues(issues, {2: "x" * 600})
        assert len(fixable) == 1
        assert fixable[0].issue_type == "角色行为逻辑"
