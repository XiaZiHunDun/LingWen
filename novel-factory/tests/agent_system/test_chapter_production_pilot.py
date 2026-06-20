"""Phase 9.73 F65: chapter production pilot (0 real LLM in default CI)."""
from __future__ import annotations

import json
import os

import pytest

from infra.agent_system.chapter_production_pilot import (
    PilotResult,
    PreflightCheck,
    build_pilot_initial_inputs,
    build_pilot_record,
    preflight_checklist,
    preflight_ok,
    real_llm_enabled,
    run_production_pilot,
    save_pilot_record,
    validate_pilot_record,
)
from infra.cross_volume.backfill import BackfillStats


class TestRealLlmGate:
    def test_default_off(self, monkeypatch):
        monkeypatch.delenv("LINGWEN_REAL_LLM", raising=False)
        assert real_llm_enabled() is False

    def test_enabled_with_one(self, monkeypatch):
        monkeypatch.setenv("LINGWEN_REAL_LLM", "1")
        assert real_llm_enabled() is True

    def test_pilot_llm_auto_with_key(self, monkeypatch):
        monkeypatch.delenv("LINGWEN_REAL_LLM", raising=False)
        monkeypatch.setenv("LINGWEN_PILOT_LLM", "auto")
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        assert real_llm_enabled() is True

    def test_pilot_llm_auto_without_key(self, monkeypatch):
        monkeypatch.delenv("LINGWEN_REAL_LLM", raising=False)
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("LINGWEN_PILOT_LLM", "auto")
        assert real_llm_enabled() is False


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
        monkeypatch.delenv("LINGWEN_MEMORY_RAG", raising=False)
        checks = preflight_checklist(state_dir=tmp_path)
        assert preflight_ok(checks) is True

    def test_live_memory_rag_requires_gateway(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LINGWEN_REAL_LLM", "1")
        monkeypatch.setenv("LINGWEN_MEMORY_RAG", "live")
        monkeypatch.setenv("MINIMAX_API_KEY", "sk-test")
        monkeypatch.setenv("LINGWEN_EMBEDDING_PROVIDER", "minimax")
        monkeypatch.setattr(
            "infra.agent_system.chapter_production_pilot.memory_rag_live_gateway_check",
            lambda: (False, "MemoryGateway NoOp: test"),
        )
        checks = preflight_checklist(state_dir=tmp_path)
        embed = next(c for c in checks if c.name == "embedding_provider_keys")
        assert embed.passed is True
        gate = next(c for c in checks if c.name == "memory_rag_live_gateway")
        assert gate.passed is False
        assert gate.required is True
        assert preflight_ok(checks) is False


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


class TestPilotRecordF72:
    def test_build_pilot_record_from_preflight_result(self, tmp_path, monkeypatch):
        monkeypatch.delenv("LINGWEN_REAL_LLM", raising=False)
        result = run_production_pilot(
            chapter_num=360,
            state_dir=tmp_path,
            preflight_only=True,
        )
        record = build_pilot_record(result, operator="tester")
        assert record["chapter_num"] == 360
        assert record["workflow_name"] == "novel_writing"
        assert record["operator"] == "tester"
        assert validate_pilot_record(record) == []

    def test_build_pilot_record_serializes_backfill_stats(self):
        stats = BackfillStats(
            character_count=1,
            foreshadow_count=0,
            setting_count=0,
            plot_point_count=0,
            total_count=1,
            elapsed_s=0.1,
            dry_run=False,
            nodes_written=1,
        )
        result = PilotResult(
            chapter_num=360,
            workflow_name="novel_writing",
            provider="minimax",
            preflight_ok=True,
            incremental_backfill=stats,
            emit_chapter_completed=True,
            completed=7,
            real_llm_gate=True,
        )
        record = build_pilot_record(result, operator="tester")
        assert record["hooks"]["incremental_backfill"]["nodes_written"] == 1
        assert validate_pilot_record(record) == []

    def test_validate_pilot_record_rejects_missing_keys(self):
        errors = validate_pilot_record({"chapter_num": 1})
        assert any("pilot_id" in e for e in errors)

    def test_save_pilot_record_writes_json(self, tmp_path, monkeypatch):
        monkeypatch.delenv("LINGWEN_REAL_LLM", raising=False)
        result = run_production_pilot(
            chapter_num=7,
            state_dir=tmp_path,
            preflight_only=True,
        )
        out = tmp_path / "records" / "ch007.json"
        saved = save_pilot_record(result, out, operator="ci")
        assert saved.is_file()
        assert validate_pilot_record(json.loads(saved.read_text(encoding="utf-8"))) == []

    def test_cli_save_record_preflight_only(self, tmp_path, monkeypatch):
        import json as json_mod

        from infra.agent_system import chapter_production_pilot as mod

        monkeypatch.delenv("LINGWEN_REAL_LLM", raising=False)
        out = tmp_path / "preflight.json"
        code = mod.main([
            "--preflight-only",
            "--chapter-num", "360",
            "--state-dir", str(tmp_path),
            "--save-record", str(out),
            "--operator", "cli-test",
        ])
        assert code in (0, 1)
        assert out.is_file()
        record = json_mod.loads(out.read_text(encoding="utf-8"))
        assert validate_pilot_record(record) == []


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
    def test_preflight_only_with_gate(self, tmp_path, monkeypatch):
        monkeypatch.delenv("LINGWEN_MEMORY_RAG", raising=False)
        result = run_production_pilot(
            chapter_num=1,
            state_dir=tmp_path,
            preflight_only=True,
        )
        assert result.preflight_ok is True
