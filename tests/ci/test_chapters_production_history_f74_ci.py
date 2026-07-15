"""Phase 9.82 F74: CI contract — ChaptersPage production history."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT
FRONTEND = NOVEL_FACTORY / "dashboard" / "frontend"


class TestChaptersProductionHistoryF74:
    def test_production_records_module(self):
        path = NOVEL_FACTORY / "infra" / "agent_system" / "production_records.py"
        assert path.is_file()
        assert "list_production_records" in path.read_text(encoding="utf-8")

    def test_api_endpoint(self):
        app = NOVEL_FACTORY / "dashboard" / "app.py"
        assert "/api/production-records" in app.read_text(encoding="utf-8")

    def test_chapters_page_history_panel(self):
        page = FRONTEND / "src" / "pages" / "ChaptersPage.vue"
        text = page.read_text(encoding="utf-8")
        assert "production-history-panel" in text
        assert "fetchProductionRecords" in text

    def test_production_records_util(self):
        util = FRONTEND / "src" / "utils" / "productionRecords.js"
        assert util.is_file()

    def test_vitest_specs_exist(self):
        assert (FRONTEND / "tests" / "unit" / "production-records.spec.js").is_file()
