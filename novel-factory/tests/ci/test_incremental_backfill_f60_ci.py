"""Phase 9.68 F60: CI contract — incremental backfill hook productization."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT / "novel-factory"


class TestIncrementalBackfillF60Contract:
    def test_runbook_documents_hook_behavior(self):
        path = NOVEL_FACTORY / "docs" / "chapter-production-runbook.md"
        text = path.read_text(encoding="utf-8")
        assert "incremental_backfill" in text
        assert "describe_incremental_backfill_hook" in text

    def test_dashboard_api_test_exists(self):
        spec = NOVEL_FACTORY / "tests" / "dashboard" / "test_workflow_incremental_backfill.py"
        assert spec.is_file()

    def test_workflow_status_vue_has_backfill_badge(self):
        vue = (
            NOVEL_FACTORY
            / "dashboard"
            / "frontend"
            / "src"
            / "components"
            / "WorkflowStatus.vue"
        )
        text = vue.read_text(encoding="utf-8")
        assert "incremental-backfill-badge" in text
        assert "incremental_backfill" in text
