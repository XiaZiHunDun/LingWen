"""Persist CallResults to disk as JSON, grouped per run.

Writes to infra/llm_benchmarks/results/<run-id>/call-NNN.json.
Directory creation failure is a fail-fast blocker (per spec §6).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from infra.llm_benchmarks.metrics import CallResult


def _results_root() -> Path:
    """Resolve results/ root. Allow override for tests."""
    env = os.environ.get("LLM_BENCH_RESULTS_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent / "results"


def _next_call_index(run_dir: Path) -> int:
    existing = sorted(run_dir.glob("call-*.json"))
    if not existing:
        return 1
    last = existing[-1].stem  # call-007
    try:
        return int(last.split("-")[1]) + 1
    except (IndexError, ValueError):
        return len(existing) + 1


def write_call_result(run_id: str, result: CallResult) -> Path:
    """Persist one CallResult to results/<run_id>/call-NNN.json.

    Returns the written path. Raises RuntimeError if results dir creation
    fails (blocker per spec §6).
    """
    root = _results_root()
    run_dir = root / run_id
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(f"results dir create failed: {run_dir}: {exc}") from exc

    idx = _next_call_index(run_dir)
    path = run_dir / f"call-{idx:03d}.json"
    path.write_text(
        json.dumps(result.__dict__, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def read_run_results(run_id: str) -> list[CallResult]:
    """Read all call-NNN.json under results/<run_id>/."""
    run_dir = _results_root() / run_id
    if not run_dir.exists():
        return []
    out: list[CallResult] = []
    for path in sorted(run_dir.glob("call-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        out.append(CallResult(**data))
    return out


def list_runs() -> list[str]:
    """List run_ids under results/, sorted by mtime desc."""
    root = _results_root()
    if not root.exists():
        return []
    runs = [p.name for p in root.iterdir() if p.is_dir()]
    runs.sort(key=lambda r: (root / r).stat().st_mtime, reverse=True)
    return runs
