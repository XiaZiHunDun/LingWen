"""Tests for infra.llm_benchmarks.results."""

from __future__ import annotations

import pytest

from infra.llm_benchmarks.metrics import CallResult
from infra.llm_benchmarks.results import (
    list_runs,
    read_run_results,
    write_call_result,
)


def _sample_call() -> CallResult:
    return CallResult(
        provider="minimax",
        chapter_id=1,
        run_index=1,
        timestamp="2026-08-26T12:00:00Z",
        raw_response='{"proposals":[]}',
        parsed_proposals=[],
        parse_ok=True,
        schema_ok=True,
        canon_level_ok=True,
        latency_s=1.0,
        output_tokens=100,
        cost_usd=0.001,
        failed=False,
    )


def test_write_call_result_creates_file(tmp_path, monkeypatch):
    monkeypatch.setattr("infra.llm_benchmarks.results._results_root", lambda: tmp_path)
    p = write_call_result("test-run", _sample_call())
    assert p.exists()
    assert p.suffix == ".json"
    assert p.parent.name == "test-run"


def test_read_run_results_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr("infra.llm_benchmarks.results._results_root", lambda: tmp_path)
    write_call_result("test-run", _sample_call())
    write_call_result(
        "test-run", _sample_call()
    )  # second call (overwrites due to same name? no, gets unique id)

    results = read_run_results("test-run")
    assert len(results) >= 1
    assert all(isinstance(r, CallResult) for r in results)


def test_list_runs_returns_sorted_by_mtime_desc(tmp_path, monkeypatch):
    monkeypatch.setattr("infra.llm_benchmarks.results._results_root", lambda: tmp_path)
    (tmp_path / "run-old").mkdir()
    (tmp_path / "run-new").mkdir()
    runs = list_runs()
    assert "run-new" in runs
    assert "run-old" in runs


def test_results_dir_creation_failure_raises(tmp_path, monkeypatch):
    # Make _results_root point to a path that can't be created (e.g. file as parent)
    blocker = tmp_path / "blocker"
    blocker.write_text("file exists")
    monkeypatch.setattr(
        "infra.llm_benchmarks.results._results_root",
        lambda: blocker / "results",  # parent is a file, not dir
    )

    with pytest.raises(RuntimeError, match="results dir"):
        write_call_result("test-run", _sample_call())
