#!/usr/bin/env python3
"""
一致性系统数据结构和Issue定义测试
"""

import pytest
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from consistency.engine.data_structures import (
    Issue, IssueSeverity, CheckerType, IssueLocation,
    ConsistencyReport, QualityDimension, CheckerResult,
    CheckScope, RealtimeIssue
)


class TestIssueSeverity:
    """测试 IssueSeverity 枚举"""

    def test_severity_values(self):
        assert IssueSeverity.P0.value == "P0"
        assert IssueSeverity.P1.value == "P1"
        assert IssueSeverity.P2.value == "P2"
        assert IssueSeverity.P3.value == "P3"


class TestCheckerType:
    """测试 CheckerType 枚举"""

    def test_checker_types(self):
        assert CheckerType.CHARACTER.value == "character_checker"
        assert CheckerType.ITEM.value == "item_checker"
        assert CheckerType.TIMELINE.value == "timeline_checker"
        assert CheckerType.ABILITY.value == "ability_checker"
        assert CheckerType.PERSONALITY.value == "personality_checker"
        assert CheckerType.FORESHADOW.value == "foreshadow_checker"
        assert CheckerType.OUTLINE.value == "outline_checker"
        assert CheckerType.AI_GLOSS.value == "ai_gloss_checker"


class TestIssueLocation:
    """测试 IssueLocation 数据类"""

    def test_location_creation(self):
        location = IssueLocation(chapter=25)
        assert location.chapter == 25
        assert location.paragraph is None

    def test_location_with_details(self):
        location = IssueLocation(
            chapter=25,
            paragraph=3,
            line=45
        )
        assert location.chapter == 25
        assert location.paragraph == 3
        assert location.line == 45

    def test_location_str(self):
        location = IssueLocation(chapter=25, paragraph=3)
        assert "ch25" in str(location)
        assert "第3段" in str(location)


class TestIssue:
    """测试 Issue 数据类"""

    def test_issue_creation(self):
        location = IssueLocation(chapter=25)
        issue = Issue(
            id="test_001",
            severity=IssueSeverity.P1,
            checker_type=CheckerType.CHARACTER,
            issue_type="性格-行为冲突",
            title="角色性格-行为冲突",
            description="角色表现与设定不符",
            location=location,
            evidence="角色设定为冷静",
            suggestion="修改为符合性格的行为"
        )

        assert issue.id == "test_001"
        assert issue.severity == IssueSeverity.P1
        assert issue.checker_type == CheckerType.CHARACTER
        assert issue.location.chapter == 25

    def test_issue_to_dict(self):
        issue = Issue(
            id="test_001",
            severity=IssueSeverity.P1,
            checker_type=CheckerType.CHARACTER,
            issue_type="测试",
            title="测试问题",
            description="测试描述",
            location=IssueLocation(chapter=25),
            character="林夜"
        )

        data = issue.to_dict()

        assert data["id"] == "test_001"
        assert data["severity"] == "P1"
        assert data["character"] == "林夜"
        assert data["location"]["chapter"] == 25

    def test_issue_from_dict(self):
        data = {
            "id": "test_001",
            "severity": "P1",
            "checker_type": "character_checker",
            "issue_type": "测试",
            "title": "测试问题",
            "description": "测试描述",
            "location": {"chapter": 25, "paragraph": 3, "line": None},
            "evidence": "",
            "suggestion": "",
            "character": "林夜",
            "created_at": datetime.now().isoformat()
        }

        issue = Issue.from_dict(data)

        assert issue.id == "test_001"
        assert issue.severity == IssueSeverity.P1
        assert issue.character == "林夜"


class TestQualityDimension:
    """测试 QualityDimension 数据类"""

    def test_quality_creation(self):
        quality = QualityDimension()
        assert quality.s1_plot_completeness == 5.0
        assert quality.s2_logic_consistency == 5.0

    def test_quality_to_dict(self):
        quality = QualityDimension(s1_plot_completeness=4.5, s2_logic_consistency=4.0)
        data = quality.to_dict()

        assert data["S1"] == 4.5
        assert data["S2"] == 4.0

    def test_quality_overall_score(self):
        quality = QualityDimension(
            s1_plot_completeness=4.0,
            s2_logic_consistency=4.0,
            s3_writing_style=4.0,
            s4_emotional_resonance=4.0,
            s5_pacing_control=4.0,
            s6_readability=4.0,
            s7_protagonist_charm=4.0,
            s8_character_arc=4.0
        )

        score = quality.overall_score()
        assert score > 0
        assert score <= 100

    def test_quality_get_dimension(self):
        quality = QualityDimension()
        dim = quality.get_dimension("S1")
        assert dim == quality.s1_plot_completeness


