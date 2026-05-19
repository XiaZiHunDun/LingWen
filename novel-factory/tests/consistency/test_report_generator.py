#!/usr/bin/env python3
"""
报告生成器测试
"""

import pytest
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from consistency.engine.report_generator import ReportGenerator
from consistency.engine.consistency_engine import ConsistencyEngine
from consistency.engine.data_structures import (
    ConsistencyReport, Issue, IssueSeverity, CheckerType, IssueLocation
)


@pytest.fixture
def sample_report():
    """创建示例报告"""
    engine = ConsistencyEngine()
    content = """
    林夜站在山崖上，望着远方的云海。

    作为一个AI，我们可以清楚地看出，这个场景充满了诗意。

    首先，他观察了云海的流动。其次，他感受了山风的气息。
    然后，他陷入了深深的沉思。最后，他转身离去。

    总之，这个场景为后续情节做了铺垫。
    """

    return engine.check_chapter(
        chapter_num=25,
        chapter_content=content
    )


@pytest.fixture
def report_generator():
    """创建报告生成器"""
    return ReportGenerator()


class TestReportGeneratorInit:
    """测试报告生成器初始化"""

    def test_default_init(self):
        generator = ReportGenerator()
        assert generator is not None
        assert generator.template is not None


class TestReportGeneratorGenerate:
    """测试报告生成"""

    def test_generate_markdown(self, report_generator, sample_report):
        result = report_generator.generate(sample_report, format="markdown")

        assert "ch25" in result
        assert "P0" in result
        assert "P1" in result
        assert "一致性检查报告" in result

    def test_generate_text(self, report_generator, sample_report):
        result = report_generator.generate(sample_report, format="text")

        assert "ch25" in result
        assert "问题汇总" in result or "P0" in result

    def test_generate_html(self, report_generator, sample_report):
        result = report_generator.generate(sample_report, format="html")

        assert "<html>" in result
        assert "ch25" in result
        assert "<table>" in result


class TestReportGeneratorFormatting:
    """测试报告格式"""

    def test_issue_details_format(self, report_generator):
        report = ConsistencyReport(chapter=25)
        report.add_issue(Issue(
            id="test_001",
            severity=IssueSeverity.P1,
            checker_type=CheckerType.CHARACTER,
            issue_type="性格冲突",
            title="角色性格-行为冲突",
            description="角色表现与设定不符",
            location=IssueLocation(chapter=25),
            evidence="设定为冷静",
            suggestion="修改为符合性格的行为",
            character="林夜"
        ))

        result = report_generator.generate(report, format="markdown")

        assert "林夜" in result
        assert "角色性格-行为冲突" in result
        assert "建议" in result

    def test_empty_issues(self, report_generator):
        report = ConsistencyReport(chapter=25)

        result = report_generator.generate(report, format="markdown")

        assert "暂无问题" in result


class TestReportGeneratorSave:
    """测试报告保存"""

    def test_save_report(self, report_generator, sample_report, tmp_path):
        output_path = tmp_path / "report.md"

        saved_path = report_generator.save_report(
            sample_report,
            str(output_path),
            format="markdown"
        )

        assert output_path.exists()
        content = output_path.read_text()
        assert "ch25" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])