"""Phase 9.72 F64: CI contract — live-backend e2e workflow."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


class TestE2eLiveF64Contract:
    def test_live_e2e_workflow_exists(self):
        wf = REPO_ROOT / ".github" / "workflows" / "dashboard-e2e-live.yml"
        assert wf.is_file()
        text = wf.read_text(encoding="utf-8")
        assert "LINGWEN_E2E_LIVE" in text
        assert "e2e-live" in text
        assert "e2e:live" in text

    def test_playwright_live_project_configured(self):
        cfg = (
            REPO_ROOT
            / "novel-factory"
            / "dashboard"
            / "frontend"
            / "playwright.config.js"
        )
        text = cfg.read_text(encoding="utf-8")
        assert "live-backend" in text
        assert "LINGWEN_E2E_LIVE" in text
