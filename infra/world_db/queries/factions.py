"""Faction CRUD."""
import json
import sqlite3

from infra.world_db.queries._helpers import now_iso, row_to_dict


def create_faction(conn: sqlite3.Connection, data: dict) -> int:
    now = now_iso()
    cur = conn.execute(
        """INSERT INTO faction
           (slug, name, description, attributes, created_at, updated_at, revision)
           VALUES (?, ?, ?, ?, ?, ?, 1)""",
        (
            data["slug"], data["name"], data.get("description"),
            json.dumps(data.get("attributes") or {}, ensure_ascii=False),
            now, now,
        ),
    )
    conn.commit()
    return cur.lastrowid


def list_factions(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM faction ORDER BY name").fetchall()
    return [row_to_dict(r, ("attributes",)) for r in rows if r is not None]


def get_faction(conn: sqlite3.Connection, fid: int) -> dict | None:
    return row_to_dict(
        conn.execute("SELECT * FROM faction WHERE id = ?", (fid,)).fetchone(),
        ("attributes",),
    )


def get_faction_by_slug(conn: sqlite3.Connection, slug: str) -> dict | None:
    return row_to_dict(
        conn.execute("SELECT * FROM faction WHERE slug = ?", (slug,)).fetchone(),
        ("attributes",),
    )
