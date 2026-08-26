"""LLM provider benchmark module (Phase 120).

Dev/CI tool for comparing extraction quality / cost / latency across
LLM providers. CLI and library entrypoints.
"""
from __future__ import annotations

from infra.llm_benchmarks.metrics import (
    CallResult,
    ProviderMetrics,
    compute_metrics,
    consistency_score,
    quality_composite,
    recommend_priority,
)
from infra.llm_benchmarks.providers import (
    MockLLMService,
    anthropic_mock_canned,
    get_provider_llm,
    minimax_mock_canned,
    openai_mock_canned,
)
from infra.llm_benchmarks.run import run_benchmark

__all__ = [
    "run_benchmark",
    "get_provider_llm",
    "MockLLMService",
    "CallResult",
    "ProviderMetrics",
    "compute_metrics",
    "consistency_score",
    "quality_composite",
    "recommend_priority",
    "anthropic_mock_canned",
    "openai_mock_canned",
    "minimax_mock_canned",
]
