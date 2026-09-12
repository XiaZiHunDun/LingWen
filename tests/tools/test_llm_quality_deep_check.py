"""Tests for tools.llm_quality.LLMQualityChecker (canonical module).

Phase 53b (C2): migrated from stale tools.llm_quality_deep_check
shim imports to canonical tools.llm_quality subpackage.

Original test file (8 ERROR + 1 FAIL) used `patch("tools.llm_quality_deep_check.LLMService")`
which:
1. Referenced a symbol that no longer exists (LLMService was renamed
   to LLMServiceAdapter during the Phase 5 LLM_QUALITY split)
2. The shim no longer re-exports LLMService (Phase 53b C1)

This rewrite uses constructor injection:
  checker = LLMQualityChecker(llm_service=mock_instance)

No patching needed — the checker accepts an llm_service parameter
that overrides the default LLMServiceAdapter() instantiation.

For the comprehensive_quality_check test, kept the canonical
tools.comprehensive_quality_check import (it was never migrated and
still works).
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest


def _make_mock_llm() -> MagicMock:
    """Return a MagicMock stand-in for LLMServiceAdapter."""
    return MagicMock()


class TestLLMQualityChecker:
    """LLMQualityChecker 核心方法测试 (canonical module)."""

    @pytest.fixture
    def mock_llm(self):
        return _make_mock_llm()

    @pytest.fixture
    def checker(self, mock_llm):
        """Create checker with injected mock LLM service."""
        from tools.llm_quality import LLMQualityChecker

        return LLMQualityChecker(llm_service=mock_llm)

    def test_load_chapter(self, checker, tmp_path):
        """测试章节加载"""
        project_root = tmp_path / "project_root"
        chapters_dir = project_root / "03_内容仓库" / "04_正文"
        chapters_dir.mkdir(parents=True)

        ch_file = chapters_dir / "ch001.md"
        ch_file.write_text("# 第一章测试内容", encoding="utf-8")

        checker.project_root = project_root
        checker.chapters_dir = chapters_dir

        content = checker.load_chapter(1)
        assert content is not None
        assert "第一章测试内容" in content

    def test_load_chapter_not_found(self, checker, tmp_path):
        """测试加载不存在的章节"""
        project_root = tmp_path / "project_root"
        chapters_dir = project_root / "03_内容仓库" / "04_正文"
        chapters_dir.mkdir(parents=True)

        checker.project_root = project_root
        checker.chapters_dir = chapters_dir

        content = checker.load_chapter(999)
        assert content is None

    def test_load_chapters(self, checker, tmp_path):
        """测试批量章节加载"""
        project_root = tmp_path / "project_root"
        chapters_dir = project_root / "03_内容仓库" / "04_正文"
        chapters_dir.mkdir(parents=True)

        for i in range(1, 4):
            ch_file = chapters_dir / f"ch{i:03d}.md"
            ch_file.write_text(f"第{i}章内容", encoding="utf-8")

        checker.project_root = project_root
        checker.chapters_dir = chapters_dir

        result = checker.load_chapters([1, 2, 3])
        assert len(result) == 3
        assert 1 in result
        assert 2 in result
        assert 3 in result

    def test_quality_report_creation(self, checker):
        """测试质检报告创建 (canonical import)"""
        from tools.llm_quality import QualityReport

        report = QualityReport(chapter=1, checker="test_checker", score=0.85)

        assert report.chapter == 1
        assert report.checker == "test_checker"
        assert report.score == 0.85
        assert report.llm_calls == 0
        assert report.timestamp != ""

    def test_quality_report_to_dict(self, checker):
        """测试质检报告序列化 (canonical import)"""
        from tools.llm_quality import QualityReport

        report = QualityReport(chapter=1, checker="test_checker", score=0.85)

        data = report.to_dict()
        assert data["chapter"] == 1
        assert data["checker"] == "test_checker"
        assert data["score"] == 0.85
        assert "timestamp" in data
        assert "issues" in data


class TestRepairMethods:
    """修复方法签名测试"""

    @pytest.fixture
    def mock_llm(self):
        return _make_mock_llm()

    @pytest.fixture
    def checker(self, mock_llm):
        from tools.llm_quality import LLMQualityChecker

        return LLMQualityChecker(llm_service=mock_llm)

    def test_check_character_consistency_exists(self, checker):
        """测试check_character_consistency方法存在"""
        assert hasattr(checker, "check_character_consistency")
        assert callable(checker.check_character_consistency)

    def test_scan_logic_contradictions_exists(self, checker):
        """测试scan_logic_contradictions方法存在"""
        assert hasattr(checker, "scan_logic_contradictions")
        assert callable(checker.scan_logic_contradictions)

    def test_verify_foreshadow_completeness_exists(self, checker):
        """测试verify_foreshadow_completeness方法存在"""
        assert hasattr(checker, "verify_foreshadow_completeness")
        assert callable(checker.verify_foreshadow_completeness)


class TestComprehensiveQualityChecker:
    """综合质量检查器测试 (separate module, not part of the shim refactor)."""

    @pytest.fixture
    def mock_api_key(self):
        return "test_api_key_12345"

    def test_chapter_file_parsing(self, mock_api_key, tmp_path):
        """测试章节文件解析"""
        # Add repo root to sys.path so tools.comprehensive_quality_check can
        # import infra.* (its legacy convention)
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        from tools.comprehensive_quality_check import ComprehensiveQualityChecker

        checker = ComprehensiveQualityChecker(api_key=mock_api_key)

        project_root = tmp_path / "project_root"
        chapters_dir = project_root / "03_内容仓库" / "04_正文"
        chapters_dir.mkdir(parents=True)

        ch_file = chapters_dir / "ch001.md"
        ch_file.write_text("# 第一章\n测试内容", encoding="utf-8")

        checker.project_root = project_root
        # C4 fix: set chapters_dir to match the test path explicitly so
        # get_chapter_files() scans the correct directory regardless of
        # the checker's default PROJECT_ROOT.
        checker.chapters_dir = chapters_dir

        files = checker.get_chapter_files()
        assert len(files) >= 1, f"Expected ≥1 chapter file, got {files}"

    def test_read_chapter(self, mock_api_key, tmp_path):
        """测试读取章节内容"""
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        from tools.comprehensive_quality_check import ComprehensiveQualityChecker

        checker = ComprehensiveQualityChecker(api_key=mock_api_key)

        project_root = tmp_path / "project_root"
        chapters_dir = project_root / "03_内容仓库" / "04_正文"
        chapters_dir.mkdir(parents=True)

        ch_file = chapters_dir / "ch999.md"
        ch_file.write_text("测试章节正文内容", encoding="utf-8")

        checker.project_root = project_root
        checker.chapters_dir = chapters_dir

        content = checker.read_chapter(999)
        assert content is not None
        assert "测试章节正文内容" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
