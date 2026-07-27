import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DEFAULT_TIMEOUT = 5.0


def get_connection(db_path: str | Path, *, timeout: float = DEFAULT_TIMEOUT) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=timeout)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def connection_context(db_path: str | Path, *, timeout: float = DEFAULT_TIMEOUT) -> Iterator[sqlite3.Connection]:
    conn = get_connection(db_path, timeout=timeout)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def _connect(db_path: str | Path, *, timeout: float = DEFAULT_TIMEOUT) -> Iterator[sqlite3.Connection]:
    conn = get_connection(db_path, timeout=timeout)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
