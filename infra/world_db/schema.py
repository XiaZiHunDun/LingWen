"""SQLite schema for world DB.

Tables: character, faction, relationship, lore_entry, timeline_event, proposal.
All main tables carry `revision INTEGER` for optimistic concurrency.
"""
import sqlite3
from pathlib import Path

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


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Open a connection to the world DB at the given path."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Create all tables if not exist. Idempotent."""
    conn.executescript(DDL)
    conn.execute(
        "INSERT OR IGNORE INTO schema_version(version) VALUES (?)",
        (SCHEMA_VERSION,),
    )
    conn.commit()
