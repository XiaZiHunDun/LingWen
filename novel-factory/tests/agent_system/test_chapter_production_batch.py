"""Phase 9.81 F73: batch chapter production runner (0 real LLM in default CI)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from infra.agent_system.chapter_production_batch import (
    BatchResult,
    build_batch_plan,
    load_calibration_from_batch,
    resolve_cost_per_chapter_usd,
    run_production_batch,
    save_batch_summary,
)
from infra.agent_system.chapter_production_pilot import PilotResult, PreflightCheck


def _ok(chapter_num: int, *, cost: float = 0.01) -> PilotResult:
    return PilotResult(
        chapter_num=chapter_num,
        workflow_name="novel_writing",
        provider="minimax",
        preflight_ok=True,
        emit_chapter_completed=True,
        completed=7,
        failed=0,
        total_cost_usd=cost,
        real_llm_gate=True,
    )


def _fail(chapter_num: int) -> PilotResult:
    return PilotResult(
        chapter_num=chapter_num,
        workflow_name="novel_writing",
        provider="minimax",
        preflight_ok=True,
        emit_chapter_completed=False,
        failed=1,
        error="emit failed",
        real_llm_gate=True,
    )


class TestRunProductionBatch:
    def test_runs_sequential_success(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LINGWEN_REAL_LLM", "1")
        monkeypatch.setenv("MINIMAX_API_KEY", "sk-test")
        calls: list[int] = []

        def runner(*, chapter_num, state_dir=None, cost_budget_usd=None, **kwargs):
            calls.append(chapter_num)
            return _ok(chapter_num, cost=0.02)

        batch = run_production_batch(
            start_chapter=361,
            max_chapters=3,
            state_dir=tmp_path,
            pilot_runner=runner,
        )
        assert calls == [361, 362, 363]
        assert batch.stopped_reason == "completed"
        assert batch.chapters_succeeded == 3
        assert batch.total_cost_usd == pytest.approx(0.06)

    def test_stop_on_fail(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LINGWEN_REAL_LLM", "1")
        monkeypatch.setenv("MINIMAX_API_KEY", "sk-test")

        def runner(*, chapter_num, **kwargs):
            if chapter_num == 362:
                return _fail(chapter_num)
            return _ok(chapter_num)

        batch = run_production_batch(
            start_chapter=361,
            max_chapters=5,
            state_dir=tmp_path,
            pilot_runner=runner,
        )
        assert batch.chapters_attempted == 2
        assert batch.chapters_succeeded == 1
        assert batch.stopped_reason == "chapter_failed"

    def test_budget_hard_stop(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LINGWEN_REAL_LLM", "1")
        monkeypatch.setenv("MINIMAX_API_KEY", "sk-test")

        def runner(*, chapter_num, **kwargs):
            return _ok(chapter_num, cost=0.05)

        batch = run_production_batch(
            start_chapter=1,
            max_chapters=5,
            state_dir=tmp_path,
            budget_usd=0.09,
            pilot_runner=runner,
        )
        assert batch.chapters_attempted == 2
        assert batch.stopped_reason == "budget_exceeded"
        assert batch.total_cost_usd == pytest.approx(0.10)

    def test_max_chapters_cap(self):
        with pytest.raises(ValueError, match="max_chapters"):
            run_production_batch(start_chapter=1, max_chapters=11)

    def test_preflight_only(self, tmp_path, monkeypatch):
        monkeypatch.delenv("LINGWEN_REAL_LLM", raising=False)
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
        batch = run_production_batch(
            start_chapter=1,
            max_chapters=3,
            state_dir=tmp_path,
            preflight_only=True,
        )
        assert batch.preflight_only is True
        assert batch.chapters_attempted == 0
        assert batch.batch_plan is not None
        assert batch.batch_plan["chapter_range"] == "1-3"
        assert batch.batch_plan["estimated_total_cost_usd"] > 0

    def test_dry_run_includes_plan(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LINGWEN_REAL_LLM", "1")
        monkeypatch.setenv("MINIMAX_API_KEY", "sk-test")
        batch = run_production_batch(
            start_chapter=364,
            max_chapters=3,
            state_dir=tmp_path,
            budget_usd=0.15,
            dry_run=True,
        )
        assert batch.dry_run is True
        assert batch.stopped_reason == "dry_run"
        assert batch.batch_plan["chapter_range"] == "364-366"
        assert batch.batch_plan["preflight_ok"] is True
        assert batch.batch_plan["estimated_chapters_within_budget"] == 3

    def test_calibrate_from_batch_json(self, tmp_path):
        path = tmp_path / "batch.json"
        path.write_text(
            json.dumps(
                {
                    "chapters_attempted": 3,
                    "total_cost_usd": 0.09,
                }
            ),
            encoding="utf-8",
        )
        cost, source = resolve_cost_per_chapter_usd(calibrate_from=path)
        assert cost == pytest.approx(0.03)
        assert "batch.json" in source

    def test_build_batch_plan_budget_headroom(self):
        checks = [
            PreflightCheck(name="real_llm_gate", passed=True, message="ok"),
        ]
        plan = build_batch_plan(
            start_chapter=361,
            max_chapters=3,
            budget_usd=0.15,
            checks=checks,
            cost_per_chapter_usd=0.027565,
            calibration_source="test",
        )
        assert plan["chapter_range"] == "361-363"
        assert plan["estimated_total_cost_usd"] == pytest.approx(0.082695, rel=1e-3)
        assert plan["budget_headroom_usd"] == pytest.approx(0.067305, rel=1e-3)

    def test_cli_dry_run(self, tmp_path, monkeypatch):
        from infra.agent_system import chapter_production_batch as mod

        monkeypatch.setenv("LINGWEN_REAL_LLM", "1")
        monkeypatch.setenv("MINIMAX_API_KEY", "sk-test")
        code = mod.main([
            "--dry-run",
            "--start-chapter", "364",
            "--max-chapters", "2",
            "--budget-usd", "0.10",
            "--state-dir", str(tmp_path),
        ])
        assert code == 0

    def test_save_batch_summary(self, tmp_path):
        batch = BatchResult(
            start_chapter=361,
            max_chapters=2,
            budget_usd=1.0,
            stopped_reason="completed",
            total_cost_usd=0.04,
            chapters_attempted=2,
            chapters_succeeded=2,
            chapter_results=[_ok(361).to_dict(), _ok(362).to_dict()],
        )
        out = tmp_path / "batch.json"
        save_batch_summary(batch, out, batch_id="test-batch")
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["batch_id"] == "test-batch"
        assert len(data["chapters"]) == 2

    def test_cli_preflight_only(self, tmp_path, monkeypatch):
        from infra.agent_system import chapter_production_batch as mod

        monkeypatch.delenv("LINGWEN_REAL_LLM", raising=False)
        code = mod.main([
            "--preflight-only",
            "--start-chapter", "361",
            "--max-chapters", "3",
            "--state-dir", str(tmp_path),
        ])
        assert code in (0, 1)
