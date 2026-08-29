"""Faction CRUD."""
import json

from infra.world_db.queries._helpers import now_iso, row_to_dict
from lingwen_shared.ports.storage import ConnectionPort


def create_faction(conn: ConnectionPort, data: dict) -> int:
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


def list_factions(conn: ConnectionPort) -> list[dict]:
    rows = conn.execute("SELECT * FROM faction ORDER BY name").fetchall()
    return [row_to_dict(r, ("attributes",)) for r in rows if r is not None]


def get_faction(conn: ConnectionPort, fid: int) -> dict | None:
    return row_to_dict(
        conn.execute("SELECT * FROM faction WHERE id = ?", (fid,)).fetchone(),
        ("attributes",),
    )


def get_faction_by_slug(conn: ConnectionPort, slug: str) -> dict | None:
    return row_to_dict(
        conn.execute("SELECT * FROM faction WHERE slug = ?", (slug,)).fetchone(),
        ("attributes",),
    )
