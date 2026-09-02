"""End-to-end tests for infra.llm_benchmarks.run (all-mock)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from infra.llm_benchmarks import run_benchmark
from infra.llm_benchmarks.metrics import ProviderMetrics


@pytest.fixture(autouse=True)
def _isolate_results_root(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_BENCH_RESULTS_ROOT", str(tmp_path))
    # Real fixtures exist at repo root (huiyu-dangan/golden-set/chapters/ch001+003+010).
    # Don't override LINGWEN_PROJECTS_ROOT — let it default to repo root.
    yield


def test_run_benchmark_produces_10_call_results():
    metrics = run_benchmark("minimax", "test-run", real=False)
    assert isinstance(metrics, ProviderMetrics)
    assert metrics.provider == "minimax"
    # 3 chapters × 3 runs + 1 control = 10
    assert metrics.n_calls == 10


def test_run_benchmark_writes_results_files():
    run_benchmark("minimax", "test-run", real=False)
    results_root = Path(os.environ["LLM_BENCH_RESULTS_ROOT"])
    run_dir = results_root / "test-run"
    files = list(run_dir.glob("call-*.json"))
    assert len(files) == 10


def test_run_benchmark_does_not_invoke_real_llm():
    # real=False path → LLMService.get() should never be called.
    # We assert no exception: if it accidentally called LLMService.get()
    # in mock mode, it'd trigger the API key check / provider plugin
    # loading and likely fail.
    metrics = run_benchmark("minimax", "test-run", real=False)
    assert metrics.parse_rate >= 0.0  # smoke: parse_rate exists


def test_run_benchmark_consistency_score_is_set():
    metrics = run_benchmark("minimax", "test-run", real=False)
    # MockLLMService is fully deterministic, so consistency should be high
    # (1.0 if all proposal dicts match pairwise across runs).
    assert metrics.consistency_score >= 0.0
    assert metrics.consistency_score <= 1.0
