"""Phase 9.76 F70: e2e-live CI parity contract + verify script."""
from __future__ import annotations

from pathlib import Path

from playwright_live_specs import count_live_backend_tests, parse_live_backend_spec_stems

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT / "novel-factory"
FRONTEND_CI = REPO_ROOT / ".github" / "workflows" / "dashboard-frontend-ci.yml"


class TestE2eLiveF70:
    def test_verify_script_exists(self):
        script = NOVEL_FACTORY / "scripts" / "verify-e2e-live-ci.sh"
        assert script.is_file()
        text = script.read_text(encoding="utf-8")
        assert "LINGWEN_E2E_LIVE=1" in text
        assert "e2e:live" in text
        assert "playwright install" in text

    def test_workflow_matches_local_verify_env(self):
        text = FRONTEND_CI.read_text(encoding="utf-8")
        assert "python-version: \"3.12\"" in text or "python-version: '3.12'" in text
        assert "node-version: \"20\"" in text or "node-version: '20'" in text
        assert "LINGWEN_E2E_LIVE" in text
        assert "playwright install --with-deps chromium" in text
        assert "upload-artifact" in text
        assert "timeout-minutes: 25" in text

    def test_live_backend_spec_count(self):
        """live-backend project matches Human-first e2e-smoke suite."""
        stems, total = count_live_backend_tests()
        assert len(stems) >= 21
        assert total >= 63
        assert "companion-full-path-flow" in stems
        assert "companion-selection-agent-flow" in stems
