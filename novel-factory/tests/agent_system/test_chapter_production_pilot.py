"""Phase 9.73 F65: chapter production pilot (0 real LLM in default CI)."""
from __future__ import annotations

import os

import pytest

from infra.agent_system.chapter_production_pilot import (
    PilotResult,
    PreflightCheck,
    build_pilot_initial_inputs,
    preflight_checklist,
    preflight_ok,
    real_llm_enabled,
    run_production_pilot,
)


class TestRealLlmGate:
    def test_default_off(self, monkeypatch):
        monkeypatch.delenv("LINGWEN_REAL_LLM", raising=False)
        assert real_llm_enabled() is False

    def test_enabled_with_one(self, monkeypatch):
        monkeypatch.setenv("LINGWEN_REAL_LLM", "1")
        assert real_llm_enabled() is True


class TestPreflightChecklist:
    def test_preflight_only_does_not_require_gate(self, tmp_path, monkeypatch):
        monkeypatch.delenv("LINGWEN_REAL_LLM", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
        checks = preflight_checklist(
            state_dir=tmp_path,
            require_real_llm_gate=False,
        )
        names = {c.name for c in checks}
        assert "real_llm_gate" in names
        assert "workflow_yaml" in names
        gate = next(c for c in checks if c.name == "real_llm_gate")
        assert gate.passed is True

    def test_preflight_requires_api_key(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LINGWEN_REAL_LLM", "1")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
        checks = preflight_checklist(state_dir=tmp_path)
        api = next(c for c in checks if c.name == "api_key")
        assert api.passed is False
        assert preflight_ok(checks) is False

    def test_preflight_passes_with_key_and_gate(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LINGWEN_REAL_LLM", "1")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        checks = preflight_checklist(state_dir=tmp_path)
        assert preflight_ok(checks) is True


class TestBuildPilotInitialInputs:
    def test_use_llm_true(self):
        inputs = build_pilot_initial_inputs(42)
        assert inputs["chapter_num"] == 42
        assert inputs["use_llm"] is True
        assert inputs["outline"]["chapters"][0]["num"] == 42


class TestRunProductionPilotStubbed:
    def test_blocks_without_real_llm_gate(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        monkeypatch.delenv("LINGWEN_REAL_LLM", raising=False)
        result = run_production_pilot(chapter_num=1, state_dir=tmp_path)
        assert isinstance(result, PilotResult)
        assert result.error == "preflight failed; fix checklist before running pilot"
        assert result.preflight_ok is False

    def test_preflight_only_no_run(self, tmp_path, monkeypatch):
        monkeypatch.delenv("LINGWEN_REAL_LLM", raising=False)
        result = run_production_pilot(
            chapter_num=5,
            state_dir=tmp_path,
            preflight_only=True,
        )
        assert result.preflight_only is True
        assert result.completed == 0
        assert result.error is None

    def test_cli_main_preflight_only(self, tmp_path, monkeypatch):
        from infra.agent_system import chapter_production_pilot as mod

        monkeypatch.delenv("LINGWEN_REAL_LLM", raising=False)
        code = mod.main(
            ["--preflight-only", "--state-dir", str(tmp_path), "--chapter-num", "2"],
        )
        assert code in (0, 1)


_REQUIRES_REAL_LLM = pytest.mark.skipif(
    os.environ.get("LINGWEN_REAL_LLM", "").lower() not in ("1", "true", "yes")
    or not (
        os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("MINIMAX_API_KEY")
    ),
    reason="opt-in: LINGWEN_REAL_LLM=1 + API key required",
)


@_REQUIRES_REAL_LLM
class TestProductionPilotRealLlmOptIn:
    def test_preflight_only_with_gate(self, tmp_path):
        result = run_production_pilot(
            chapter_num=1,
            state_dir=tmp_path,
            preflight_only=True,
        )
        assert result.preflight_ok is True
