"""Relationship CRUD."""
import sqlite3

from infra.world_db.queries._helpers import now_iso


def create_relationship(conn: sqlite3.Connection, data: dict) -> int:
    now = now_iso()
    cur = conn.execute(
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
    return cur.lastrowid


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
