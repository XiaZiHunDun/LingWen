"""LLM provider benchmark module (Phase 120).

Dev/CI tool for comparing extraction quality / cost / latency across
LLM providers. CLI and library entrypoints.

Public API:
- run_benchmark: orchestrate a single provider benchmark run
- get_provider_llm: factory for real/mock LLM service
- CallResult, ProviderMetrics: dataclasses for results aggregation
"""
from __future__ import annotations

# Imports populated as subsequent tasks land
__all__ = [
    "run_benchmark",
    "get_provider_llm",
    "CallResult",
    "ProviderMetrics",
]