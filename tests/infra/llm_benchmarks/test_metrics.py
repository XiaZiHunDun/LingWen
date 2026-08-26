"""Tests for infra.llm_benchmarks.metrics."""
from __future__ import annotations

from infra.llm_benchmarks.metrics import (
    CallResult,
    ProviderMetrics,
    compute_metrics,
)


def _make_call(
    *,
    provider: str = "minimax",
    chapter_id: int = 1,
    run_index: int = 1,
    parse_ok: bool = True,
    schema_ok: bool = True,
    canon_level_ok: bool = True,
    latency_s: float = 1.0,
    output_tokens: int = 100,
    cost_usd: float = 0.001,
    failed: bool = False,
    parsed_proposals: list[dict] | None = None,
) -> CallResult:
    return CallResult(
        provider=provider,
        chapter_id=chapter_id,
        run_index=run_index,
        timestamp="2026-08-26T12:00:00Z",
        raw_response='{"proposals":[]}',
        parsed_proposals=parsed_proposals if parsed_proposals is not None else [],
        parse_ok=parse_ok,
        schema_ok=schema_ok,
        canon_level_ok=canon_level_ok,
        latency_s=latency_s,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        failed=failed,
        error=None,
    )


def test_parse_rate_counts_only_parse_ok():
    calls = [
        _make_call(parse_ok=True),
        _make_call(parse_ok=True),
        _make_call(parse_ok=True),
        _make_call(parse_ok=False),
        _make_call(parse_ok=True),
    ]
    m = compute_metrics(calls, provider="minimax")
    assert m.parse_rate == 0.8


def test_schema_compliance_counts_only_schema_ok():
    calls = [
        _make_call(parse_ok=True, schema_ok=True),
        _make_call(parse_ok=True, schema_ok=True),
        _make_call(parse_ok=True, schema_ok=False),
        _make_call(parse_ok=False, schema_ok=False),  # not counted in denominator
    ]
    m = compute_metrics(calls, provider="minimax")
    # parse_ok rate is 3/4, schema_compliance counts among parse_ok only
    assert m.schema_compliance == 2 / 3


def test_compute_metrics_returns_provider_metrics_instance():
    calls = [_make_call()]
    m = compute_metrics(calls, provider="minimax")
    assert isinstance(m, ProviderMetrics)
    assert m.provider == "minimax"
    assert m.n_calls == 1
    assert m.n_failed == 0