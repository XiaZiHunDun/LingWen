"""SQLite schema for world DB.

Tables: character, faction, relationship, lore_entry, timeline_event, proposal.
All main tables carry `revision INTEGER` for optimistic concurrency.

v16.5 #N.4: use lingwen_shared.ports.storage.ConnectionPort for
parameter typing (no direct sqlite3 import). The SqliteStorageAdapter
already sets ``row_factory = sqlite3.Row`` and ``PRAGMA foreign_keys = ON``;
callers do not need to set them again.
"""

from pathlib import Path

from lingwen_shared.ports.storage import ConnectionPort

SCHEMA_VERSION = 1

DDL = """
CREATE TABLE schema_version (
  version INTEGER PRIMARY KEY
);

CREATE TABLE character (
  id INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  canon_level TEXT NOT NULL,
  status TEXT,
  first_chapter INTEGER,
  last_seen_chapter INTEGER,
  attributes TEXT,   -- JSON
  aliases TEXT,      -- JSON array
  notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE faction (
  id INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  attributes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE relationship (
  id INTEGER PRIMARY KEY,
  source_kind TEXT NOT NULL,
  source_id INTEGER NOT NULL,
  target_kind TEXT NOT NULL,
  target_id INTEGER NOT NULL,
  kind TEXT NOT NULL,
  strength REAL,
  chapter INTEGER,
  notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(source_kind, source_id, target_kind, target_id, kind)
);

CREATE TABLE lore_entry (
  id INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  category TEXT NOT NULL,
  summary TEXT NOT NULL,
  body TEXT NOT NULL,
  tags TEXT,         -- JSON array
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE timeline_event (
  id INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  story_year INTEGER,
  story_label TEXT,
  chapter INTEGER,
  description TEXT,
  category TEXT,
  related_characters TEXT,  -- JSON array of ids
  related_factions TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE proposal (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL,
  target_kind TEXT,
  target_id INTEGER,
  payload TEXT NOT NULL,      -- JSON
  source TEXT NOT NULL,       -- 'human' | 'agent'
  source_context TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  reviewer TEXT,
  reviewed_at TEXT,
  created_at TEXT NOT NULL
);
"""


def get_connection(db_path: Path) -> ConnectionPort:
    """Open a connection to the world DB at the given path.

    v16.5 #N.4: delegates to ``SqliteStorageAdapter`` so callers get a
    ``SqliteConnection`` wrapper that satisfies ``ConnectionPort``.
    The adapter pre-configures ``row_factory = sqlite3.Row`` and
    ``PRAGMA foreign_keys = ON``; no manual setup needed here.

    Caller owns the returned connection (close via ``conn.close()`` or
    pass to ``SqliteStorageAdapter._connection_cm()`` for auto-cleanup).
    """
    # Lazy import: keep the schema module import-time side-effect free.
    from lingwen_storage.sqlite_storage_adapter import (
        SqliteConnection,
        SqliteStorageAdapter,
    )

    adapter = SqliteStorageAdapter(str(db_path))
    # Borrow the adapter's _open() to get a freshly configured connection
    # (row_factory + PRAGMA foreign_keys applied), wrapped in SqliteConnection
    # so callers can use it as ConnectionPort.
    return SqliteConnection(adapter._open())


def init_schema(conn: ConnectionPort) -> None:
    """Create all tables if not exist. Idempotent."""
    conn.executescript(DDL)
    conn.execute(
        "INSERT OR IGNORE INTO schema_version(version) VALUES (?)",
        (SCHEMA_VERSION,),
    )
    conn.commit()
