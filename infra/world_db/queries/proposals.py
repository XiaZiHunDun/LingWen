"""Proposal CRUD for review flow."""
import json
import sqlite3
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_to_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    d = dict(row)
    if d.get("payload"):
        d["payload"] = json.loads(d["payload"])
    return d


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    return [_row_to_dict(r) for r in rows]  # type: ignore[misc]


def create_proposal(conn: sqlite3.Connection, data: dict) -> int:
    cur = conn.execute(
        """INSERT INTO proposal
           (kind, target_kind, target_id, payload, source, source_context,
            status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)""",
        (
            data["kind"], data.get("target_kind"), data.get("target_id"),
            json.dumps(data["payload"], ensure_ascii=False),
            data["source"], data.get("source_context"), _now(),
        ),
    )
    conn.commit()
    return cur.lastrowid


def list_proposals(
    conn: sqlite3.Connection, status: str | None = None
) -> list[dict]:
    if status:
        rows = conn.execute(
            "SELECT * FROM proposal WHERE status = ? ORDER BY created_at DESC",
            (status,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM proposal ORDER BY created_at DESC"
        ).fetchall()
    return _rows_to_dicts(rows)


def get_proposal(conn: sqlite3.Connection, pid: int) -> dict | None:
    row = conn.execute("SELECT * FROM proposal WHERE id = ?", (pid,)).fetchone()
    return _row_to_dict(row)


def update_proposal_status(
    conn: sqlite3.Connection,
    pid: int,
    status: str,
    reviewer: str | None = None,
) -> None:
    """Update proposal status. Raises ValueError if proposal does not exist."""
    cur = conn.execute(
        """UPDATE proposal SET status = ?, reviewer = ?, reviewed_at = ?
           WHERE id = ?""",
        (status, reviewer, _now(), pid),
    )
    if cur.rowcount == 0:
        raise ValueError(f"proposal {pid} not found")
    conn.commit()
