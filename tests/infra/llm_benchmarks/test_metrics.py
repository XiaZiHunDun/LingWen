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


def test_canon_level_compliance_counts_only_canon_ok_among_parse_ok():
    calls = [
        _make_call(parse_ok=True, canon_level_ok=True),
        _make_call(parse_ok=True, canon_level_ok=False),
        _make_call(parse_ok=False, canon_level_ok=True),  # not counted
    ]
    m = compute_metrics(calls, provider="minimax")
    assert m.canon_level_compliance == 0.5


def test_latency_p50_and_p95():
    calls = [_make_call(latency_s=float(i)) for i in range(1, 11)]  # 1.0..10.0
    m = compute_metrics(calls, provider="minimax")
    # 10 sorted latencies: 1,2,3,...,10 → p50=5.5 (mean of 5th & 6th), p95=9.55 (linear interp)
    assert 5.4 <= m.latency_p50_s <= 5.6
    assert 9.0 <= m.latency_p95_s <= 10.0


def test_cost_per_call_is_mean():
    calls = [
        _make_call(cost_usd=0.001),
        _make_call(cost_usd=0.003),
        _make_call(cost_usd=0.006),
    ]
    m = compute_metrics(calls, provider="minimax")
    assert abs(m.cost_per_call_usd - 0.003333) < 1e-6


def test_confidence_distribution_counts_by_proposal_payload():
    calls = [
        _make_call(
            parse_ok=True,
            parsed_proposals=[
                {"payload": {"confidence": "high"}, "kind": "character.update"},
                {"payload": {"confidence": "medium"}, "kind": "character.update"},
            ],
        ),
        _make_call(
            parse_ok=True,
            parsed_proposals=[
                {"payload": {"confidence": "high"}, "kind": "character.update"},
                {"payload": {"confidence": "low"}, "kind": "character.update"},
            ],
        ),
    ]
    m = compute_metrics(calls, provider="minimax")
    assert m.confidence_distribution == {"high": 2, "medium": 1, "low": 1}


from infra.llm_benchmarks.metrics import (
    consistency_score,
    quality_composite,
    recommend_priority,
)


def test_consistency_score_perfect_when_proposals_match_across_runs():
    proposals = [{"kind": "character.update", "target_id": 5}]
    calls = [
        _make_call(chapter_id=1, run_index=i, parsed_proposals=proposals)
        for i in range(1, 4)
    ]
    assert consistency_score(calls) == 1.0


def test_consistency_score_zero_when_all_proposals_differ():
    calls = [
        _make_call(chapter_id=1, run_index=1, parsed_proposals=[{"target_id": 1}]),
        _make_call(chapter_id=1, run_index=2, parsed_proposals=[{"target_id": 2}]),
        _make_call(chapter_id=1, run_index=3, parsed_proposals=[{"target_id": 3}]),
    ]
    # pairwise identical rate = 0/3 = 0.0
    assert consistency_score(calls) == 0.0


def test_consistency_score_handles_missing_runs():
    calls = [_make_call(chapter_id=1, run_index=1)]
    # only 1 run → no variance to measure → 1.0
    assert consistency_score(calls) == 1.0


def test_quality_composite_is_simple_average():
    m = ProviderMetrics(
        provider="minimax",
        n_calls=10,
        n_failed=0,
        parse_rate=0.9,
        schema_compliance=0.8,
        canon_level_compliance=1.0,
    )
    assert abs(quality_composite(m) - 0.9) < 1e-9


def test_recommend_priority_orders_by_cost_above_threshold():
    metrics = [
        ProviderMetrics(provider="a", n_calls=10, n_failed=0, parse_rate=1.0,
                        schema_compliance=1.0, canon_level_compliance=1.0,
                        cost_per_call_usd=0.005),
        ProviderMetrics(provider="b", n_calls=10, n_failed=0, parse_rate=1.0,
                        schema_compliance=1.0, canon_level_compliance=1.0,
                        cost_per_call_usd=0.001),
        ProviderMetrics(provider="c", n_calls=10, n_failed=0, parse_rate=0.5,
                        schema_compliance=0.5, canon_level_compliance=0.5,
                        cost_per_call_usd=0.0001),  # composite=0.5, below 0.9
    ]
    priority = recommend_priority(metrics, threshold=0.9)
    # a and b pass (composite=1.0), c fails (composite=0.5)
    assert priority == ["b", "a", "c"]


def test_recommend_priority_handles_empty_list():
    assert recommend_priority([], threshold=0.9) == []
