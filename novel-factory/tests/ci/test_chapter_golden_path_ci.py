"""Phase 9.67 F59: CI contract — chapter production runbook + golden path."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT / "novel-factory"


class TestChapterProductionRunbook:
    def test_runbook_exists(self):
        path = NOVEL_FACTORY / "docs" / "chapter-production-runbook.md"
        assert path.is_file()
        text = path.read_text(encoding="utf-8")
        assert "LINGWEN_INCREMENTAL_BACKFILL" in text
        assert "chapter_golden_path" in text

    def test_golden_path_module_exists(self):
        mod = NOVEL_FACTORY / "infra" / "agent_system" / "chapter_golden_path.py"
        assert mod.is_file()

    def test_golden_path_tests_exist(self):
        spec = NOVEL_FACTORY / "tests" / "agent_system" / "test_chapter_golden_path.py"
        assert spec.is_file()
