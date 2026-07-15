"""Phase 9.54 F43: ECharts 6.x upgrade contract tests."""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = REPO_ROOT / "dashboard" / "frontend"


class TestEchartsUpgrade:
    def test_package_json_echarts_6(self):
        pkg = json.loads((FRONTEND_DIR / "package.json").read_text(encoding="utf-8"))
        version = pkg["dependencies"]["echarts"]
        assert version.startswith("^6."), version

    def test_lockfile_resolves_echarts_6(self):
        lock = (FRONTEND_DIR / "pnpm-lock.yaml").read_text(encoding="utf-8")
        assert "echarts@6." in lock

    def test_chart_components_use_modular_or_full_import(self):
        """Smoke: chart SFCs still import echarts (modular path unchanged in 6.x)."""
        components = [
            "CostBarChart.vue",
            "CostTrendChart.vue",
            "CascadeGraph.vue",
            "ImpactGraph.vue",
        ]
        for name in components:
            text = (FRONTEND_DIR / "src" / "components" / name).read_text(encoding="utf-8")
            assert "echarts" in text, name
