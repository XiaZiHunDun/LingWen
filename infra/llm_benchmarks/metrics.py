"""Pure metrics computation for LLM provider benchmark results.

Aggregates CallResult list per provider into ProviderMetrics summary.
All functions are pure (no I/O), testable without fixtures.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CallResult:
    """One LLM call outcome. Persisted as JSON in results/<run-id>/."""

    provider: str
    chapter_id: int
    run_index: int
    timestamp: str  # ISO-8601 UTC
    raw_response: str
    parsed_proposals: list[dict]
    parse_ok: bool
    schema_ok: bool
    canon_level_ok: bool
    latency_s: float
    output_tokens: int
    cost_usd: float
    failed: bool
    error: str | None = None


@dataclass(frozen=True)
class ProviderMetrics:
    """Aggregated metrics for one provider's N calls."""

    provider: str
    n_calls: int
    n_failed: int
    parse_rate: float  # parse_ok / n_calls
    schema_compliance: float  # schema_ok among parse_ok
    canon_level_compliance: float  # canon_level_ok among parse_ok
    confidence_distribution: dict[str, int] = field(default_factory=dict)
    latency_p50_s: float = 0.0
    latency_p95_s: float = 0.0
    cost_per_call_usd: float = 0.0
    consistency_score: float = 1.0
    quality_composite: float = 0.0


def compute_metrics(calls: list[CallResult], provider: str) -> ProviderMetrics:
    """Aggregate N CallResults into a ProviderMetrics summary.

    parse_rate = parse_ok / n_calls
    schema_compliance = schema_ok / count(parse_ok)
    canon_level_compliance = canon_level_ok / count(parse_ok)
    """
    n_calls = len(calls)
    n_failed = sum(1 for c in calls if c.failed)
    n_parse_ok = sum(1 for c in calls if c.parse_ok)
    n_schema_ok = sum(1 for c in calls if c.parse_ok and c.schema_ok)
    n_canon_ok = sum(1 for c in calls if c.parse_ok and c.canon_level_ok)

    parse_rate = n_parse_ok / n_calls if n_calls else 0.0
    schema_compliance = n_schema_ok / n_parse_ok if n_parse_ok else 0.0
    canon_level_compliance = n_canon_ok / n_parse_ok if n_parse_ok else 0.0

    return ProviderMetrics(
        provider=provider,
        n_calls=n_calls,
        n_failed=n_failed,
        parse_rate=parse_rate,
        schema_compliance=schema_compliance,
        canon_level_compliance=canon_level_compliance,
    )