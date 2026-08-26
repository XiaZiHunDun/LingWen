"""Tests for infra.llm_benchmarks.render."""
from __future__ import annotations

from infra.llm_benchmarks.metrics import ProviderMetrics
from infra.llm_benchmarks.render import render_report


def _m(
    name: str,
    *,
    parse_rate: float = 0.9,
    schema: float = 0.8,
    canon: float = 1.0,
    cost: float = 0.001,
    p50: float = 1.0,
    p95: float = 2.0,
    consistency: float = 1.0,
    confidence: dict[str, int] | None = None,
) -> ProviderMetrics:
    return ProviderMetrics(
        provider=name,
        n_calls=10,
        n_failed=0,
        parse_rate=parse_rate,
        schema_compliance=schema,
        canon_level_compliance=canon,
        confidence_distribution=confidence or {"high": 5, "medium": 3, "low": 1},
        latency_p50_s=p50,
        latency_p95_s=p95,
        cost_per_call_usd=cost,
        consistency_score=consistency,
    )


def test_render_report_contains_all_providers_in_table():
    metrics = [_m("minimax"), _m("anthropic (mock)"), _m("openai (mock)")]
    md = render_report("test-run", metrics, ["minimax", "anthropic (mock)", "openai (mock)"])
    assert "minimax" in md
    assert "anthropic (mock)" in md
    assert "openai (mock)" in md
    assert "| provider |" in md


def test_render_report_includes_recommended_priority_diff():
    metrics = [_m("a", cost=0.001), _m("b", cost=0.005)]
    md = render_report("test-run", metrics, ["a", "b"])
    assert "default_priority" in md
    assert '"a"' in md
    assert '"b"' in md


def test_render_report_threshold_callout():
    metrics = [_m("a", cost=0.001)]
    md = render_report("test-run", metrics, ["a"])
    assert "0.90" in md or "0.9" in md
