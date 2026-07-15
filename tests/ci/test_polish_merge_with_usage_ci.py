"""F27: polish_merge_synthesis *_with_usage variant contract tests.

Phase 8.7 已实现 MC variant + got_bridge handler; F27 补 CI 契约防 regression
(旧 polish_merge_synthesis 估算 path 误接 workflow cost tracking).
"""
from __future__ import annotations

import inspect
from pathlib import Path

from infra.agent_system.got_bridge import SCENARIO_HANDLERS, _handler_polish_merge
from infra.agent_system.master_controller import MasterController

REPO_ROOT = Path(__file__).resolve().parents[3]
GOT_BRIDGE_PATH = REPO_ROOT / "infra" / "agent_system" / "got_bridge.py"
MASTER_CONTROLLER_PATH = (
    REPO_ROOT / "infra" / "agent_system" / "master_controller.py"
)

WITH_USAGE_VARIANTS = (
    "write_chapter_with_usage",
    "audit_chapter_with_usage",
    "polish_chapter_with_usage",
    "polish_emotional_pacing_with_usage",
    "polish_ai_trace_removal_with_usage",
    "polish_merge_synthesis_with_usage",
)


class TestPolishMergeWithUsageContract:
    def test_master_controller_exposes_with_usage_variant(self):
        assert hasattr(MasterController, "polish_merge_synthesis_with_usage")
        sig = inspect.signature(MasterController.polish_merge_synthesis_with_usage)
        assert "content_a" in sig.parameters
        assert "content_b" in sig.parameters

    def test_legacy_polish_merge_synthesis_still_exists(self):
        """Backward compat: 旧 method 保留 (record_usage=False 估算 path)."""
        assert hasattr(MasterController, "polish_merge_synthesis")
        sig = inspect.signature(MasterController.polish_merge_synthesis)
        assert sig.return_annotation in (inspect._empty, dict) or "Dict" in str(sig.return_annotation)

    def test_got_bridge_handler_calls_with_usage_variant(self):
        source = GOT_BRIDGE_PATH.read_text(encoding="utf-8")
        handler_block = source.split("def _handler_polish_merge", 1)[1].split("\ndef _handler_", 1)[0]
        assert "polish_merge_synthesis_with_usage" in handler_block
        assert "polish_merge_synthesis(" not in handler_block.replace(
            "polish_merge_synthesis_with_usage", ""
        )

    def test_impl_uses_chat_with_usage_when_record_usage_true(self):
        source = MASTER_CONTROLLER_PATH.read_text(encoding="utf-8")
        impl_block = source.split("def _impl_polish_merge_synthesis", 1)[1].split(
            "\n    class _MergeParseError", 1
        )[0]
        assert "if record_usage:" in impl_block
        assert "chat_with_usage" in impl_block

    def test_scenario_handlers_register_polish_merge(self):
        assert SCENARIO_HANDLERS["polish_merge"] is _handler_polish_merge

    def test_six_with_usage_variants_on_master_controller(self):
        for name in WITH_USAGE_VARIANTS:
            assert hasattr(MasterController, name), name
