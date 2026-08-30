"""Timeline event CRUD with optimistic concurrency."""
import json

from lingwen_shared.ports.storage import ConnectionPort

from infra.world_db.queries._helpers import (
    RevisionConflict,
    now_iso,
    row_to_dict,
)


class TimelineRevisionConflict(RevisionConflict):
    """Raised when expected_revision does not match current timeline_event row."""


def create_timeline_event(conn: ConnectionPort, data: dict) -> int:
    now = now_iso()
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


def list_timeline(conn: ConnectionPort) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM timeline_event ORDER BY story_year"
    ).fetchall()
    return [
        row_to_dict(r, ("related_characters", "related_factions"))
        for r in rows if r is not None
    ]


def get_timeline_event(conn: ConnectionPort, tid: int) -> dict | None:
    return row_to_dict(
        conn.execute("SELECT * FROM timeline_event WHERE id = ?", (tid,)).fetchone(),
        ("related_characters", "related_factions"),
    )


def update_timeline_event(
    conn: ConnectionPort, tid: int, patch: dict, expected_revision: int
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
            now_iso(), tid, expected_revision,
        ),
    )
    if cur.rowcount == 0:
        raise TimelineRevisionConflict(
            f"timeline_event {tid} revision != {expected_revision}"
        )
    conn.commit()
