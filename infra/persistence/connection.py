"""Back-compat thin wrappers around ``SqliteStorageAdapter``.

v16.5 #N.4: these helpers used to call ``sqlite3.connect`` directly. They
now delegate to ``lingwen_storage.sqlite_storage_adapter`` (the canonical
SQLite backend) so business code never imports ``sqlite3`` directly.

Public API (unchanged — must satisfy the existing test contract which
asserts ``isinstance(conn, sqlite3.Connection)`` and the context-manager
protocol on ``_connect``):

- ``DEFAULT_TIMEOUT``: same constant as before (5.0 s).
- ``get_connection(db_path, *, timeout=DEFAULT_TIMEOUT)``: open a raw
  ``sqlite3.Connection`` (caller owns the connection).
- ``connection_context(db_path, *, timeout=DEFAULT_TIMEOUT)``: read-only
  context manager (no implicit commit).
- ``_connect(db_path, *, timeout=DEFAULT_TIMEOUT)``: transactional
  context manager (commit on success, rollback on error).
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

DEFAULT_TIMEOUT = 5.0


def get_connection(
    db_path: str | object,
    *,
    timeout: float = DEFAULT_TIMEOUT,
):
    """Open a connection to the SQLite database at ``db_path``.

    The returned object is a real ``sqlite3.Connection`` (not a wrapper)
    with ``row_factory = sqlite3.Row`` pre-set by the adapter. The caller
    owns the connection and is responsible for closing it.
    """
    from lingwen_storage.sqlite_storage_adapter import SqliteStorageAdapter

    adapter = SqliteStorageAdapter(str(db_path), timeout=timeout)
    return adapter._open()


@contextmanager
def connection_context(
    db_path: str | object,
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> Iterator[object]:
    """Read-only context manager — open connection, no implicit commit.

    Suitable for SELECT, schema introspection, and other operations that
    should not implicitly commit pending transactions in other concurrent
    connections.
    """
    from lingwen_storage.sqlite_storage_adapter import SqliteStorageAdapter

    adapter = SqliteStorageAdapter(str(db_path), timeout=timeout)
    with adapter._connection_cm() as conn:
        yield conn


@contextmanager
def _connect(
    db_path: str | object,
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> Iterator[object]:
    """Transactional context manager — commit on success, rollback on error.

    Used by callers that already manually call ``conn.execute()`` and want
    the wrapper to handle the BEGIN/COMMIT/ROLLBACK boundary.
    """
    from lingwen_storage.sqlite_storage_adapter import SqliteStorageAdapter

    adapter = SqliteStorageAdapter(str(db_path), timeout=timeout)
    with adapter._transaction_cm() as conn:
        yield conn
