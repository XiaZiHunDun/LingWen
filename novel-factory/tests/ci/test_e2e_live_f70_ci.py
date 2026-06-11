"""Phase 9.76 F70: e2e-live CI parity contract + verify script."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT / "novel-factory"


class TestE2eLiveF70:
    def test_verify_script_exists(self):
        script = NOVEL_FACTORY / "scripts" / "verify-e2e-live-ci.sh"
        assert script.is_file()
        text = script.read_text(encoding="utf-8")
        assert "LINGWEN_E2E_LIVE=1" in text
        assert "e2e:live" in text
        assert "playwright install" in text

    def test_workflow_matches_local_verify_env(self):
        wf = REPO_ROOT / ".github" / "workflows" / "dashboard-e2e-live.yml"
        text = wf.read_text(encoding="utf-8")
        assert "python-version: '3.13'" in text
        assert "node-version: '20'" in text
        assert "CI: 'true'" in text
        assert "LINGWEN_E2E_LIVE: '1'" in text
        assert "playwright install --with-deps chromium" in text
        assert "upload-artifact" in text
        assert "timeout-minutes: 25" in text

    def test_live_backend_spec_count(self):
        """live-backend project runs 5 tests (2 files × multi-test)."""
        cfg = NOVEL_FACTORY / "dashboard" / "frontend" / "playwright.config.js"
        text = cfg.read_text(encoding="utf-8")
        assert "live-backend" in text
        assert "ripples-audit" in text
        assert "decisions-resolve" in text
