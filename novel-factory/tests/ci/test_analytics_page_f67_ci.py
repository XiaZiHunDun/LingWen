"""Phase 9.77 F67: CI contract — AnalyticsPage MVP."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT / "novel-factory"
FRONTEND = NOVEL_FACTORY / "dashboard" / "frontend"


class TestAnalyticsPageF67:
    def test_analytics_page_exists(self):
        page = FRONTEND / "src" / "pages" / "AnalyticsPage.vue"
        assert page.is_file()
        text = page.read_text(encoding="utf-8")
        assert "HookTrendChart" in text
        assert "production-kpi" in text

    def test_analytics_kpi_util_exists(self):
        util = FRONTEND / "src" / "utils" / "analyticsKpi.js"
        assert util.is_file()
        assert "buildProductionKpiCards" in util.read_text(encoding="utf-8")

    def test_app_wires_analytics_page(self):
        page = FRONTEND / "src" / "pages" / "InsightPage.vue"
        text = page.read_text(encoding="utf-8")
        assert "AnalyticsPage" in text
        assert "数据分析 - 开发中" not in text

    def test_vitest_specs_exist(self):
        assert (FRONTEND / "tests" / "unit" / "analytics-page.spec.ts").is_file()
        assert (FRONTEND / "tests" / "unit" / "analytics-kpi.spec.js").is_file()
