"""LLMServiceAdapter — sync facade for concrete LLMService.

v16.5: removed all string-concat + PEP 562 workarounds (v16.4 hack).
Data types (``LLMTask``, ``TaskType``) now imported directly from
``lingwen_shared.contracts.python.llm``. The default service is resolved
via a factory registered at startup by ``infra.llm_service`` — this
ensures the import graph never crosses from ``lingwen_llm`` into
``infra.llm_service`` (which would re-trigger the DP-02 forbidden
contract via grimp transitive analysis).

Architecture invariant: this module MUST NOT contain any static
``from infra.llm_service import ...`` statement, any string-concat
dynamic import of ``infra.llm_service``, or any PEP 562 ``__getattr__``
that re-exports ``infra.llm_service`` symbols. Regression-tested by
``tooling/hygiene/check_no_grimp_evasion.py`` (T10).
"""
from __future__ import annotations

from typing import Any, Callable, Iterator, Optional

from lingwen_shared.contracts.python.llm import LLMTask, TaskType

_DEFAULT_FACTORY: Optional[Callable[[], Any]] = None


def set_default_factory(factory: Optional[Callable[[], Any]]) -> None:
    """Register the default factory used when no service is injected.

    Called once at module load time by ``infra.llm_service`` to wire the
    concrete ``LLMService`` singleton into the adapter's default behavior.
    Passing ``None`` clears the registration (useful in tests).

    The factory MUST be a zero-argument callable returning the service
    instance (or any object matching the surface used by ``LLMServiceAdapter``).
    """
    global _DEFAULT_FACTORY
    _DEFAULT_FACTORY = factory


def get_default_factory() -> Optional[Callable[[], Any]]:
    """Return the currently registered default factory, or ``None``.

    Exposed for introspection (tests, debugging). Not used by the adapter
    itself — it reads the module-level variable directly.
    """
    return _DEFAULT_FACTORY


class LLMServiceAdapter:
    """Sync facade matching the concrete ``LLMService`` call surface.

    Wraps the concrete LLM service singleton by default; accepts an
    injected service for tests. Implements the same method signatures as
    the concrete class so existing consumers can swap direct calls for
    the adapter with zero call-site changes.

    Constructing without arguments requires the default factory to be
    registered (importing ``infra.llm_service`` does this). To use the
    adapter in an isolated test, either inject ``service=fake`` explicitly
    or call ``set_default_factory(lambda: fake)`` before constructing.
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

    def execute(self, task: LLMTask) -> str:
        """Execute an LLM task and return the raw text response."""
        return self._service.execute(task)

    def execute_stream(self, task: LLMTask) -> Iterator[str]:
        """Stream an LLM task, yielding text chunks."""
        return self._service.execute_stream(task)

    def parse_json_response(self, response: str) -> Any:
        """Parse a JSON response from the LLM (handles markdown code fences)."""
        return self._service.parse_json_response(response)

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        model: str = "default",
        **kwargs: Any,
    ) -> str:
        """Convenience method mirroring the concrete ``generate`` API.

        Wraps ``prompt``/``system`` into an ``LLMTask`` and delegates to
        ``execute``. Used by code paths that pre-date the task-based API.
        """
        task = LLMTask(
            task_type=TaskType.QUALITY_ANALYSIS,
            prompt=prompt,
            system=system,
            max_tokens=int(kwargs.get("max_tokens", 2000)),
            temperature=float(kwargs.get("temperature", 0.3)),
        )
        return self._service.execute(task)

    def is_available(self) -> bool:
        """Check if the underlying LLM service is available.

        Returns True if the provider is configured and providers are loaded.
        """
        return self._service.is_available()


__all__ = [
    "LLMServiceAdapter",
    "set_default_factory",
    "get_default_factory",
]
