"""核心道具贯穿检查器测试"""

import tempfile
from pathlib import Path

import pytest
from lingwen_quality.consistency.checkers.core_props_checker import CorePropsChecker, PropIssue


class TestCorePropsChecker:
    """CorePropsChecker 测试"""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_init_with_chapters_dir(self):
        checker = CorePropsChecker(chapters_dir=self.tmpdir)
        assert checker.chapters_dir == Path(self.tmpdir)

    def test_extract_ch1_props_no_file(self):
        checker = CorePropsChecker(chapters_dir=self.tmpdir)
        props = checker.extract_ch1_props()
        assert props == []

    def test_extract_ch1_props_with_content(self):
        ch1_dir = Path(self.tmpdir)
        ch1_file = ch1_dir / "ch001.md"
        ch1_file.write_text(
            "这是一段文字。【道具:木勺】出现在这里。【道具:地窖】也在这里。母亲在厨房忙碌，父亲在院子里。"
        )
        checker = CorePropsChecker(chapters_dir=self.tmpdir)
        props = checker.extract_ch1_props()
        assert "木勺" in props
        assert "地窖" in props
        # 强制道具自动检测
        assert "母亲" in props
        assert "父亲" in props

    def test_check_reappear_no_chapters(self):
        checker = CorePropsChecker(chapters_dir=self.tmpdir)
        count = checker.check_reappear("木勺")
        assert count == 0

    def test_check_reappear_with_chapters(self):
        ch_dir = Path(self.tmpdir)
        ch1_file = ch_dir / "ch001.md"
        ch1_file.write_text("第1章内容。木勺。")
        ch2_file = ch_dir / "ch002.md"
        ch2_file.write_text("第2章内容。木勺出现。")
        ch3_file = ch_dir / "ch003.md"
        ch3_file.write_text("第3章内容。木勺又出现了。")
        ch5_file = ch_dir / "ch005.md"
        ch5_file.write_text("第5章内容。木勺还在。")

        checker = CorePropsChecker(chapters_dir=self.tmpdir)
        count = checker.check_reappear("木勺")
        assert count == 3  # 第2、3、5章

    def test_check_reappear_skips_ch1(self):
        ch_dir = Path(self.tmpdir)
        ch1 = ch_dir / "ch001.md"
        ch1.write_text("第1章。木勺。")
        ch2 = ch_dir / "ch002.md"
        ch2.write_text("第2章没有。")

        checker = CorePropsChecker(chapters_dir=self.tmpdir)
        count = checker.check_reappear("木勺")
        assert count == 0  # 第2章没有木勺，第1章跳过

    def test_check_all_empty(self):
        checker = CorePropsChecker(chapters_dir=self.tmpdir)
        issues = checker.check_all()
        assert issues == []

    def test_check_all_with_missing_props(self):
        ch_dir = Path(self.tmpdir)
        ch1 = ch_dir / "ch001.md"
        ch1.write_text("木勺。【道具:木勺】这里出现了。")
        ch2 = ch_dir / "ch002.md"
        ch2.write_text("第2章内容，没有。")
        ch3 = ch_dir / "ch003.md"
        ch3.write_text("第3章内容，也没有。")

        checker = CorePropsChecker(chapters_dir=self.tmpdir)
        issues = checker.check_all()
        assert len(issues) == 1
        assert issues[0].prop_name == "木勺"
        assert issues[0].severity == "HIGH"

    def test_check_all_with_insufficient_reappear(self):
        ch_dir = Path(self.tmpdir)
        ch1 = ch_dir / "ch001.md"
        ch1.write_text("木勺。")
        ch2 = ch_dir / "ch002.md"
        ch2.write_text("木勺出现一次。")

        checker = CorePropsChecker(chapters_dir=self.tmpdir)
        issues = checker.check_all()
        assert len(issues) == 1
        assert issues[0].severity == "MEDIUM"
        assert "1次" in issues[0].description

    def test_check_chapter_1_returns_empty(self):
        ch_dir = Path(self.tmpdir)
        ch1 = ch_dir / "ch001.md"
        ch1.write_text("木勺。")
        checker = CorePropsChecker(chapters_dir=self.tmpdir)
        context = {}
        issues = checker.check("", 1, context)
        assert issues == []
        assert "ch1_props" in context

    def test_check_non_ch1_returns_empty(self):
        checker = CorePropsChecker(chapters_dir=self.tmpdir)
        issues = checker.check("章节内容", 5, {})
        assert issues == []

    def test_generate_report_empty(self):
        checker = CorePropsChecker(chapters_dir=self.tmpdir)
        report = checker.generate_report([])
        assert "通过" in report

    def test_generate_report_with_issues(self):
        issues = [
            PropIssue(chapter="ch001", prop_name="木勺", severity="HIGH", description="道具'木勺'完全消失"),
            PropIssue(chapter="ch001", prop_name="地窖", severity="MEDIUM", description="道具'地窖'再现不足"),
        ]
        checker = CorePropsChecker(chapters_dir=self.tmpdir)
        report = checker.generate_report(issues)
        assert "HIGH级问题: 1" in report
        assert "MEDIUM级问题: 1" in report
        assert "必须修复" in report


class TestPropIssue:
    """PropIssue 数据类测试"""

    def test_create(self):
        issue = PropIssue(
            chapter="ch001",
            prop_name="木勺",
            severity="HIGH",
            description="道具完全消失",
        )
        assert issue.chapter == "ch001"
        assert issue.prop_name == "木勺"
        assert issue.severity == "HIGH"
        assert issue.description == "道具完全消失"
