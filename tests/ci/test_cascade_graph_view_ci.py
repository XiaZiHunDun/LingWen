"""Phase 9.51 F40: CascadeGraph 3rd view mode contract tests."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIR = REPO_ROOT / "dashboard" / "frontend"
UTILS = FRONTEND_DIR / "src" / "utils" / "cascadeGraphUtils.js"
COMPONENT = FRONTEND_DIR / "src" / "components" / "CascadeGraph.vue"


class TestCascadeGraphViewMode:
    def test_cascade_graph_utils_exports_three_view_modes(self):
        text = UTILS.read_text(encoding="utf-8")
        assert "CASCADE_VIEW_MODES" in text
        assert "'force'" in text
        assert "'depth-layer'" in text
        assert "'action-cluster'" in text
        assert "buildCascadeChartOption" in text

    def test_cascade_graph_vue_has_view_mode_toggle_testids(self):
        text = COMPONENT.read_text(encoding="utf-8")
        assert 'data-testid="cascade-view-toggle"' in text
        assert "cascade-view-${mode}" in text or "cascade-view-`" in text
        assert "data-view-mode" in text
        assert "cascadeGraphUtils.js" in text
