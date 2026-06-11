"""Phase 9.74 F66: CI contract — production_summary module + runbook."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT / "novel-factory"


class TestProductionSummaryF66:
    def test_module_exists(self):
        path = NOVEL_FACTORY / "infra" / "agent_system" / "production_summary.py"
        assert path.is_file()

    def test_frontend_util_exists(self):
        path = (
            NOVEL_FACTORY
            / "dashboard"
            / "frontend"
            / "src"
            / "utils"
            / "productionSummary.js"
        )
        assert path.is_file()
        assert "productionSummaryLines" in path.read_text(encoding="utf-8")

    def test_workflow_status_response_field(self):
        app_py = NOVEL_FACTORY / "dashboard" / "app.py"
        text = app_py.read_text(encoding="utf-8")
        assert "production_summary" in text
