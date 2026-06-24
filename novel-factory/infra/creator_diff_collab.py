"""Per-volume collaboration notes linked to volume-plan diff share (v2)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_STATE_VERSION = "1"
_MAX_NOTE_LEN = 500


def _path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_diff_collab_notes.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_notes(raw: Any) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    notes: dict[str, str] = {}
    for key, value in raw.items():
        label = str(key).strip()
        text = str(value).strip()[:_MAX_NOTE_LEN]
        if label and text:
            notes[label] = text
    return notes


def load_diff_collab_notes(project_root: Path | str) -> dict[str, str]:
    path = _path(project_root)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return _normalize_notes(data.get("notes", {}))


def save_diff_collab_notes(project_root: Path | str, notes: dict[str, str]) -> dict[str, str]:
    normalized = _normalize_notes(notes)
    path = _path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": _STATE_VERSION,
                "updated_at": _now_iso(),
                "notes": normalized,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return normalized


def merge_diff_collab_notes(
    existing: dict[str, str],
    incoming: dict[str, str],
) -> dict[str, str]:
    merged = dict(existing)
    for label, note in _normalize_notes(incoming).items():
        merged[label] = note
    return merged


def diff_collab_notes_payload(project_root: Path | str) -> dict[str, Any]:
    notes = load_diff_collab_notes(project_root)
    return {"notes": notes, "count": len(notes)}
