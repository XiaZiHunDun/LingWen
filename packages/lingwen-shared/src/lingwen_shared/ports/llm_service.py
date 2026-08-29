"""LLMServicePort — Hexagonal port for LLM service access.

v16.1 status: declaration only (Protocol definition). Business code may continue
to import the concrete ``LLMService`` class.
v16.4 status: import-linter enforcement — business code MUST import this port,
              not the concrete LLMService. is_available() added in v16.4 for
              health-check use cases.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, AsyncIterator, Mapping, Protocol


@dataclass(frozen=True)
class TaskSpec:
    """A request to the LLM service.

    Mirrors design doc §4.4 LLMServicePort input.
    """

    prompt: str
    system: str
    max_tokens: int = 4000
    temperature: float = 0.7
    metadata: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class LLMResult:
    """A response from the LLM service."""

    text: str
    provider: str
    cost_usd: Decimal
    latency_ms: int
    raw_response: bytes  # for debugging, NOT for business logic


class LLMServicePort(Protocol):
    """Hexagonal port for LLM access. Concrete adapters live in packages/lingwen-llm/."""

    async def execute(self, task: TaskSpec) -> LLMResult: ...
    async def execute_stream(self, task: TaskSpec) -> AsyncIterator[str]: ...
    def parse_json_response(self, response: LLMResult, schema: type) -> Any: ...
    def is_available(self) -> bool: ...
