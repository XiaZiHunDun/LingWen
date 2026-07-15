"""Phase 9.87 F79: CI contract — manual batch pilot record + runbook §15."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT


class TestChapterProductionBatchF79:
    def test_runbook_section_15(self):
        runbook = NOVEL_FACTORY / "docs" / "chapter-production-runbook.md"
        text = runbook.read_text(encoding="utf-8")
        assert "## 15." in text
        assert "Manual batch pilot" in text
        assert "--save-chapter-records-dir" in text
        assert "stopped_reason" in text

    def test_batch_stub_template(self):
        tpl = NOVEL_FACTORY / "docs" / "templates" / "chapter-batch-record.stub.example.json"
        assert tpl.is_file()
        text = tpl.read_text(encoding="utf-8")
        assert "batch-ch361-363-stub" in text
        assert "chapters_succeeded" in text

    def test_batch_save_summary_cli(self):
        path = NOVEL_FACTORY / "infra" / "agent_system" / "chapter_production_batch.py"
        text = path.read_text(encoding="utf-8")
        assert "--save-summary" in text
        assert "--save-chapter-records-dir" in text
        assert "save_batch_summary" in text

    def test_v8_roadmap_f79(self):
        roadmap = (
            NOVEL_FACTORY
            / "docs"
            / "superpowers"
            / "plans"
            / "2026-06-11-followup-roadmap-v8-post-9.84.md"
        )
        assert "F79" in roadmap.read_text(encoding="utf-8")
