"""Phase 9.88 F80: CI contract — batch dry-run + batch_plan."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NOVEL_FACTORY = REPO_ROOT


class TestChapterProductionBatchF80:
    def test_dry_run_cli_flag(self):
        path = NOVEL_FACTORY / "infra" / "agent_system" / "chapter_production_batch.py"
        text = path.read_text(encoding="utf-8")
        assert "--dry-run" in text
        assert "build_batch_plan" in text
        assert "batch_plan" in text
        assert "resolve_cost_per_chapter_usd" in text

    def test_runbook_section_16(self):
        runbook = NOVEL_FACTORY / "docs" / "chapter-production-runbook.md"
        text = runbook.read_text(encoding="utf-8")
        assert "## 16." in text
        assert "--dry-run" in text
        assert "batch_plan" in text
        assert "calibrate-from" in text

    def test_batch_tests_cover_f80(self):
        spec = NOVEL_FACTORY / "tests" / "agent_system" / "test_chapter_production_batch.py"
        text = spec.read_text(encoding="utf-8")
        assert "test_dry_run_includes_plan" in text
        assert "test_calibrate_from_batch_json" in text
