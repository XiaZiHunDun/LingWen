"""Timeline event CRUD with optimistic concurrency."""
import json
import sqlite3
from datetime import datetime, timezone


class TimelineRevisionConflict(Exception):
    """Raised when expected_revision does not match current timeline_event row."""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_to_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    d = dict(row)
    for k in ("related_characters", "related_factions"):
        if d.get(k):
            d[k] = json.loads(d[k])
    return d


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    return [_row_to_dict(r) for r in rows]  # type: ignore[misc]


def create_timeline_event(conn: sqlite3.Connection, data: dict) -> int:
    now = _now()
    cur = conn.execute(
        """INSERT INTO timeline_event
           (slug, title, story_year, story_label, chapter, description,
            category, related_characters, related_factions,
            created_at, updated_at, revision)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
        (
            data["slug"], data["title"],
            data.get("story_year"), data.get("story_label"),
            data.get("chapter"), data.get("description"),
            data.get("category"),
            json.dumps(data.get("related_characters") or [], ensure_ascii=False),
            json.dumps(data.get("related_factions") or [], ensure_ascii=False),
            now, now,
        ),
    )
    conn.commit()
    return cur.lastrowid


def list_timeline(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM timeline_event ORDER BY story_year"
    ).fetchall()
    return _rows_to_dicts(rows)


def get_timeline_event(conn: sqlite3.Connection, tid: int) -> dict | None:
    row = conn.execute(
        "SELECT * FROM timeline_event WHERE id = ?", (tid,)
    ).fetchone()
    return _row_to_dict(row)


def update_timeline_event(
    conn: sqlite3.Connection, tid: int, patch: dict, expected_revision: int
) -> None:
    related_chars = (
        json.dumps(patch["related_characters"], ensure_ascii=False)
        if "related_characters" in patch else None
    )
    related_facts = (
        json.dumps(patch["related_factions"], ensure_ascii=False)
        if "related_factions" in patch else None
    )
    cur = conn.execute(
        """UPDATE timeline_event SET
           title = COALESCE(?, title),
           story_year = COALESCE(?, story_year),
           story_label = COALESCE(?, story_label),
           chapter = COALESCE(?, chapter),
           description = COALESCE(?, description),
           category = COALESCE(?, category),
           related_characters = COALESCE(?, related_characters),
           related_factions = COALESCE(?, related_factions),
           updated_at = ?,
           revision = revision + 1
           WHERE id = ? AND revision = ?""",
        (
            patch.get("title"),
            patch.get("story_year"), patch.get("story_label"),
            patch.get("chapter"), patch.get("description"),
            patch.get("category"),
            related_chars, related_facts,
            _now(), tid, expected_revision,
        ),
    )
    if cur.rowcount == 0:
        raise TimelineRevisionConflict(
            f"timeline_event {tid} revision != {expected_revision}"
        )
    conn.commit()
