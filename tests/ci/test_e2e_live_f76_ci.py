"""Phase 9.84 F76: remote e2e-live checklist + workflow summary step."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NOVEL_FACTORY = REPO_ROOT
FRONTEND_CI = REPO_ROOT / ".github" / "workflows" / "dashboard-frontend-ci.yml"


class TestE2eLiveRemoteF76:
    def test_remote_checklist_script(self):
        script = NOVEL_FACTORY / "scripts" / "e2e-live-remote-checklist.sh"
        assert script.is_file()
        text = script.read_text(encoding="utf-8")
        assert "F76" in text
        assert "workflow_dispatch" in text or "Run workflow" in text

    def test_runbook_section_11_2(self):
        runbook = NOVEL_FACTORY / "docs" / "chapter-production-runbook.md"
        text = runbook.read_text(encoding="utf-8")
        assert "## 11.2" in text
        assert "e2e-live-remote-checklist.sh" in text

    def test_primary_test_workflow_has_job_summary(self):
        text = FRONTEND_CI.read_text(encoding="utf-8")
        assert "e2e-live:" in text
        assert "Upload Playwright trace on failure" in text
