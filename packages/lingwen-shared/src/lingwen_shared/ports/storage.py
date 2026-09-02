"""StoragePort — Hexagonal port for persistence (SQLite + markdown round-trip).

v16.1 status: declaration only (Protocol definition).
v16.5 #N.1 status: factory pattern added (mirrors v16.5 #1 LLMServiceAdapter).
v16.5 status: import-linter enforcement — business code MUST NOT import sqlite3
or hardcode paths.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional, Protocol, TypeVar

T = TypeVar("T")


class ConnectionPort(Protocol):
    """Subset of sqlite3.Connection to enable testing without real SQLite."""

    def execute(self, sql: str, params: ...) -> object: ...
    def commit(self) -> None: ...


class MarkdownRoundtripPort(Protocol):
    """Markdown file read/write with atomicity guarantee."""

    def read(self, path: Path) -> str: ...
    def write(self, path: Path, body: str) -> None: ...  # atomic via .tmp + rename
    def list_chapters(self, project: str) -> list[str]: ...


class StoragePort(Protocol):
    """Abstract over SQLite + markdown round-trip + migrations."""

    def with_connection(self, fn: Callable[[ConnectionPort], T]) -> T: ...
    def with_transaction(self, fn: Callable[[ConnectionPort], T]) -> T: ...
    def markdown_roundtrip(self) -> MarkdownRoundtripPort: ...


# v16.5 #N.1: Factory pattern (mirrors v16.5 #1 LLMServiceAdapter).
#
# Architecture:
# - lingwen_storage.sqlite_storage_adapter registers itself as default factory
#   at module load time (mirrors infra.llm_service pattern).
# - Apps call ``get_default_storage()`` (no args) to obtain a StoragePort instance.
# - The factory pattern keeps ``lingwen_shared`` free of sqlite3 imports
#   while letting apps use StoragePort without depending on the concrete adapter.


_DEFAULT_STORAGE_FACTORY: Optional[Callable[[], "StoragePort"]] = None


def set_default_storage_factory(
    factory: Optional[Callable[[], "StoragePort"]],
) -> None:
    """Register the default factory used when ``get_default_storage()`` is called.

    Called once at module load time by ``lingwen_storage.sqlite_storage_adapter``
    to wire the concrete SqliteStorageAdapter into the default behavior. Passing
    ``None`` clears the registration.

    The factory MUST be a zero-argument callable returning a StoragePort instance.
    """
    global _DEFAULT_STORAGE_FACTORY
    _DEFAULT_STORAGE_FACTORY = factory


def get_default_storage_factory() -> Optional[Callable[[], "StoragePort"]]:
    """Return the currently registered default factory, or ``None``.

    Exposed for introspection (tests, debugging).
    """
    return _DEFAULT_STORAGE_FACTORY


def get_default_storage() -> "StoragePort":
    """Construct a StoragePort using the registered default factory.

    Raises RuntimeError if no factory is registered. To use a StoragePort in
    an isolated test, either:
    - Call ``set_default_storage_factory(lambda: fake_storage)`` before calling
      this function
    - Or use ``storage.with_connection(...)`` directly on a constructed adapter

    Apps should use this convenience function (no args). The concrete
    ``lingwen_storage.sqlite_storage_adapter`` registers itself at import time,
    so as long as the canonical module is imported somewhere during app
    startup (e.g., via ``infra.persistence.sqlite_storage_adapter`` shim which
    ``infra.persistence.bootstrap`` imports), this function works.
    """
    if _DEFAULT_STORAGE_FACTORY is None:
        raise RuntimeError(
            "StoragePort default factory not registered. "
            "Either pass an adapter explicitly or import "
            "`lingwen_storage.sqlite_storage_adapter` (which registers the "
            "factory at module load time) before calling `get_default_storage()`."
        )
    return _DEFAULT_STORAGE_FACTORY()


__all__ = [
    "ConnectionPort",
    "MarkdownRoundtripPort",
    "StoragePort",
    "set_default_storage_factory",
    "get_default_storage_factory",
    "get_default_storage",
]
