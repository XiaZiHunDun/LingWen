"""Phase 9.80 F72: CI contract — pilot record save + runbook §13."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT


class TestChapterProductionPilotF72:
    def test_save_record_cli_flag(self):
        path = NOVEL_FACTORY / "infra" / "agent_system" / "chapter_production_pilot.py"
        text = path.read_text(encoding="utf-8")
        assert "--save-record" in text
        assert "save_pilot_record" in text
        assert "validate_pilot_record" in text

    def test_runbook_section_13(self):
        runbook = NOVEL_FACTORY / "docs" / "chapter-production-runbook.md"
        text = runbook.read_text(encoding="utf-8")
        assert "## 13." in text
        assert "--save-record" in text

    def test_stub_record_template(self):
        tpl = NOVEL_FACTORY / "docs" / "templates" / "chapter-pilot-record.stub.example.json"
        assert tpl.is_file()
        assert "stub-example" in tpl.read_text(encoding="utf-8")

    def test_pilot_record_tests(self):
        spec = NOVEL_FACTORY / "tests" / "agent_system" / "test_chapter_production_pilot.py"
        assert "TestPilotRecordF72" in spec.read_text(encoding="utf-8")
