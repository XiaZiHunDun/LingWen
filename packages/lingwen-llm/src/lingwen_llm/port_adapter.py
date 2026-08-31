"""LLMServiceAdapter — async facade for concrete LLMService.

v16.5 #N.12: converted to async surface matching LLMServicePort Protocol.
Sync concrete ``LLMService`` is wrapped via ``asyncio.to_thread`` so HTTP I/O
runs in the default threadpool without blocking the event loop.

Architecture invariant: this module MUST NOT contain any static
``from infra.llm_service import ...`` statement, any string-concat
dynamic import of ``infra.llm_service``, or any PEP 562 ``__getattr__``
that re-exports ``infra.llm_service`` symbols. Regression-tested by
``tooling/hygiene/check_no_grimp_evasion.py`` (v16.5 #1).
"""
from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Callable, Optional

from lingwen_shared.contracts.python.llm import LLMTask, TaskType

_DEFAULT_FACTORY: Optional[Callable[[], Any]] = None


def set_default_factory(factory: Optional[Callable[[], Any]]) -> None:
    """Register the default factory used when no service is injected."""
    global _DEFAULT_FACTORY
    _DEFAULT_FACTORY = factory


def get_default_factory() -> Optional[Callable[[], Any]]:
    """Return the currently registered default factory, or ``None``."""
    return _DEFAULT_FACTORY


class LLMServiceAdapter:
    """Async facade matching ``LLMServicePort`` Protocol.

    Wraps the concrete LLM service singleton by default; accepts an
    injected service for tests. Async methods route through
    ``asyncio.to_thread`` so sync concrete I/O doesn't block the event loop.
    """

    def __init__(self, service: Any = None) -> None:
        if service is None:
            if _DEFAULT_FACTORY is None:
                raise RuntimeError(
                    "LLMServiceAdapter default factory not registered. "
                    "Either pass `service=` explicitly or import "
                    "`infra.llm_service` (which registers the factory at "
                    "module load time) before constructing the adapter."
                )
            service = _DEFAULT_FACTORY()
        self._service = service

    @property
    def provider_name(self) -> str:
        return self._service.provider_name

    async def execute(self, task: LLMTask) -> str:
        """Execute an LLM task in a thread pool (so sync HTTP doesn't block event loop)."""
        return await asyncio.to_thread(self._service.execute, task)

    async def execute_stream(self, task: LLMTask) -> AsyncIterator[str]:
        """Stream an LLM task, yielding text chunks as an async generator."""
        for chunk in self._service.execute_stream(task):
            yield chunk

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        model: str = "default",
        **kwargs: Any,
    ) -> str:
        """Async convenience method (was sync in v16.5 #N.6)."""
        task = LLMTask(
            task_type=TaskType.QUALITY_ANALYSIS,
            prompt=prompt,
            system=system,
            max_tokens=int(kwargs.get("max_tokens", 2000)),
            temperature=float(kwargs.get("temperature", 0.3)),
        )
        return await self.execute(task)

    def parse_json_response(self, response: str) -> Any:
        """Parse a JSON response from the LLM (handles markdown code fences)."""
        return self._service.parse_json_response(response)

    def is_available(self) -> bool:
        """Check if the underlying LLM service is available."""
        return self._service.is_available()


__all__ = [
    "LLMServiceAdapter",
    "set_default_factory",
    "get_default_factory",
]
