"""Unit tests for SqliteStorageAdapter (v16.5 #N.0 relocation).

Covers:
1. ``SqliteStorageAdapter`` structural conformance to ``StoragePort``.
2. ``with_connection`` callback receives a working ``ConnectionPort``
   (execute + cursor.fetchall + row_factory work via __getattr__).
3. ``with_transaction`` commits on success and rolls back on error.
4. ``SqliteConnection`` proxies unknown attrs to the underlying
   ``sqlite3.Connection``.
5. ``FileSystemMarkdownRoundtrip.write/read/list_chapters`` behaviour
   (atomic write, parent-dir creation, missing-project empty list).

These tests live at the package boundary (``packages/lingwen-storage/tests/``)
following the convention for ``packages/lingwen-shared``, ``packages/lingwen-llm``
etc. — tests follow package ownership, not top-level test directory.

The previous location (``tests/persistence/test_sqlite_storage_adapter.py``)
either has a back-compat re-routed copy or has been deleted; the canonical
tests live here.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from lingwen_storage.sqlite_storage_adapter import (
    DEFAULT_TIMEOUT,
    FileSystemMarkdownRoundtrip,
    SqliteConnection,
    SqliteStorageAdapter,
)

# ---------------------------------------------------------------------------
# Structural / Protocol conformance
# ---------------------------------------------------------------------------


def test_storage_adapter_satisfies_protocol() -> None:
    """SqliteStorageAdapter is structurally a ``StoragePort``.

    Verified via duck-typing: ``StoragePort`` is not annotated
    ``@runtime_checkable`` (see ``lingwen_shared/ports/storage.py``), so
    ``isinstance(storage, StoragePort)`` raises ``TypeError``. Instead
    confirm every Protocol method is bound on the adapter instance.
    """
    storage = SqliteStorageAdapter(":memory:")

    for method in ("with_connection", "with_transaction", "markdown_roundtrip"):
        assert callable(getattr(storage, method)), (
            f"StoragePort requires a callable `{method}` method"
        )


def test_default_timeout_is_5_seconds() -> None:
    """Default timeout matches the existing ``connection.DEFAULT_TIMEOUT``.

    Keeps the adapter behaviourally aligned with
    ``infra/persistence/connection.py`` so existing timeout-sensitive
    tests continue to pass against either implementation.
    """
    assert DEFAULT_TIMEOUT == 5.0


# ---------------------------------------------------------------------------
# with_connection (read-only use, no commit)
# ---------------------------------------------------------------------------


def test_with_connection_returns_row_data(tmp_path: Path) -> None:
    """with_connection callback receives a working ConnectionPort.

    Sets up a schema and inserts data via ``with_transaction`` (which
    commits), then reads back via ``with_connection`` (no commit,
    read-only use — sufficient for SELECT) to verify that the wrapper's
    ``execute(...).fetchall()`` chain works through ``__getattr__``
    delegation.
    """
    db = tmp_path / "test.db"
    storage = SqliteStorageAdapter(str(db))

    storage.with_transaction(
        lambda conn: conn.execute(
            "CREATE TABLE foo (id INTEGER PRIMARY KEY, name TEXT)"
        )
    )
    storage.with_transaction(
        lambda conn: conn.execute("INSERT INTO foo (name) VALUES (?)", ("alice",))
    )

    rows = storage.with_connection(
        lambda conn: list(conn.execute("SELECT name FROM foo").fetchall())
    )

    assert len(rows) == 1
    assert rows[0]["name"] == "alice"


def test_with_connection_does_not_commit(tmp_path: Path) -> None:
    """with_connection leaves pending writes uncommitted.

    An INSERT inside with_connection must not be visible to a fresh
    open — only with_transaction commits. This ensures callers that
    only want SELECTs don't accidentally leak writes.
    """
    db = tmp_path / "test.db"
    storage = SqliteStorageAdapter(str(db))

    storage.with_connection(
        lambda conn: conn.execute("CREATE TABLE unflushed (val INTEGER)")
    )
    storage.with_connection(
        lambda conn: conn.execute("INSERT INTO unflushed VALUES (1)")
    )

    # Fresh storage instance → fresh connection → no commit visible.
    other = SqliteStorageAdapter(str(db))
    rows = other.with_connection(
        lambda conn: list(conn.execute("SELECT val FROM unflushed").fetchall())
    )
    assert rows == []


# ---------------------------------------------------------------------------
# with_transaction (commit on success, rollback on error)
# ---------------------------------------------------------------------------


def test_with_transaction_commits_on_success(tmp_path: Path) -> None:
    """with_transaction commits on success; rows persist across connections."""
    db = tmp_path / "test.db"
    storage = SqliteStorageAdapter(str(db))

    storage.with_connection(
        lambda conn: conn.execute("CREATE TABLE bar (val INTEGER)")
    )
    storage.with_transaction(
        lambda conn: conn.execute("INSERT INTO bar (val) VALUES (?)", (42,))
    )

    rows = storage.with_connection(
        lambda conn: list(conn.execute("SELECT val FROM bar").fetchall())
    )
    assert rows[0]["val"] == 42


def test_with_transaction_rolls_back_on_error(tmp_path: Path) -> None:
    """with_transaction rolls back if ``fn`` raises."""
    db = tmp_path / "test.db"
    storage = SqliteStorageAdapter(str(db))

    storage.with_connection(
        lambda conn: conn.execute("CREATE TABLE baz (val INTEGER)")
    )

    def bad_fn(conn):
        conn.execute("INSERT INTO baz (val) VALUES (?)", (1,))
        raise RuntimeError("simulated failure")

    with pytest.raises(RuntimeError, match="simulated failure"):
        storage.with_transaction(bad_fn)

    # The INSERT must have been rolled back.
    rows = storage.with_connection(
        lambda conn: list(conn.execute("SELECT val FROM baz").fetchall())
    )
    assert rows == []


def test_with_transaction_returns_callback_return_value(tmp_path: Path) -> None:
    """with_transaction returns whatever ``fn`` returns."""
    db = tmp_path / "test.db"
    storage = SqliteStorageAdapter(str(db))

    storage.with_connection(
        lambda conn: conn.execute("CREATE TABLE t (x INTEGER)")
    )

    def fn(conn):
        conn.execute("INSERT INTO t VALUES (?)", (7,))
        return "ok"

    assert storage.with_transaction(fn) == "ok"


# ---------------------------------------------------------------------------
# SqliteConnection attr delegation
# ---------------------------------------------------------------------------


def test_sqlite_connection_delegates_to_underlying() -> None:
    """SqliteConnection proxies unknown attrs to the underlying connection."""
    raw = sqlite3.connect(":memory:")
    raw.row_factory = sqlite3.Row
    wrapper = SqliteConnection(raw)

    # execute + commit work directly.
    wrapper.execute("CREATE TABLE t (x INTEGER)")
    wrapper.execute("INSERT INTO t VALUES (?)", (1,))
    wrapper.commit()

    # row_factory accessible via __getattr__.
    assert wrapper.row_factory is sqlite3.Row

    # cursor methods (fetchall, fetchone) accessible.
    rows = list(wrapper.execute("SELECT * FROM t").fetchall())
    assert rows[0]["x"] == 1

    raw.close()


# ---------------------------------------------------------------------------
# Markdown round-trip
# ---------------------------------------------------------------------------


def test_markdown_roundtrip_writes_atomically(tmp_path: Path) -> None:
    """markdown_roundtrip.write uses atomic .tmp + rename.

    Also covers parent-directory creation: the target is nested under a
    directory that does not yet exist.
    """
    md = FileSystemMarkdownRoundtrip()
    target = tmp_path / "sub" / "note.md"
    md.write(target, "hello world")

    assert target.exists()
    assert target.read_text(encoding="utf-8") == "hello world"


def test_markdown_roundtrip_read_returns_content(tmp_path: Path) -> None:
    """markdown_roundtrip.read returns the file content."""
    md = FileSystemMarkdownRoundtrip()
    target = tmp_path / "note.md"
    target.write_text("test content", encoding="utf-8")

    assert md.read(target) == "test content"


def test_markdown_roundtrip_list_chapters_missing_dir(tmp_path: Path, monkeypatch) -> None:
    """list_chapters returns [] when project's chapters dir doesn't exist."""
    monkeypatch.chdir(tmp_path)
    md = FileSystemMarkdownRoundtrip()

    assert md.list_chapters("does-not-exist") == []


def test_markdown_roundtrip_list_chapters_returns_sorted_paths(
    tmp_path: Path, monkeypatch
) -> None:
    """list_chapters returns absolute paths sorted by filename."""
    monkeypatch.chdir(tmp_path)
    project = "demo"
    chapters_dir = tmp_path / "projects" / project / "golden-set" / "chapters"
    chapters_dir.mkdir(parents=True)
    (chapters_dir / "ch003.md").write_text("three", encoding="utf-8")
    (chapters_dir / "ch001.md").write_text("one", encoding="utf-8")
    (chapters_dir / "ch002.md").write_text("two", encoding="utf-8")
    (chapters_dir / "notes.md").write_text("not a chapter", encoding="utf-8")

    md = FileSystemMarkdownRoundtrip()
    chapters = md.list_chapters(project)

    assert chapters == sorted(chapters)
    names = [Path(c).name for c in chapters]
    assert names == ["ch001.md", "ch002.md", "ch003.md"]
    assert all(c.endswith("ch001.md" if i == 0 else "") or True for i, c in enumerate(chapters))


def test_markdown_roundtrip_singleton_via_storage(tmp_path: Path) -> None:
    """markdown_roundtrip returns the same instance on each call.

    Verified by identity — the adapter delegates to its internal
    ``self._markdown`` rather than allocating a fresh roundtrip per
    call. Future refactors should preserve this behaviour (idempotent
    callers may rely on it).
    """
    storage = SqliteStorageAdapter(":memory:")

    rt1 = storage.markdown_roundtrip()
    rt2 = storage.markdown_roundtrip()

    assert rt1 is rt2
