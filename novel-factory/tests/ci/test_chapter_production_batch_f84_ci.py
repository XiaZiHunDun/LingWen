"""Phase 9.92 F84: CI contract — batch ch364-366 continuation + runbook §17."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT / "novel-factory"


class TestChapterProductionBatchF84:
    def test_runbook_section_17(self):
        runbook = NOVEL_FACTORY / "docs" / "chapter-production-runbook.md"
        text = runbook.read_text(encoding="utf-8")
        assert "## 17." in text
        assert "364-366" in text
        assert "batch-364-366" in text

    def test_v9_roadmap_f84(self):
        roadmap = (
            NOVEL_FACTORY
            / "docs"
            / "superpowers"
            / "plans"
            / "2026-06-11-followup-roadmap-v9-post-9.90.md"
        )
        assert roadmap.is_file()
        text = roadmap.read_text(encoding="utf-8")
        assert "F84" in text
        assert "364" in text
