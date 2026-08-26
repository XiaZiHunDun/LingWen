"""Render benchmark metrics into a markdown report."""
from __future__ import annotations

from infra.llm_benchmarks.metrics import ProviderMetrics, quality_composite


def _format_row(m: ProviderMetrics) -> str:
    composite = quality_composite(m)
    return (
        f"| {m.provider} "
        f"| {m.parse_rate:.2f} "
        f"| {m.schema_compliance:.2f} "
        f"| {m.canon_level_compliance:.2f} "
        f"| {composite:.2f} "
        f"| ${m.cost_per_call_usd:.4f} "
        f"| {m.latency_p50_s:.2f} "
        f"| {m.latency_p95_s:.2f} "
        f"| {m.consistency_score:.2f} |"
    )


def _format_confidence_row(m: ProviderMetrics) -> str:
    d = m.confidence_distribution
    return (
        f"| {m.provider} "
        f"| {d.get('high', 0)} "
        f"| {d.get('medium', 0)} "
        f"| {d.get('low', 0)} |"
    )


def render_report(
    run_id: str,
    provider_metrics: list[ProviderMetrics],
    recommended_priority: list[str],
    *,
    threshold: float = 0.9,
) -> str:
    """Render markdown report content. Caller writes to disk."""
    lines: list[str] = []
    lines.append(f"# LLM Provider Benchmark — {run_id}")
    lines.append("")
    lines.append("## Run")
    lines.append(f"- run_id: `{run_id}`")
    lines.append(f"- providers: {', '.join(m.provider for m in provider_metrics)}")
    lines.append(f"- calls/provider: {provider_metrics[0].n_calls if provider_metrics else 0}")
    lines.append("- fixture: huiyu-dangan/golden-set/chapters/{ch001, ch003, ch010} + 林栀")
    lines.append("")
    lines.append("## Per-provider metrics")
    lines.append("")
    lines.append(
        "| provider | parse_rate | schema_compliance | canon_level | composite | cost/call | p50 (s) | p95 (s) | consistency |"
    )
    lines.append(
        "|----------|-----------|------------------|-------------|-----------|-----------|---------|---------|-------------|"
    )
    for m in provider_metrics:
        lines.append(_format_row(m))
    lines.append("")
    lines.append("## Confidence distribution")
    lines.append("")
    lines.append("| provider | high | medium | low |")
    lines.append("|----------|------|--------|-----|")
    for m in provider_metrics:
        lines.append(_format_confidence_row(m))
    lines.append("")
    lines.append("## Threshold check")
    lines.append("")
    lines.append(f"Quality threshold = {threshold:.2f}.")
    above = [m for m in provider_metrics if quality_composite(m) >= threshold]
    if above:
        above_sorted = sorted(above, key=lambda m: m.cost_per_call_usd)
        lines.append("Providers above threshold (cost-ordered):")
        for i, m in enumerate(above_sorted, 1):
            composite = quality_composite(m)
            lines.append(
                f"{i}. {m.provider} (composite={composite:.2f}, cost=${m.cost_per_call_usd:.4f})"
            )
    lines.append("")
    lines.append("## Recommended priority")
    lines.append("")
    lines.append("```python")
    quoted = ", ".join(f'"{p}"' for p in recommended_priority)
    lines.append(f"default_priority = [{quoted}]")
    lines.append("```")
    lines.append("")
    lines.append("Reasoning: above-threshold providers ordered by cost asc; below-threshold appended.")
    lines.append("")
    return "\n".join(lines)
