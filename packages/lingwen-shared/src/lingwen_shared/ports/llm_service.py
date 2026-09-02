"""LLMServicePort — Hexagonal port for LLM service access.

v16.1 status: declaration only (Protocol definition). Business code may continue
to import the concrete ``LLMService`` class.
v16.4 status: import-linter enforcement — business code MUST import this port,
              not the concrete LLMService. is_available() added in v16.4 for
              health-check use cases.
v16.5 #N.12 status: protocol signatures match LLMServiceAdapter async surface
              (async execute / async execute_stream / sync helpers). Data types
              aligned with ``lingwen_shared.contracts.python.llm.LLMTask``
              (canonical, established in v16.5 #1).
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Protocol

from lingwen_shared.contracts.python.llm import LLMTask


class LLMServicePort(Protocol):
    """Hexagonal port for LLM access. Concrete adapters live in packages/lingwen-llm/."""

    async def execute(self, task: LLMTask) -> str: ...
    async def execute_stream(self, task: LLMTask) -> AsyncIterator[str]: ...
    def parse_json_response(self, response: str) -> Any: ...
    def is_available(self) -> bool: ...
