"""SqliteStorageAdapter — concrete ``StoragePort`` implementation (SQLite backend).

v16.5 #N.0 relocated: this file moved from
``infra/persistence/sqlite_storage_adapter.py`` to
``packages/lingwen-storage/src/lingwen_storage/sqlite_storage_adapter.py``.

Why: enable shared use across all lingwen-* packages (lingwen_core,
lingwen_pipeline, lingwen_cli) without circular import. Previously the
canonical SQLite backend lived in infra/, but lingwen_core/pipeline depend
on infra.persistence (reverse of the desired direction) — moving to a leaf
package (lingwen_storage has no lingwen_* dependencies) breaks the cycle.

The OLD location at ``infra/persistence/sqlite_storage_adapter.py`` is now a
back-compat re-export shim that imports from this module. All consumers can
transition to importing from ``lingwen_storage.sqlite_storage_adapter``
directly at their convenience (v16.5 #N.2-N.6).

Architectural invariant: this module is the canonical SQLite backend
implementation. It is the ONLY file in the lingwen-* package family allowed
to ``import sqlite3`` directly. The
``infra/persistence/sqlite_storage_adapter.py`` shim re-exports symbols from
here — it does not import sqlite3 itself.

Regression-tested by:
- ``packages/lingwen-storage/tests/test_sqlite_storage_adapter.py`` (moved
  in v16.5 #N.0).
- ``tests/persistence/test_sqlite_storage_adapter.py`` if it still exists
  (back-compat shim path).
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator, TypeVar

from lingwen_shared.ports.storage import (
    ConnectionPort,
    MarkdownRoundtripPort,
    StoragePort,
)

T = TypeVar("T")

DEFAULT_TIMEOUT = 5.0


class SqliteConnection:
    """Wraps ``sqlite3.Connection`` to satisfy ``ConnectionPort``.

    The wrapper is intentionally thin: it delegates ``execute`` and
    ``commit`` to the underlying connection, and exposes all other
    ``sqlite3.Connection`` methods via ``__getattr__`` so callers that
    use ``cursor.fetchall()``, ``conn.row_factory``, ``conn.cursor()``,
    etc. continue to work unchanged.

    Why a wrapper instead of returning ``sqlite3.Connection`` directly:
    a future test or alternate backend can swap this for an in-memory
    fake without changing call sites.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def execute(self, sql: str, params: object = ()) -> object:
        """Execute a single SQL statement, returning a cursor-like object.

        Matches ``ConnectionPort.execute`` signature. ``params`` defaults
        to ``()`` (empty tuple) so callers can omit it for parameterless
        statements; concrete callers cast or rely on duck-typing for
        cursor methods (``fetchall``, ``fetchone``, ``lastrowid``, etc.).
        """
        return self._conn.execute(sql, params)

    def commit(self) -> None:
        """Commit the current transaction."""
        self._conn.commit()

    def __getattr__(self, name: str) -> object:
        """Delegate unknown attribute access to the underlying connection.

        Allows callers to use ``conn.row_factory``, ``conn.cursor()``,
        ``conn.executescript()``, etc. without changing call sites.
        """
        return getattr(self._conn, name)


class FileSystemMarkdownRoundtrip:
    """``MarkdownRoundtripPort`` implementation backed by the filesystem.

    Atomic writes are performed via ``tempfile.mkstemp`` + ``os.replace``
    so a partial write never corrupts an existing chapter file.
    """

    def read(self, path: Path) -> str:
        """Read UTF-8 markdown content from ``path``."""
        return Path(path).read_text(encoding="utf-8")

    def write(self, path: Path, body: str) -> None:
        """Write ``body`` to ``path`` atomically (via .tmp + rename).

        Creates parent directories if missing. On error during the
        write, the temporary file is removed and the exception
        re-raised — the target file is never partially overwritten.
        """
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(body)
            os.replace(tmp_path, target)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def list_chapters(self, project: str) -> list[str]:
        """List chapter files for ``project`` (golden-set chapters).

        Convention: ``projects/<project>/golden-set/chapters/ch*.md``.
        Returns absolute paths sorted by name. Empty list if the
        directory does not exist (project not yet initialised).
        """
        chapters_dir = Path("projects") / project / "golden-set" / "chapters"
        if not chapters_dir.exists():
            return []
        return sorted(str(p) for p in chapters_dir.glob("ch*.md"))


class SqliteStorageAdapter(StoragePort):
    """Concrete ``StoragePort`` backed by SQLite + filesystem markdown.

    Construct with the SQLite database path; the markdown round-trip
    implementation is initialised once per adapter. Per-call connection
    lifecycle is owned by ``with_connection`` (read-only use) and
    ``with_transaction`` (commit on success, rollback on error).
    """

    def __init__(
        self,
        db_path: str | Path,
        *,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._db_path = str(db_path)
        self._timeout = timeout
        self._markdown = FileSystemMarkdownRoundtrip()

    def _open(self) -> sqlite3.Connection:
        """Open a fresh SQLite connection with ``row_factory`` set."""
        conn = sqlite3.connect(self._db_path, timeout=self._timeout)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def _connection_cm(self) -> Iterator[SqliteConnection]:
        """Internal: open + close a connection (no commit)."""
        conn = self._open()
        try:
            yield SqliteConnection(conn)
        finally:
            conn.close()

    @contextmanager
    def _transaction_cm(self) -> Iterator[SqliteConnection]:
        """Internal: open + commit/rollback + close (transactional)."""
        conn = self._open()
        try:
            yield SqliteConnection(conn)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def with_connection(self, fn: Callable[[ConnectionPort], T]) -> T:
        """Open a connection, call ``fn``, close. No commit (read-only use).

        Suitable for SELECT, schema introspection, and other operations
        that should not implicitly commit pending transactions in other
        concurrent connections.
        """
        with self._connection_cm() as conn:
            return fn(conn)

    def with_transaction(self, fn: Callable[[ConnectionPort], T]) -> T:
        """Open a connection, call ``fn``, commit on success.

        Rolls back and re-raises if ``fn`` raises. The connection is
        always closed, whether or not ``fn`` succeeded.
        """
        with self._transaction_cm() as conn:
            return fn(conn)

    def markdown_roundtrip(self) -> MarkdownRoundtripPort:
        """Return the markdown round-trip implementation.

        A single instance is reused across calls (the roundtrip has
        no per-call state, so re-using is safe and avoids repeated
        allocations).
        """
        return self._markdown


__all__ = [
    "DEFAULT_TIMEOUT",
    "FileSystemMarkdownRoundtrip",
    "SqliteConnection",
    "SqliteStorageAdapter",
]


# v16.5 #N.1: Register this concrete adapter as the default factory for
# ``get_default_storage()``. Mirrors the v16.5 #1 pattern where
# ``infra.llm_service`` registers itself as default factory for LLMServiceAdapter.
#
# The factory returns a SqliteStorageAdapter with default settings. Apps that
# need a specific DB path should construct SqliteStorageAdapter(db_path=...)
# explicitly and register it via set_default_storage_factory() at startup.
from lingwen_shared.ports.storage import set_default_storage_factory


def _default_storage_factory() -> "SqliteStorageAdapter":
    """Default factory: SqliteStorageAdapter with in-memory DB.

    Production apps should register their own factory at startup with the
    appropriate db_path. This default is for tests and minimal bootstrap.
    """
    return SqliteStorageAdapter(":memory:")


set_default_storage_factory(_default_storage_factory)
