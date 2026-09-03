"""Phase 9.74 F66: CI contract — production_summary module + runbook."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NOVEL_FACTORY = REPO_ROOT


class TestProductionSummaryF66:
    def test_module_exists(self):
        path = (
            NOVEL_FACTORY
            / "packages"
            / "lingwen-core"
            / "src"
            / "lingwen_core"
            / "agents"
            / "production_summary.py"
        )
        assert path.is_file()

    def test_frontend_util_exists(self):
        path = NOVEL_FACTORY / "apps" / "dashboard" / "src" / "utils" / "productionSummary.js"
        assert path.is_file()
        assert "productionSummaryLines" in path.read_text(encoding="utf-8")

    def test_workflow_status_response_field(self):
        protocols_py = NOVEL_FACTORY / "apps" / "studio_api" / "protocols.py"
        text = protocols_py.read_text(encoding="utf-8")
        assert "production_summary" in text
