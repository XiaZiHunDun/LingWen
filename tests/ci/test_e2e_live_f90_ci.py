"""Phase 9.98 F90: CI contract — e2e-live first-green JSON record tooling."""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT


class TestE2eLiveF90:
    def test_ci_records_module(self):
        mod = NOVEL_FACTORY / "infra" / "agent_system" / "ci_records.py"
        text = mod.read_text(encoding="utf-8")
        assert "validate_e2e_live_first_green_record" in text
        assert "write_e2e_live_first_green_record" in text

    def test_write_record_script(self):
        script = NOVEL_FACTORY / "scripts" / "write-e2e-live-first-green-record.sh"
        assert script.is_file()
        text = script.read_text(encoding="utf-8")
        assert "F90" in text
        assert "verify-e2e-live-ci.sh" in text

    def test_runbook_section_11_4(self):
        runbook = NOVEL_FACTORY / "docs" / "chapter-production-runbook.md"
        text = runbook.read_text(encoding="utf-8")
        assert "### 11.4 F90" in text
        assert "write-e2e-live-first-green-record.sh" in text

    def test_stub_validates_with_ci_records(self):
        from infra.agent_system.ci_records import validate_e2e_live_first_green_record

        stub = NOVEL_FACTORY / "docs" / "templates" / "e2e-live-first-green.stub.example.json"
        data = json.loads(stub.read_text(encoding="utf-8"))
        assert validate_e2e_live_first_green_record(data) == []

    def test_v9_roadmap_f90(self):
        roadmap = (
            NOVEL_FACTORY
            / "docs"
            / "superpowers"
            / "plans"
            / "2026-06-11-followup-roadmap-v9-post-9.90.md"
        )
        assert "F90" in roadmap.read_text(encoding="utf-8")

    def test_ci_records_pytest(self):
        assert (NOVEL_FACTORY / "tests" / "agent_system" / "test_ci_records.py").is_file()
