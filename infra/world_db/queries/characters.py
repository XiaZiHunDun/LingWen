"""Character CRUD with optimistic concurrency."""
import json
import sqlite3
from datetime import datetime, timezone


class CharacterRevisionConflict(Exception):
    """Raised when expected_revision does not match current row."""


CHARACTER_REVISION_CONFLICT = CharacterRevisionConflict


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    for k in ("attributes", "aliases"):
        if d.get(k):
            d[k] = json.loads(d[k])
    return d


def create_character(conn: sqlite3.Connection, data: dict) -> int:
    now = _now()
    attrs = json.dumps(data.get("attributes") or {}, ensure_ascii=False)
    aliases = json.dumps(data.get("aliases") or [], ensure_ascii=False)
    cur = conn.execute(
        """INSERT INTO character
           (slug, name, canon_level, status, first_chapter, last_seen_chapter,
            attributes, aliases, notes, created_at, updated_at, revision)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
        (
            data["slug"], data["name"], data["canon_level"],
            data.get("status"), data.get("first_chapter"),
            data.get("last_seen_chapter"), attrs, aliases,
            data.get("notes"), now, now,
        ),
    )
    conn.commit()
    return cur.lastrowid


def get_character(conn: sqlite3.Connection, char_id: int) -> dict | None:
    row = conn.execute(
        "SELECT * FROM character WHERE id = ?", (char_id,)
    ).fetchone()
    return _row_to_dict(row) if row else None


def get_character_by_slug(conn: sqlite3.Connection, slug: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM character WHERE slug = ?", (slug,)
    ).fetchone()
    return _row_to_dict(row) if row else None


def list_characters(conn: sqlite3.Connection, canon_level: str | None = None) -> list[dict]:
    if canon_level:
        rows = conn.execute(
            "SELECT * FROM character WHERE canon_level = ? ORDER BY name",
            (canon_level,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM character ORDER BY name").fetchall()
    return [_row_to_dict(r) for r in rows]


def update_character(
    conn: sqlite3.Connection, char_id: int, patch: dict, expected_revision: int
) -> None:
    cur = conn.execute(
        """UPDATE character SET
           name = COALESCE(?, name),
           canon_level = COALESCE(?, canon_level),
           status = COALESCE(?, status),
           first_chapter = COALESCE(?, first_chapter),
           last_seen_chapter = COALESCE(?, last_seen_chapter),
           attributes = COALESCE(?, attributes),
           aliases = COALESCE(?, aliases),
           notes = COALESCE(?, notes),
           updated_at = ?,
           revision = revision + 1
           WHERE id = ? AND revision = ?""",
        (
            patch.get("name"), patch.get("canon_level"),
            patch.get("status"), patch.get("first_chapter"),
            patch.get("last_seen_chapter"),
            json.dumps(patch["attributes"], ensure_ascii=False)
                if "attributes" in patch else None,
            json.dumps(patch["aliases"], ensure_ascii=False)
                if "aliases" in patch else None,
            patch.get("notes"),
            _now(), char_id, expected_revision,
        ),
    )
    if cur.rowcount == 0:
        raise CharacterRevisionConflict(
            f"character {char_id} revision != {expected_revision}"
        )
    conn.commit()
