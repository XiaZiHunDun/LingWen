"""Phase 9.81 F73: CI contract — batch production runner."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT / "novel-factory"


class TestChapterProductionBatchF73:
    def test_batch_module_exists(self):
        path = NOVEL_FACTORY / "infra" / "agent_system" / "chapter_production_batch.py"
        assert path.is_file()
        text = path.read_text(encoding="utf-8")
        assert "run_production_batch" in text
        assert "MAX_BATCH_CHAPTERS" in text

    def test_runbook_section_14(self):
        runbook = NOVEL_FACTORY / "docs" / "chapter-production-runbook.md"
        text = runbook.read_text(encoding="utf-8")
        assert "## 14." in text
        assert "chapter_production_batch" in text

    def test_batch_tests_exist(self):
        spec = NOVEL_FACTORY / "tests" / "agent_system" / "test_chapter_production_batch.py"
        assert spec.is_file()
