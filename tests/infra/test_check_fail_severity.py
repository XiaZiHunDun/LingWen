"""Tests for check --fail-severity gate (Phase 10.38)."""
from infra.cli.commands.check import _issues_meet_fail_threshold
from infra.consistency.engine.data_structures import (
    CheckerType,
    Issue,
    IssueLocation,
    IssueSeverity,
)


def _issue(sev: IssueSeverity) -> Issue:
    return Issue(
        id="t",
        severity=sev,
        checker_type=CheckerType.CHARACTER_AGENCY,
        issue_type="test",
        title="t",
        description="d",
        location=IssueLocation(chapter=1),
    )


def test_fail_severity_p0_only_blocks_p0():
    issues = [_issue(IssueSeverity.P1), _issue(IssueSeverity.P2)]
    assert not _issues_meet_fail_threshold(issues, "P0")


def test_fail_severity_p0_blocks_p0():
    issues = [_issue(IssueSeverity.P1), _issue(IssueSeverity.P0)]
    assert _issues_meet_fail_threshold(issues, "P0")


def test_no_fail_severity_blocks_any_issue():
    issues = [_issue(IssueSeverity.P3)]
    assert _issues_meet_fail_threshold(issues, None)
