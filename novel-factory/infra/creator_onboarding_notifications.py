"""Persist @mention notifications for creator onboarding wizard notes."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infra.creator_onboarding_progress import extract_step_mentions

_STATE_VERSION = "1"
_MAX_NOTIFICATIONS = 100
_MAX_NOTE_EXCERPT = 120


def _notifications_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_onboarding_notifications.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_store(project_root: Path | str) -> dict[str, Any]:
    path = _notifications_path(project_root)
    if not path.is_file():
        return {"schema_version": _STATE_VERSION, "notifications": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_store(project_root: Path | str, data: dict[str, Any]) -> None:
    path = _notifications_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def record_mentions_from_notes(
    project_root: Path | str,
    *,
    step_notes: dict[str, str],
    changed_step_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Create unread notifications for @mentions in updated step notes."""
    if not step_notes:
        return []
    store = _load_store(project_root)
    notifications: list[dict[str, Any]] = list(store.get("notifications") or [])
    created: list[dict[str, Any]] = []
    for step_id, note in step_notes.items():
        sid = str(step_id).strip()
        if not sid:
            continue
        if changed_step_ids is not None and sid not in changed_step_ids:
            continue
        text = str(note).strip()
        if not text:
            continue
        for handle in extract_step_mentions(text):
            entry = {
                "id": uuid.uuid4().hex[:12],
                "step_id": sid,
                "handle": handle,
                "note_excerpt": text[:_MAX_NOTE_EXCERPT],
                "created_at": _now_iso(),
                "read": False,
            }
            notifications.insert(0, entry)
            created.append(entry)
    store["notifications"] = notifications[:_MAX_NOTIFICATIONS]
    store["schema_version"] = _STATE_VERSION
    _save_store(project_root, store)
    return created


def list_onboarding_notifications(
    project_root: Path | str,
    *,
    unread_only: bool = False,
) -> list[dict[str, Any]]:
    store = _load_store(project_root)
    rows = list(store.get("notifications") or [])
    if unread_only:
        rows = [row for row in rows if not row.get("read")]
    return [
        {
            "id": str(row["id"]),
            "step_id": str(row.get("step_id", "")),
            "handle": str(row.get("handle", "")),
            "note_excerpt": str(row.get("note_excerpt", "")),
            "created_at": row.get("created_at"),
            "read": bool(row.get("read")),
        }
        for row in rows
    ]


def unread_mention_count(project_root: Path | str) -> int:
    return len(list_onboarding_notifications(project_root, unread_only=True))


def ack_onboarding_notifications(
    project_root: Path | str,
    *,
    notification_ids: list[str] | None = None,
    all_notifications: bool = False,
) -> dict[str, Any]:
    store = _load_store(project_root)
    notifications: list[dict[str, Any]] = list(store.get("notifications") or [])
    acked = 0
    if all_notifications:
        for row in notifications:
            if not row.get("read"):
                row["read"] = True
                acked += 1
    elif notification_ids:
        wanted = {str(nid).strip() for nid in notification_ids if str(nid).strip()}
        for row in notifications:
            if row.get("id") in wanted and not row.get("read"):
                row["read"] = True
                acked += 1
    store["notifications"] = notifications
    _save_store(project_root, store)
    return {"acked": acked, "unread": unread_mention_count(project_root)}
