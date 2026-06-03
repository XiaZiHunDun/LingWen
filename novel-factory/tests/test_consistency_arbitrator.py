import pytest

from infra.consistency.engine.consistency_arbitrator import (
    ArbitrationResult,
    ConsistencyArbitrator,
    IssueGroup,
)
from infra.consistency.engine.data_structures import (
    CheckerType,
    ConfidenceLevel,
    Issue,
    IssueLocation,
    IssueSeverity,
)


class TestConsistencyArbitrator:
    def test_arbitrate_empty(self):
        arb = ConsistencyArbitrator()
        result = arb.arbitrate([])
        assert len(result.resolved_issues) == 0
        assert result.arbitration_summary == "无问题可仲裁"

    def test_arbitrate_single_high_confidence(self):
        arb = ConsistencyArbitrator()
        issue = Issue(
            id="test1", severity=IssueSeverity.P1,
            checker_type=CheckerType.CHARACTER, issue_type="test",
            title="Test", description="Test",
            location=IssueLocation(chapter=1),
            confidence=ConfidenceLevel.HIGH
        )
        result = arb.arbitrate([issue])
        assert len(result.resolved_issues) == 1

    def test_arbitrate_multiple_checkers_same_location(self):
        arb = ConsistencyArbitrator()
        issue1 = Issue(
            id="test1", severity=IssueSeverity.P1,
            checker_type=CheckerType.CHARACTER, issue_type="test",
            title="Test1", description="Test1",
            location=IssueLocation(chapter=1, paragraph=3),
            confidence=ConfidenceLevel.MEDIUM
        )
        issue2 = Issue(
            id="test2", severity=IssueSeverity.P2,
            checker_type=CheckerType.ABILITY, issue_type="test",
            title="Test2", description="Test2",
            location=IssueLocation(chapter=1, paragraph=3),
            confidence=ConfidenceLevel.MEDIUM
        )
        result = arb.arbitrate([issue1, issue2])
        # 两个检查器报告同一位置 → 高置信度
        assert len(result.resolved_issues) >= 1

    def test_arbitrate_low_confidence_ambiguous(self):
        arb = ConsistencyArbitrator()
        issue = Issue(
            id="test1", severity=IssueSeverity.P2,
            checker_type=CheckerType.TIMELINE, issue_type="test",
            title="Test", description="Test",
            location=IssueLocation(chapter=5),
            confidence=ConfidenceLevel.LOW,
            confidence_score=0.3
        )
        result = arb.arbitrate([issue])
        assert len(result.ambiguous_issues) == 1
        assert result.needs_llm_review