class TestCheckerResult:
    """测试 CheckerResult 数据类"""

    def test_checker_result_creation(self):
        result = CheckerResult(checker_type=CheckerType.CHARACTER)
        assert result.checker_type == CheckerType.CHARACTER
        assert result.issue_count == 0
        assert result.score == 100.0

    def test_checker_result_with_issues(self):
        result = CheckerResult(checker_type=CheckerType.CHARACTER)
        result.issues.append(Issue(
            id="test",
            severity=IssueSeverity.P1,
            checker_type=CheckerType.CHARACTER,
            issue_type="test",
            title="test",
            description="test",
            location=IssueLocation(chapter=1)
        ))

        assert result.issue_count == 1
        assert result.p1_count == 1
        assert result.p0_count == 0


class TestConsistencyReport:
    """测试 ConsistencyReport 数据类"""

    def test_report_creation(self):
        report = ConsistencyReport(chapter=25)
        assert report.chapter == 25
        assert report.issue_count == 0
        assert report.verdict == "pending"

    def test_report_add_issue(self):
        report = ConsistencyReport(chapter=25)
        report.add_issue(Issue(
            id="test",
            severity=IssueSeverity.P1,
            checker_type=CheckerType.CHARACTER,
            issue_type="test",
            title="test",
            description="test",
            location=IssueLocation(chapter=25)
        ))

        assert report.issue_count == 1
        assert report.p1_count == 1

    def test_report_get_issues_by_severity(self):
        report = ConsistencyReport(chapter=25)
        report.add_issue(Issue(
            id="p0",
            severity=IssueSeverity.P0,
            checker_type=CheckerType.CHARACTER,
            issue_type="test",
            title="p0",
            description="test",
            location=IssueLocation(chapter=25)
        ))
        report.add_issue(Issue(
            id="p1",
            severity=IssueSeverity.P1,
            checker_type=CheckerType.CHARACTER,
            issue_type="test",
            title="p1",
            description="test",
            location=IssueLocation(chapter=25)
        ))

        p0_issues = report.get_issues_by_severity(IssueSeverity.P0)
        assert len(p0_issues) == 1
        assert p0_issues[0].severity == IssueSeverity.P0

    def test_report_make_verdict_pass(self):
        report = ConsistencyReport(chapter=25)
        report.total_score = 95
        verdict = report.make_verdict()

        assert verdict == "pass"

    def test_report_make_verdict_fail_p0(self):
        report = ConsistencyReport(chapter=25)
        report.add_issue(Issue(
            id="p0",
            severity=IssueSeverity.P0,
            checker_type=CheckerType.CHARACTER,
            issue_type="test",
            title="p0",
            description="test",
            location=IssueLocation(chapter=25)
        ))
        verdict = report.make_verdict()

        assert verdict == "fail"

    def test_report_make_verdict_fail_p1(self):
        report = ConsistencyReport(chapter=25)
        for i in range(3):
            report.add_issue(Issue(
                id=f"p1_{i}",
                severity=IssueSeverity.P1,
                checker_type=CheckerType.CHARACTER,
                issue_type="test",
                title="p1",
                description="test",
                location=IssueLocation(chapter=25)
            ))
        verdict = report.make_verdict()

        assert verdict == "fail"

    def test_report_to_dict(self):
        report = ConsistencyReport(chapter=25)
        report.total_score = 85
        report.verdict = "review"

        data = report.to_dict()

        assert data["chapter"] == 25
        assert data["total_score"] == 85
        assert data["verdict"] == "review"


class TestRealtimeIssue:
    """测试 RealtimeIssue 数据类"""

    def test_realtime_issue_creation(self):
        issue = RealtimeIssue(
            severity=IssueSeverity.P2,
            checker_type=CheckerType.AI_GLOSS,
            message="检测到AI痕迹",
            location="第3段",
            quick_fix="使用更自然的表达"
        )

        assert issue.severity == IssueSeverity.P2
        assert issue.quick_fix == "使用更自然的表达"

    def test_realtime_issue_to_dict(self):
        issue = RealtimeIssue(
            severity=IssueSeverity.P2,
            checker_type=CheckerType.AI_GLOSS,
            message="检测到AI痕迹",
            location="第3段"
        )

        data = issue.to_dict()

        assert data["severity"] == "P2"
        assert data["checker_type"] == "ai_gloss_checker"
        assert data["message"] == "检测到AI痕迹"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])