"""Faction CRUD."""
import json
import sqlite3
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_to_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    d = dict(row)
    if d.get("attributes"):
        d["attributes"] = json.loads(d["attributes"])
    return d


def create_faction(conn: sqlite3.Connection, data: dict) -> int:
    now = _now()
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
    return [_row_to_dict(r) for r in rows]


def get_faction(conn: sqlite3.Connection, fid: int) -> dict | None:
    row = conn.execute("SELECT * FROM faction WHERE id = ?", (fid,)).fetchone()
    return _row_to_dict(row)


def get_faction_by_slug(conn: sqlite3.Connection, slug: str) -> dict | None:
    row = conn.execute("SELECT * FROM faction WHERE slug = ?", (slug,)).fetchone()
    return _row_to_dict(row)
