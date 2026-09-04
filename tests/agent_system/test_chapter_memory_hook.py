"""Phase 9.70 F62: chapter memory RAG hook tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from lingwen_core.agents.chapter_golden_path import run_golden_path
from lingwen_core.agents.chapter_memory_hook import (
    WORKFLOWS_WITH_MEMORY,
    default_studio_memory_rag_mode,
    describe_memory_rag_hook,
    maybe_attach_memory_context,
    memory_rag_live_gateway_check,
    resolve_memory_rag_mode,
    stub_chapter_memory_context,
)


class TestChapterMemoryHookHelpers:
    def test_resolve_memory_rag_mode_env(self, monkeypatch):
        monkeypatch.delenv("LINGWEN_MEMORY_RAG", raising=False)
        assert resolve_memory_rag_mode() == "off"
        monkeypatch.setenv("LINGWEN_MEMORY_RAG", "stub")
        assert resolve_memory_rag_mode() == "stub"
        monkeypatch.setenv("LINGWEN_MEMORY_RAG", "1")
        assert resolve_memory_rag_mode() == "live"

    def test_default_studio_memory_rag_mode(self, monkeypatch):
        monkeypatch.delenv("LINGWEN_MEMORY_RAG", raising=False)
        mode = default_studio_memory_rag_mode()
        assert mode in ("live", "stub")
        monkeypatch.setenv("LINGWEN_MEMORY_RAG", "stub")
        assert default_studio_memory_rag_mode() == "stub"

    def test_stub_context_has_source_and_chapter(self):
        ctx = stub_chapter_memory_context(12)
        assert ctx["chapter"] == 12
        assert ctx["source"] == "stub"
        assert ctx["related_segments"]

    def test_maybe_attach_stub_for_golden_workflow(self):
        ctx = maybe_attach_memory_context(
            "chapter_golden",
            {"chapter_num": 7},
            mode="stub",
        )
        assert ctx is not None
        assert ctx["source"] == "stub"
        assert ctx["chapter"] == 7

    def test_maybe_attach_skips_when_off(self):
        assert (
            maybe_attach_memory_context(
                "chapter_golden",
                {"chapter_num": 7},
                mode="off",
            )
            is None
        )

    def test_maybe_attach_skips_unknown_workflow(self):
        assert (
            maybe_attach_memory_context(
                "other_workflow",
                {"chapter_num": 7},
                mode="stub",
            )
            is None
        )

    def test_maybe_attach_skips_when_memory_context_provided(self):
        existing = {"chapter": 1, "source": "manual"}
        assert (
            maybe_attach_memory_context(
                "chapter_golden",
                {"chapter_num": 7, "memory_context": existing},
                mode="stub",
            )
            is None
        )

    def test_describe_memory_rag_hook(self):
        rows = describe_memory_rag_hook()
        assert len(rows) >= 3
        assert "novel_writing" in rows[1]["behavior"]

    def test_live_mode_uses_gateway(self):
        gateway = MagicMock()
        gateway.auto_push_context.return_value = {
            "chapter": 5,
            "character_states": {"hero": {}},
            "pending_foreshadows": {},
            "recent_events": [],
            "related_segments": [],
        }
        ctx = maybe_attach_memory_context(
            "novel_writing",
            {"chapter_num": 5},
            mode="live",
            gateway=gateway,
        )
        assert ctx is not None
        assert ctx["source"] == "live"
        gateway.auto_push_context.assert_called_once_with(5)

    def test_memory_rag_live_gateway_check(self):
        # The live check is now an import probe against
        # ``lingwen_memory.gateway.memory_gateway.MemoryGateway``; runtime
        # health probes belong to the gateway itself, not the preflight.
        ok, msg = memory_rag_live_gateway_check()
        assert ok is True
        assert "MemoryGateway" in msg

    def test_memory_rag_live_gateway_check_unavailable(self, monkeypatch):
        # When the canonical symbol cannot be imported, the preflight must
        # surface a degraded (False, reason) result rather than crashing.
        import builtins

        real_import = builtins.__import__

        def _blocked(name, *args, **kwargs):
            if name == "lingwen_memory.gateway.memory_gateway":
                raise ModuleNotFoundError("simulated missing gateway")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _blocked)
        ok, msg = memory_rag_live_gateway_check()
        assert ok is False
        assert "MemoryGateway unavailable" in msg


class TestChapterMemoryHookGoldenPath:
    def test_golden_path_attaches_stub_memory_context(self, tmp_path: Path):
        result = run_golden_path(tmp_path, chapter_num=8)
        assert result.memory_context_attached is True
        assert result.memory_context_source == "stub"

    def test_workflows_with_memory_includes_golden(self):
        assert "chapter_golden" in WORKFLOWS_WITH_MEMORY
