"""Phase 9.73 F65: CI contract — production pilot module + runbook §12."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NOVEL_FACTORY = REPO_ROOT


class TestChapterProductionPilotF65:
    def test_pilot_module_exists(self):
        path = NOVEL_FACTORY / "infra" / "agent_system" / "chapter_production_pilot.py"
        assert path.is_file()
        text = path.read_text(encoding="utf-8")
        assert "LINGWEN_REAL_LLM" in text
        assert "run_production_pilot" in text

    def test_runbook_section_12(self):
        runbook = NOVEL_FACTORY / "docs" / "chapter-production-runbook.md"
        text = runbook.read_text(encoding="utf-8")
        assert "## 12." in text
        assert "chapter_production_pilot" in text
        assert "LINGWEN_REAL_LLM=1" in text

    def test_pilot_record_template_exists(self):
        tpl = NOVEL_FACTORY / "docs" / "templates" / "chapter-pilot-record.example.json"
        assert tpl.is_file()
        assert "chapter_num" in tpl.read_text(encoding="utf-8")

    def test_pilot_tests_exist(self):
        spec = NOVEL_FACTORY / "tests" / "agent_system" / "test_chapter_production_pilot.py"
        assert spec.is_file()

    def test_describe_production_pilot(self):
        from infra.agent_system.chapter_production_pilot import describe_production_pilot

        rows = describe_production_pilot()
        assert len(rows) >= 3
        assert any("LINGWEN_REAL_LLM" in r.get("trigger", "") for r in rows)
