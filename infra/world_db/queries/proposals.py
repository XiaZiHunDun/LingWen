"""Proposal CRUD for review flow."""

import json

from lingwen_shared.ports.storage import ConnectionPort

from infra.world_db.queries._helpers import now_iso, row_to_dict


def create_proposal(conn: ConnectionPort, data: dict) -> int:
    cur = conn.execute(
        """INSERT INTO proposal
           (kind, target_kind, target_id, payload, source, source_context,
            status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)""",
        (
            data["kind"],
            data.get("target_kind"),
            data.get("target_id"),
            json.dumps(data["payload"], ensure_ascii=False),
            data["source"],
            data.get("source_context"),
            now_iso(),
        ),
    )
    conn.commit()
    return cur.lastrowid


def list_proposals(conn: ConnectionPort, status: str | None = None) -> list[dict]:
    if status:
        rows = conn.execute(
            "SELECT * FROM proposal WHERE status = ? ORDER BY created_at DESC",
            (status,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM proposal ORDER BY created_at DESC").fetchall()
    return [row_to_dict(r, ("payload",)) for r in rows if r is not None]


def get_proposal(conn: ConnectionPort, pid: int) -> dict | None:
    return row_to_dict(
        conn.execute("SELECT * FROM proposal WHERE id = ?", (pid,)).fetchone(),
        ("payload",),
    )


def update_proposal_status(
    conn: ConnectionPort,
    pid: int,
    status: str,
    reviewer: str | None = None,
) -> None:
    """Update proposal status. Raises ValueError if proposal does not exist."""
    cur = conn.execute(
        """UPDATE proposal SET status = ?, reviewer = ?, reviewed_at = ?
           WHERE id = ?""",
        (status, reviewer, now_iso(), pid),
    )
    if cur.rowcount == 0:
        raise ValueError(f"proposal {pid} not found")
    conn.commit()
