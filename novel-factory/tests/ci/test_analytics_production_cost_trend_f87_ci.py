"""Phase 9.96 F87: CI contract — Analytics production cost trend."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT / "novel-factory"
FRONTEND = NOVEL_FACTORY / "dashboard" / "frontend"


class TestAnalyticsProductionCostTrendF87:
    def test_trend_module_and_api(self):
        mod = NOVEL_FACTORY / "infra" / "agent_system" / "production_records.py"
        text = mod.read_text(encoding="utf-8")
        assert "production_cost_trend" in text
        assert "_record_label" in text
        app = NOVEL_FACTORY / "dashboard" / "app.py"
        assert "/api/production-records/trend" in app.read_text(encoding="utf-8")

    def test_analytics_trend_util_and_chart(self):
        util = FRONTEND / "src" / "utils" / "analyticsProductionCostTrend.js"
        assert util.is_file()
        chart = FRONTEND / "src" / "components" / "ProductionCostTrendChart.vue"
        assert chart.is_file()
        page = FRONTEND / "src" / "pages" / "AnalyticsPage.vue"
        assert "production-cost-trend-kpi" in page.read_text(encoding="utf-8")
        api = FRONTEND / "src" / "api" / "index.js"
        assert "fetchProductionCostTrend" in api.read_text(encoding="utf-8")

    def test_vitest_specs_exist(self):
        assert (
            FRONTEND / "tests" / "unit" / "analytics-production-cost-trend.spec.js"
        ).is_file()
        spec = FRONTEND / "tests" / "unit" / "analytics-page.spec.ts"
        assert "production-cost-trend-kpi" in spec.read_text(encoding="utf-8")

    def test_dashboard_trend_pytest(self):
        assert (
            NOVEL_FACTORY / "tests" / "dashboard" / "test_app_production_records_trend_f87.py"
        ).is_file()
