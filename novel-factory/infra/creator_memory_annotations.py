"""Per-asset memory annotations (note, pin) stored in project state."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_STATE_VERSION = "1"
_NOTE_MAX_LEN = 500


def _annotations_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_memory_annotations.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_raw(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"schema_version": _STATE_VERSION, "items": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("items"), dict):
        data["items"] = {}
    return data


def _save_raw(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_memory_annotations(project_root: Path | str) -> dict[str, dict[str, Any]]:
    path = _annotations_path(project_root)
    data = _load_raw(path)
    items = data.get("items") or {}
    return {str(k): v for k, v in items.items() if isinstance(v, dict)}


def upsert_memory_annotation(
    project_root: Path | str,
    asset_id: str,
    *,
    note: str | None = None,
    pinned: bool | None = None,
) -> dict[str, Any]:
    asset_key = (asset_id or "").strip()
    if not asset_key:
        raise ValueError("asset_id is required")

    path = _annotations_path(project_root)
    data = _load_raw(path)
    items: dict[str, Any] = data.setdefault("items", {})
    current = dict(items.get(asset_key) or {})

    if note is not None:
        trimmed = note.strip()[:_NOTE_MAX_LEN]
        if trimmed:
            current["note"] = trimmed
        else:
            current.pop("note", None)

    if pinned is not None:
        current["pinned"] = bool(pinned)

    if not current:
        items.pop(asset_key, None)
    else:
        current["updated_at"] = _now_iso()
        items[asset_key] = current

    data["schema_version"] = _STATE_VERSION
    _save_raw(path, data)
    return {"asset_id": asset_key, **current}


def apply_memory_annotations(
    items: list[dict[str, Any]],
    annotations: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for row in items:
        entry = dict(row)
        ann = annotations.get(str(entry.get("id") or "")) or {}
        if ann.get("note"):
            entry["note"] = str(ann["note"])
        entry["pinned"] = bool(ann.get("pinned"))
        enriched.append(entry)

    enriched.sort(
        key=lambda r: (
            0 if r.get("pinned") else 1,
            0 if not r.get("placeholder") else 2,
            str(r.get("name") or ""),
        ),
    )
    return enriched
