"""Phase 9.93 F85: CI contract — 10-chapter wave runbook + dry-run script."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT


class TestChapterProductionBatchF85:
    def test_batch_wave_dry_run_script(self):
        script = NOVEL_FACTORY / "scripts" / "batch-wave-dry-run.sh"
        assert script.is_file()
        text = script.read_text(encoding="utf-8")
        assert "F85" in text
        assert "--dry-run" in text
        assert "367" in text

    def test_runbook_section_18(self):
        runbook = NOVEL_FACTORY / "docs" / "chapter-production-runbook.md"
        text = runbook.read_text(encoding="utf-8")
        assert "## 18." in text
        assert "367-376" in text
        assert "batch-wave-dry-run.sh" in text

    def test_wave_stub_template(self):
        stub = NOVEL_FACTORY / "docs" / "templates" / "chapter-batch-wave.stub.example.json"
        assert stub.is_file()
        assert "wave-ch367-376-stub" in stub.read_text(encoding="utf-8")

    def test_max_batch_chapters_ten(self):
        batch = NOVEL_FACTORY / "infra" / "agent_system" / "chapter_production_batch.py"
        assert "MAX_BATCH_CHAPTERS = 10" in batch.read_text(encoding="utf-8")
