"""P2-MULTI: parallel multi-LLM batch orchestration (0 real LLM in default CI)."""

from __future__ import annotations

from pathlib import Path

import pytest
from lingwen_core.agents.chapter_production_batch import (
    assign_chapter_provider,
    run_parallel_chapters,
    run_production_batch_parallel,
    split_parallel_budget,
)
from lingwen_core.agents.chapter_production_pilot import (
    PilotResult,
    build_provider_override_config,
)


def _ok(chapter_num: int, *, cost: float = 0.01, provider: str | None = "minimax") -> PilotResult:
    return PilotResult(
        chapter_num=chapter_num,
        workflow_name="novel_writing",
        provider=provider,
        preflight_ok=True,
        emit_chapter_completed=True,
        completed=7,
        failed=0,
        total_cost_usd=cost,
        real_llm_gate=True,
    )


class TestAssignChapterProvider:
    def test_map_wins_over_default(self):
        assert (
            assign_chapter_provider(6, provider="minimax", provider_map={6: "anthropic", 7: "openai"})
            == "anthropic"
        )
        assert (
            assign_chapter_provider(7, provider="minimax", provider_map={6: "anthropic", 7: "openai"})
            == "openai"
        )

    def test_unmapped_falls_back_to_default(self):
        assert assign_chapter_provider(8, provider="minimax", provider_map={6: "anthropic"}) == "minimax"

    def test_no_provider_returns_none(self):
        assert assign_chapter_provider(6) is None


class TestSplitParallelBudget:
    def test_splits_evenly(self):
        budgets, total = split_parallel_budget(budget_usd=0.6, cost_per_chapter_usd=0.1, max_chapters=3)
        assert total == 0.6
        assert all(round(b, 6) == round(0.2, 6) for b in budgets.values())

    def test_no_budget_yields_none(self):
        budgets, total = split_parallel_budget(budget_usd=None, cost_per_chapter_usd=0.1, max_chapters=3)
        assert total == 0.0
        assert budgets == {0: None, 1: None, 2: None}


class TestRunParallelChapters:
    def test_runs_all_and_preserves_order_with_providers(self):
        seen: list[tuple[int, str | None, float | None]] = []

        def runner(*, chapter_num, state_dir=None, cost_budget_usd=None, provider=None, **kwargs):
            seen.append((chapter_num, provider, cost_budget_usd))
            return _ok(chapter_num, provider=provider)

        tasks = [(6, "minimax"), (7, "anthropic"), (8, "openai")]
        budgets = [0.2, 0.2, 0.2]
        results = run_parallel_chapters(
            tasks=tasks, runner=runner, budgets=budgets, state_dir=Path("."), max_workers=3
        )

        assert [r.chapter_num for r in results] == [6, 7, 8]
        assert [r.provider for r in results] == ["minimax", "anthropic", "openai"]
        # each task carried its own provider + budget to the runner (concurrent, so sort)
        assert sorted(seen) == [(6, "minimax", 0.2), (7, "anthropic", 0.2), (8, "openai", 0.2)]

    def test_clamps_max_workers_min_1(self):
        seen: list[int] = []

        def runner(*, chapter_num, state_dir=None, cost_budget_usd=None, provider=None, **kwargs):
            seen.append(chapter_num)
            return _ok(chapter_num, provider=provider)

        results = run_parallel_chapters(
            tasks=[(1, None), (2, None)],
            runner=runner,
            budgets=[None, None],
            state_dir=Path("."),
            max_workers=0,
        )
        assert sorted(seen) == [1, 2]
        assert [r.chapter_num for r in results] == [1, 2]


class TestBuildProviderOverrideConfig:
    def test_override_uses_requested_provider(self, monkeypatch):
        monkeypatch.setenv("MINIMAX_API_KEY", "sk-minimax")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-anthropic")
        cfg, err = build_provider_override_config(Path("/tmp"), "anthropic")
        assert err is None
        assert cfg is not None
        assert cfg.primary_provider == "anthropic"
        assert "minimax" in cfg.providers

    def test_invalid_provider_returns_error(self, monkeypatch):
        monkeypatch.setenv("MINIMAX_API_KEY", "sk-minimax")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        cfg, err = build_provider_override_config(Path("/tmp"), "openai")
        assert cfg is None
        assert err and "openai" in err

    def test_default_config_when_no_override(self, monkeypatch):
        monkeypatch.setenv("MINIMAX_API_KEY", "sk-minimax")
        cfg, err = build_provider_override_config(Path("/tmp"), None)
        assert err is None
        assert cfg is not None
        assert cfg.primary_provider == "minimax"


class TestRunProductionBatchParallelWrapper:
    def test_preflight_failure_returns_clean_shell(self, tmp_path, monkeypatch):
        # No API keys → preflight fails; wrapper must return a BatchResult, not raise.
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("LINGWEN_REAL_LLM", "1")
        batch = run_production_batch_parallel(
            start_chapter=361,
            max_chapters=2,
            state_dir=tmp_path,
            provider="minimax",
            max_workers=1,
        )
        assert batch.stopped_reason == "preflight_failed"
        assert batch.chapters_attempted == 0

    def test_rejects_invalid_chapter_count(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MINIMAX_API_KEY", "sk-minimax")
        with pytest.raises(ValueError):
            run_production_batch_parallel(start_chapter=1, max_chapters=0, state_dir=tmp_path)
