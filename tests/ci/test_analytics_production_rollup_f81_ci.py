"""Phase 9.89 F81: CI contract — Analytics production rollup."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT
FRONTEND = NOVEL_FACTORY / "dashboard" / "frontend"


class TestAnalyticsProductionRollupF81:
    def test_rollup_module_and_api(self):
        mod = NOVEL_FACTORY / "infra" / "agent_system" / "production_records.py"
        text = mod.read_text(encoding="utf-8")
        assert "rollup_production_records" in text
        assert "compute_deduplicated_cost_usd" in text
        app = NOVEL_FACTORY / "dashboard" / "app.py"
        assert "/api/production-records/rollup" in app.read_text(encoding="utf-8")

    def test_analytics_rollup_util(self):
        util = FRONTEND / "src" / "utils" / "analyticsProductionRollup.js"
        assert util.is_file()
        page = FRONTEND / "src" / "pages" / "AnalyticsPage.vue"
        assert "production-rollup-kpi" in page.read_text(encoding="utf-8")
        api = FRONTEND / "src" / "api" / "index.js"
        assert "fetchProductionRollup" in api.read_text(encoding="utf-8")

    def test_vitest_specs_exist(self):
        assert (FRONTEND / "tests" / "unit" / "analytics-production-rollup.spec.js").is_file()
        spec = FRONTEND / "tests" / "unit" / "analytics-page.spec.ts"
        assert "production-rollup-kpi" in spec.read_text(encoding="utf-8")

    def test_dashboard_rollup_pytest(self):
        assert (
            NOVEL_FACTORY / "tests" / "dashboard" / "test_app_production_records_rollup_f81.py"
        ).is_file()
