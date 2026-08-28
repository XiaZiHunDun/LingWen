"""LLMServiceAdapter — sync facade for concrete infra.llm_service.LLMService.

v16.4 transitional adapter for DP-02 enforcement. Blocks business code from
importing the concrete LLMService class directly. The full async-port-conformance
(TaskSpec + async execute → LLMResult) is deferred to v16.5+.

This adapter preserves the existing sync API (LLMTask → str) so consumers
need not be refactored to async/await. Business code imports this adapter
instead of `infra.llm_service.LLMService`.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from infra.llm_service import LLMService, LLMTask


class LLMServiceAdapter:
    """Sync facade matching the concrete LLMService call surface.

    Wraps ``infra.llm_service.LLMService.get()`` singleton by default;
    accepts an injected service for tests.

    Implements the same method signatures as the concrete class so existing
    consumers can swap ``LLMService.get()`` for ``LLMServiceAdapter()``
    with zero call-site changes.
    """

    def __init__(self, service: "LLMService | None" = None) -> None:
        if service is None:
            from infra.llm_service import LLMService

            service = LLMService.get()
        self._service = service

    @property
    def provider_name(self) -> str:
        return self._service.provider_name

    def execute(self, task: "LLMTask") -> str:
        """Execute an LLM task and return the raw text response."""
        return self._service.execute(task)

    def execute_stream(self, task: "LLMTask") -> Iterator[str]:
        """Stream an LLM task, yielding text chunks."""
        return self._service.execute_stream(task)

    def parse_json_response(self, response: str) -> Any:
        """Parse a JSON response from the LLM (handles markdown code fences)."""
        return self._service.parse_json_response(response)

    def is_available(self) -> bool:
        """Check if the underlying LLM service is available.

        Returns True if the provider is configured and providers are loaded.
        """
        provider = getattr(self._service, "_provider", None)
        return provider is not None
