"""Lore CRUD with optimistic concurrency."""
import json
import sqlite3
from datetime import datetime, timezone


class LoreRevisionConflict(Exception):
    """Raised when expected_revision does not match current lore row."""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_to_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    d = dict(row)
    if d.get("tags"):
        d["tags"] = json.loads(d["tags"])
    return d


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    return [_row_to_dict(r) for r in rows]  # type: ignore[misc]


def create_lore(conn: sqlite3.Connection, data: dict) -> int:
    now = _now()
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


def get_lore(conn: sqlite3.Connection, lid: int) -> dict | None:
    row = conn.execute("SELECT * FROM lore_entry WHERE id = ?", (lid,)).fetchone()
    return _row_to_dict(row)


def get_lore_by_slug(conn: sqlite3.Connection, slug: str) -> dict | None:
    row = conn.execute("SELECT * FROM lore_entry WHERE slug = ?", (slug,)).fetchone()
    return _row_to_dict(row)


def list_lore(conn: sqlite3.Connection, category: str | None = None) -> list[dict]:
    if category:
        rows = conn.execute(
            "SELECT * FROM lore_entry WHERE category = ? ORDER BY title",
            (category,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM lore_entry ORDER BY title").fetchall()
    return _rows_to_dicts(rows)


def update_lore(
    conn: sqlite3.Connection, lid: int, patch: dict, expected_revision: int
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
            tags_value, _now(), lid, expected_revision,
        ),
    )
    if cur.rowcount == 0:
        raise LoreRevisionConflict(
            f"lore {lid} revision != {expected_revision}"
        )
    conn.commit()
