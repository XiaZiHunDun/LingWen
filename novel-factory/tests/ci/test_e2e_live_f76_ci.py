"""Phase 9.84 F76: remote e2e-live checklist + workflow summary step."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT / "novel-factory"


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

    def test_workflow_job_summary_step(self):
        wf = REPO_ROOT / ".github" / "workflows" / "dashboard-e2e-live.yml"
        text = wf.read_text(encoding="utf-8")
        assert "GITHUB_STEP_SUMMARY" in text
        assert "Write job summary" in text
