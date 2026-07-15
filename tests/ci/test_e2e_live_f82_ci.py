"""Phase 9.90 F82: CI contract — remote e2e-live first-green confirmation."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT


class TestE2eLiveF82:
    def test_first_green_checklist_script(self):
        script = NOVEL_FACTORY / "scripts" / "e2e-live-first-green-checklist.sh"
        assert script.is_file()
        text = script.read_text(encoding="utf-8")
        assert "F82" in text
        assert "verify-e2e-live-ci.sh" in text

    def test_runbook_section_11_3(self):
        runbook = NOVEL_FACTORY / "docs" / "chapter-production-runbook.md"
        text = runbook.read_text(encoding="utf-8")
        assert "### 11.3 F82" in text
        assert "e2e-live-first-green-checklist.sh" in text

    def test_first_green_stub_template(self):
        stub = NOVEL_FACTORY / "docs" / "templates" / "e2e-live-first-green.stub.example.json"
        assert stub.is_file()
        assert "github_run_id" in stub.read_text(encoding="utf-8")

    def test_v8_roadmap_f82(self):
        roadmap = (
            NOVEL_FACTORY
            / "docs"
            / "superpowers"
            / "plans"
            / "2026-06-11-followup-roadmap-v8-post-9.84.md"
        )
        assert "F82" in roadmap.read_text(encoding="utf-8")
