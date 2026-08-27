"""StoragePort — Hexagonal port for persistence (SQLite + markdown round-trip).

v16.1 status: declaration only (Protocol definition).
v16.5 status: import-linter enforcement — business code MUST NOT import sqlite3
or hardcode paths.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Protocol, TypeVar

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
