"""Phase 9.70 F62: CI contract — chapter memory RAG hook."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT


class TestChapterMemoryHookF62Contract:
    def test_hook_module_exists(self):
        mod = NOVEL_FACTORY / "infra" / "agent_system" / "chapter_memory_hook.py"
        assert mod.is_file()

    def test_runbook_documents_memory_rag(self):
        text = (NOVEL_FACTORY / "docs" / "chapter-production-runbook.md").read_text(
            encoding="utf-8"
        )
        assert "LINGWEN_MEMORY_RAG" in text
        assert "describe_memory_rag_hook" in text

    def test_hook_tests_exist(self):
        spec = NOVEL_FACTORY / "tests" / "agent_system" / "test_chapter_memory_hook.py"
        assert spec.is_file()
