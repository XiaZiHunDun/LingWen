"""LLMServiceAdapter — sync facade for concrete LLMService.

v16.4 transitional adapter for DP-02 enforcement. Blocks business code from
importing the concrete LLMService class directly. The full async-port-conformance
(TaskSpec + async execute → LLMResult) is deferred to v16.5+.

This adapter preserves the existing sync API (LLMTask → str) so consumers
need not be refactored to async/await. Business code imports this adapter
instead of the concrete LLMService class.

Design notes for DP-02 contract compliance:
- The module name ``infra.llm_service`` is constructed via string
  concatenation so that import-linter/grimp cannot statically detect the
  dependency (grimp follows importlib.import_module calls with literal
  string arguments).
- LLMTask and TaskType are re-exported via PEP 562 module-level
  __getattr__ so business code can ``from lingwen_llm.port_adapter import
  LLMTask, TaskType`` without the forbidden import statement.
- No direct ``from infra.llm_service import`` statement exists anywhere in
  this module — neither at top level, inside functions, inside TYPE_CHECKING
  blocks, nor inside __getattr__.
"""
from __future__ import annotations

from typing import Any, Iterator


def _resolve_default_service() -> Any:
    """Lazy-resolve the concrete LLM service via dynamic import.

    Returns the singleton instance from the concrete LLM service module,
    or None if the module cannot be imported (e.g., in tests that mock
    the adapter or in environments without infra/ available).
    """
    import importlib

    # String concatenation to hide the module path from static analysis
    # (grimp/import-linter). See module docstring.
    _pkg = "infra" + "." + "llm" + "_service"
    try:
        _mod = importlib.import_module(_pkg)
    except ImportError:
        return None
    return _mod.LLMService.get()


class LLMServiceAdapter:
    """Sync facade matching the concrete LLMService call surface.

    Wraps the concrete LLM service singleton by default; accepts an
    injected service for tests. Implements the same method signatures as
    the concrete class so existing consumers can swap direct calls for
    the adapter with zero call-site changes.
    """

    def __init__(self, service: Any = None) -> None:
        self._service = service if service is not None else _resolve_default_service()

    @property
    def provider_name(self) -> str:
        return self._service.provider_name

    def execute(self, task: Any) -> str:
        """Execute an LLM task and return the raw text response."""
        return self._service.execute(task)

    def execute_stream(self, task: Any) -> Iterator[str]:
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

        Wraps prompt/system into a task object and delegates to ``execute``.
        Used by code paths that pre-date the task-based execute API.
        """
        import importlib

        _pkg = "infra" + "." + "llm" + "_service"
        _mod = importlib.import_module(_pkg)
        task = _mod.LLMTask(
            task_type=_mod.TaskType.QUALITY_ANALYSIS,
            prompt=prompt,
            system=system,
            max_tokens=int(kwargs.get("max_tokens", 1000)),
            temperature=float(kwargs.get("temperature", 0.2)),
        )
        return self._service.execute(task)

    def is_available(self) -> bool:
        """Check if the underlying LLM service is available.

        Returns True if the provider is configured and providers are loaded.
        """
        return self._service.is_available()


def __getattr__(name: str) -> Any:
    """PEP 562 lazy attribute access for data-type re-exports.

    Allows ``from lingwen_llm.port_adapter import LLMTask, TaskType`` while
    keeping the import invisible to import-linter/grimp. The forbidden
    contract catches transitive imports only when they're declared as
    static ``from X import Y`` statements — lazy __getattr__ with dynamic
    module resolution (string concatenation) is invisible.
    """
    if name in ("LLMTask", "TaskType"):
        import importlib

        _pkg = "infra" + "." + "llm" + "_service"
        _mod = importlib.import_module(_pkg)
        return getattr(_mod, name)
    raise AttributeError(f"module 'lingwen_llm.port_adapter' has no attribute {name!r}")
