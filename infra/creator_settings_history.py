"""Settings document version history for creator mode."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infra.creator_volume_plan import global_outline_path
from infra.paths import ProjectPaths
from infra.project_config import ProjectConfig
from infra.studio_registry import StudioProject

_HISTORY_VERSION = "1"
_MAX_SNAPSHOTS = 10
_EXCERPT_LEN = 120


def _history_path(project_root: Path) -> Path:
    return project_root / ".state" / "creator_settings_history.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _excerpt(text: str) -> str:
    compact = text.strip().replace("\n", " ")
    if len(compact) <= _EXCERPT_LEN:
        return compact
    return compact[: _EXCERPT_LEN - 1] + "…"


def _load_history(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"schema_version": _HISTORY_VERSION, "snapshots": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_history(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_settings_snapshot(
    project: StudioProject,
    *,
    pillars_text: str,
    global_outline_text: str,
    label: str = "save",
) -> dict[str, Any]:
    """Store a snapshot of settings before overwrite."""
    path = _history_path(project.root)
    data = _load_history(path)
    snapshot = {
        "id": uuid.uuid4().hex[:12],
        "saved_at": _now_iso(),
        "label": label,
        "pillars_text": pillars_text,
        "global_outline_text": global_outline_text,
    }
    snapshots: list[dict[str, Any]] = data.get("snapshots", [])
    snapshots.insert(0, snapshot)
    data["snapshots"] = snapshots[:_MAX_SNAPSHOTS]
    data["schema_version"] = _HISTORY_VERSION
    _save_history(path, data)
    return snapshot


def settings_history_payload(project: StudioProject) -> dict[str, Any]:
    path = _history_path(project.root)
    data = _load_history(path)
    items: list[dict[str, Any]] = []
    for snap in data.get("snapshots", []):
        pillars = str(snap.get("pillars_text", ""))
        outline = str(snap.get("global_outline_text", ""))
        items.append(
            {
                "id": snap["id"],
                "saved_at": snap.get("saved_at"),
                "label": snap.get("label", "save"),
                "pillars_excerpt": _excerpt(pillars),
                "global_outline_excerpt": _excerpt(outline),
                "pillars_lines": len(pillars.splitlines()) if pillars else 0,
                "global_outline_lines": len(outline.splitlines()) if outline else 0,
            },
        )
    return {
        "slug": ProjectConfig.load(ProjectPaths.get(project.root)).slug,
        "snapshots": items,
        "count": len(items),
    }


def restore_settings_snapshot(project: StudioProject, snapshot_id: str) -> dict[str, Any]:
    from infra.creator_settings_docs import creator_settings_docs_payload

    path = _history_path(project.root)
    data = _load_history(path)
    match = next(
        (snap for snap in data.get("snapshots", []) if snap.get("id") == snapshot_id),
        None,
    )
    if match is None:
        raise ValueError(f"unknown snapshot: {snapshot_id!r}")

    current = creator_settings_docs_payload(project)
    append_settings_snapshot(
        project,
        pillars_text=current["pillars_text"],
        global_outline_text=current["global_outline_text"],
        label=f"before-restore-{snapshot_id}",
    )

    paths = ProjectPaths.get(project.root)
    config = ProjectConfig.load(paths)
    pillars_path = config.pillars_path
    outline_path = global_outline_path(project.root)
    pillars_path.parent.mkdir(parents=True, exist_ok=True)
    outline_path.parent.mkdir(parents=True, exist_ok=True)
    pillars_path.write_text(str(match["pillars_text"]).rstrip() + "\n", encoding="utf-8")
    outline_path.write_text(str(match["global_outline_text"]).rstrip() + "\n", encoding="utf-8")
    return creator_settings_docs_payload(project)


def load_snapshot_raw(project: StudioProject, snapshot_id: str) -> dict[str, Any]:
    path = _history_path(project.root)
    data = _load_history(path)
    match = next(
        (snap for snap in data.get("snapshots", []) if snap.get("id") == snapshot_id),
        None,
    )
    if match is None:
        raise ValueError(f"unknown snapshot: {snapshot_id!r}")
    return match
