"""Character CRUD with optimistic concurrency."""
import json

from infra.world_db.queries._helpers import (
    RevisionConflict,
    now_iso,
    row_to_dict,
)
from lingwen_shared.ports.storage import ConnectionPort


class CharacterRevisionConflict(RevisionConflict):
    """Raised when expected_revision does not match current character row."""


CHARACTER_REVISION_CONFLICT = CharacterRevisionConflict


def create_character(conn: ConnectionPort, data: dict) -> int:
    now = now_iso()
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


def get_character(conn: ConnectionPort, char_id: int) -> dict | None:
    return row_to_dict(
        conn.execute("SELECT * FROM character WHERE id = ?", (char_id,)).fetchone(),
        ("attributes", "aliases"),
    )


def get_character_by_slug(conn: ConnectionPort, slug: str) -> dict | None:
    return row_to_dict(
        conn.execute("SELECT * FROM character WHERE slug = ?", (slug,)).fetchone(),
        ("attributes", "aliases"),
    )


def list_characters(conn: ConnectionPort, canon_level: str | None = None) -> list[dict]:
    if canon_level:
        rows = conn.execute(
            "SELECT * FROM character WHERE canon_level = ? ORDER BY name",
            (canon_level,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM character ORDER BY name").fetchall()
    return [row_to_dict(r, ("attributes", "aliases")) for r in rows if r is not None]


def update_character(
    conn: ConnectionPort, char_id: int, patch: dict, expected_revision: int
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
            now_iso(), char_id, expected_revision,
        ),
    )
    if cur.rowcount == 0:
        raise CharacterRevisionConflict(
            f"character {char_id} revision != {expected_revision}"
        )
    conn.commit()
