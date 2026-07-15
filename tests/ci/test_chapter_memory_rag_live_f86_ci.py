"""Phase 9.94 F86: CI contract — MEMORY_RAG=live preflight + runbook §19."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT


class TestChapterMemoryRagLiveF86:
    def test_memory_rag_live_preflight_script(self):
        script = NOVEL_FACTORY / "scripts" / "memory-rag-live-preflight.sh"
        assert script.is_file()
        text = script.read_text(encoding="utf-8")
        assert "F86" in text
        assert "memory_rag_live_gateway_check" in text
        assert "--preflight-only" in text

    def test_runbook_section_19(self):
        runbook = NOVEL_FACTORY / "docs" / "chapter-production-runbook.md"
        text = runbook.read_text(encoding="utf-8")
        assert "## 19." in text
        assert "memory-rag-live-preflight.sh" in text
        assert "memory_rag_live_gateway" in text

    def test_live_rag_stub_template(self):
        stub = NOVEL_FACTORY / "docs" / "templates" / "chapter-pilot-live-rag.stub.example.json"
        assert stub.is_file()
        assert '"memory_context_source": "live"' in stub.read_text(encoding="utf-8")

    def test_pilot_live_gateway_required_check(self):
        pilot = NOVEL_FACTORY / "infra" / "agent_system" / "chapter_production_pilot.py"
        text = pilot.read_text(encoding="utf-8")
        assert "memory_rag_live_gateway_check" in text
        assert 'name="memory_rag_live_gateway"' in text
        assert "required=True" in text

    def test_chapter_memory_hook_live_gateway_check(self):
        hook = NOVEL_FACTORY / "infra" / "agent_system" / "chapter_memory_hook.py"
        assert "def memory_rag_live_gateway_check" in hook.read_text(encoding="utf-8")
