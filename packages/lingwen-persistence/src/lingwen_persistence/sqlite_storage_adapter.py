"""Back-compat re-export shim for SqliteStorageAdapter.

v16.5 #N.0 relocated the canonical SqliteStorageAdapter from infra.persistence
to packages/lingwen-storage. This shim preserves the import path for existing
consumers — they can keep doing ``from infra.persistence.sqlite_storage_adapter
import SqliteStorageAdapter`` while new code should prefer:

    from lingwen_storage.sqlite_storage_adapter import SqliteStorageAdapter

The shim does NOT import sqlite3 directly (the architectural invariant is
preserved by delegating to lingwen_storage).
"""

from lingwen_storage.sqlite_storage_adapter import (  # noqa: F401
    FileSystemMarkdownRoundtrip,
    SqliteConnection,
    SqliteStorageAdapter,
)

__all__ = ["FileSystemMarkdownRoundtrip", "SqliteConnection", "SqliteStorageAdapter"]
