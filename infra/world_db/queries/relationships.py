"""Relationship CRUD."""
import sqlite3

from infra.world_db.queries._helpers import now_iso


def create_relationship(conn: sqlite3.Connection, data: dict) -> int:
    """Insert a relationship, idempotent on the UNIQUE constraint.

    Returns the canonical row id. When a relationship with the same
    (source_kind, source_id, target_kind, target_id, kind) already exists,
    the INSERT OR IGNORE is a no-op and we resolve the id with a SELECT on
    the same key — making the return value deterministic regardless of
    SQLite's lastrowid behavior on conflict (which is implementation-defined
    across Python/sqlite3 versions and may return 0, the pre-existing row's
    id, or None).
    """
    now = now_iso()
    conn.execute(
        """INSERT OR IGNORE INTO relationship
           (source_kind, source_id, target_kind, target_id, kind,
            strength, chapter, notes, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data["source_kind"], data["source_id"],
            data["target_kind"], data["target_id"], data["kind"],
            data.get("strength"), data.get("chapter"),
            data.get("notes"), now, now,
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id FROM relationship "
        "WHERE source_kind = ? AND source_id = ? "
        "AND target_kind = ? AND target_id = ? AND kind = ?",
        (data["source_kind"], data["source_id"],
         data["target_kind"], data["target_id"], data["kind"]),
    ).fetchone()
    if row is None:
        # Should be unreachable — INSERT OR IGNORE either inserts or finds
        # a conflicting row, both of which leave a row matching the key.
        raise RuntimeError(
            "create_relationship: row missing after INSERT OR IGNORE"
        )
    return row["id"]


def list_relationships(
    conn: sqlite3.Connection,
    source_kind: str | None = None,
    source_id: int | None = None,
    target_kind: str | None = None,
    target_id: int | None = None,
) -> list[dict]:
    sql = "SELECT * FROM relationship WHERE 1=1"
    args: list = []
    if source_kind:
        sql += " AND source_kind = ?"
        args.append(source_kind)
    if source_id is not None:
        sql += " AND source_id = ?"
        args.append(source_id)
    if target_kind:
        sql += " AND target_kind = ?"
        args.append(target_kind)
    if target_id is not None:
        sql += " AND target_id = ?"
        args.append(target_id)
    rows = conn.execute(sql, args).fetchall()
    return [dict(r) for r in rows]
