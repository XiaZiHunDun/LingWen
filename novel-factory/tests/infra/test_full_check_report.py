"""Tests for full-check report parse/generate (Phase 10.07)."""
from __future__ import annotations

from pathlib import Path

from infra.consistency.engine.data_structures import (
    CheckerType,
    Issue,
    IssueLocation,
    IssueSeverity,
)
from infra.full_check_report import (
    format_report_markdown,
    generate_report,
    load_report_summary,
    parse_report_markdown,
)


def _sample_issue(chapter: int, severity: IssueSeverity, issue_type: str) -> Issue:
    return Issue(
        id=f"test-{chapter}-{issue_type}",
        severity=severity,
        checker_type=CheckerType.SENTENCE_DIVERSITY,
        issue_type=issue_type,
        title=issue_type,
        description=f"desc for {issue_type}",
        location=IssueLocation(chapter=chapter),
        evidence="sample evidence",
    )


class TestFullCheckReportMarkdown:
    def test_format_and_parse_roundtrip(self, tmp_path: Path) -> None:
        issues = [
            _sample_issue(1, IssueSeverity.P3, "AI机械过渡"),
            _sample_issue(1, IssueSeverity.P1, "sentence_diversity_low"),
        ]
        md = format_report_markdown(
            title="《测试》",
            project_root=tmp_path,
            issues=issues,
            chapters=[1],
            note="test note",
        )
        parsed = parse_report_markdown(md)
        assert parsed["total"] == 2
        assert parsed["p1"] == 1
        assert parsed["p3"] == 1
        assert len(parsed["chapters"]) == 1
        assert parsed["chapters"][0]["issue_count"] == 2

    def test_generate_for_anye_project(self) -> None:
        root = Path(__file__).resolve().parents[1] / "projects" / "anye-xinbiao"
        if not root.is_dir():
            return
        out = generate_report(root, start_chapter=1, end_chapter=3, limit=3)
        assert out.is_file()
        summary = load_report_summary(root)
        assert summary["available"] is True
        assert summary["total"] >= 0
