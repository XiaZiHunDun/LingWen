"""Creator publish job log with PublishAdapter handoff."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infra.creator_publish_adapters import get_publish_adapter, list_publish_platforms
from infra.studio_registry import StudioProject

_STATE_VERSION = "1"
_MAX_ENTRIES = 30
_VALID_PLATFORMS = frozenset({"fanqie", "qidian", "jjwxc", "custom"})

__all__ = [
    "submit_creator_publish",
    "list_creator_publish_history",
    "list_publish_platforms",
]


def _log_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_publish_log.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_log(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"schema_version": _STATE_VERSION, "entries": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_log(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def submit_creator_publish(
    project: StudioProject,
    *,
    platform: str,
    include_outline: bool = True,
    intro: str = "",
    mode: str = "submission",
) -> dict[str, Any]:
    platform_id = platform if platform in _VALID_PLATFORMS else "custom"
    adapter = get_publish_adapter(platform_id)
    mode_val = mode if mode in {"full", "range", "submission"} else "submission"
    outcome = adapter.submit(
        project,
        include_outline=include_outline,
        intro=intro,
        mode=mode_val,
    )
    path = _log_path(project.root)
    data = _load_log(path)
    entry = {
        "id": uuid.uuid4().hex[:12],
        "platform": platform_id,
        "include_outline": bool(include_outline),
        "intro": (intro or "").strip(),
        "mode": mode_val,
        "status": outcome.status,
        "message": outcome.message,
        "adapter_id": outcome.adapter_id,
        "connection": outcome.connection,
        "external_url": outcome.external_url,
        "package_hint": outcome.package_hint,
        "created_at": _now_iso(),
    }
    entries = [entry, *(data.get("entries") or [])]
    data["entries"] = entries[:_MAX_ENTRIES]
    _save_log(path, data)
    return entry


def list_creator_publish_history(project: StudioProject, *, limit: int = 10) -> dict[str, Any]:
    path = _log_path(project.root)
    data = _load_log(path)
    entries = list(data.get("entries") or [])[: max(1, min(limit, _MAX_ENTRIES))]
    return {
        "slug": project.slug,
        "entries": entries,
    }
