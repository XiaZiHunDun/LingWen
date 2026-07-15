"""Phase 9.72 F64: CI contract — live-backend e2e in primary test workflow."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_CI = REPO_ROOT / ".github" / "workflows" / "dashboard-frontend-ci.yml"


class TestE2eLiveF64Contract:
    def test_primary_test_workflow_runs_live_e2e(self):
        text = FRONTEND_CI.read_text(encoding="utf-8")
        assert "LINGWEN_E2E_LIVE" in text
        assert "e2e-live:" in text
        assert "e2e:live" in text

    def test_playwright_live_project_configured(self):
        cfg = (
            REPO_ROOT
            / "dashboard"
            / "frontend"
            / "playwright.config.js"
        )
        text = cfg.read_text(encoding="utf-8")
        assert "live-backend" in text
        assert "LINGWEN_E2E_LIVE" in text
