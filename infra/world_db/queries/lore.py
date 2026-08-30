"""Lore CRUD with optimistic concurrency."""
import json

from lingwen_shared.ports.storage import ConnectionPort

from infra.world_db.queries._helpers import (
    RevisionConflict,
    now_iso,
    row_to_dict,
)


class LoreRevisionConflict(RevisionConflict):
    """Raised when expected_revision does not match current lore row."""


def create_lore(conn: ConnectionPort, data: dict) -> int:
    now = now_iso()
    cur = conn.execute(
        """INSERT INTO lore_entry
           (slug, title, category, summary, body, tags, created_at, updated_at, revision)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)""",
        (
            data["slug"], data["title"], data["category"],
            data["summary"], data["body"],
            json.dumps(data.get("tags") or [], ensure_ascii=False),
            now, now,
        ),
    )
    conn.commit()
    return cur.lastrowid


def get_lore(conn: ConnectionPort, lid: int) -> dict | None:
    return row_to_dict(
        conn.execute("SELECT * FROM lore_entry WHERE id = ?", (lid,)).fetchone(),
        ("tags",),
    )


def get_lore_by_slug(conn: ConnectionPort, slug: str) -> dict | None:
    return row_to_dict(
        conn.execute("SELECT * FROM lore_entry WHERE slug = ?", (slug,)).fetchone(),
        ("tags",),
    )


def list_lore(conn: ConnectionPort, category: str | None = None) -> list[dict]:
    if category:
        rows = conn.execute(
            "SELECT * FROM lore_entry WHERE category = ? ORDER BY title",
            (category,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM lore_entry ORDER BY title").fetchall()
    return [row_to_dict(r, ("tags",)) for r in rows if r is not None]


def update_lore(
    conn: ConnectionPort, lid: int, patch: dict, expected_revision: int
) -> None:
    tags_value = (
        json.dumps(patch["tags"], ensure_ascii=False) if "tags" in patch else None
    )
    cur = conn.execute(
        """UPDATE lore_entry SET
           title = COALESCE(?, title),
           category = COALESCE(?, category),
           summary = COALESCE(?, summary),
           body = COALESCE(?, body),
           tags = COALESCE(?, tags),
           updated_at = ?,
           revision = revision + 1
           WHERE id = ? AND revision = ?""",
        (
            patch.get("title"), patch.get("category"),
            patch.get("summary"), patch.get("body"),
            tags_value, now_iso(), lid, expected_revision,
        ),
    )
    if cur.rowcount == 0:
        raise LoreRevisionConflict(
            f"lore {lid} revision != {expected_revision}"
        )
    conn.commit()
