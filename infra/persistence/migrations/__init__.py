"""SQLite migration runner.

v16.5 #N.4: drop direct ``import sqlite3``; the connection parameter is
typed as ``ConnectionPort`` (from ``lingwen_shared.ports.storage``).
``conn.cursor()`` works because ``SqliteConnection.__getattr__`` delegates
to the underlying ``sqlite3.Connection``.
"""

from pathlib import Path
from typing import List, Tuple

from lingwen_shared.ports.storage import ConnectionPort

MIGRATIONS_DIR = Path(__file__).parent


def get_migration_files() -> List[Tuple[int, str, Path]]:
    migrations = []
    for file in MIGRATIONS_DIR.glob("*.sql"):
        try:
            name = file.stem
            if "_" in name:
                version = int(name.split("_")[0])
                description = "_".join(name.split("_")[1:])
                migrations.append((version, description, file))
        except (ValueError, IndexError):
            continue
    migrations.sort(key=lambda x: x[0])
    return migrations


def init_migrations(conn: ConnectionPort) -> None:
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
            version INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def get_applied_migrations(conn: ConnectionPort) -> List[int]:
    cursor = conn.cursor()
    cursor.execute("SELECT version FROM migrations ORDER BY version ASC")
    return [row[0] for row in cursor.fetchall()]


def apply_migration(conn: ConnectionPort, version: int, description: str, sql_file: Path) -> None:
    cursor = conn.cursor()
    with open(sql_file, "r") as f:
        sql = f.read()
    try:
        cursor.executescript(sql)
        cursor.execute("INSERT INTO migrations (version, description) VALUES (?, ?)", (version, description))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e


def run_migrations(conn: ConnectionPort) -> List[Tuple[int, str]]:
    init_migrations(conn)
    applied = get_applied_migrations(conn)
    all_migrations = get_migration_files()
    applied_list = []

    for version, description, sql_file in all_migrations:
        if version not in applied:
            apply_migration(conn, version, description, sql_file)
            applied_list.append((version, description))

    return applied_list
