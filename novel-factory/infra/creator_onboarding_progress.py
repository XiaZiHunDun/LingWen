"""Persist creator onboarding wizard step completion per project."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_STATE_VERSION = "1"


def _progress_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_onboarding_progress.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_onboarding_progress(project_root: Path | str) -> dict[str, Any]:
    path = _progress_path(project_root)
    if not path.is_file():
        return {"schema_version": _STATE_VERSION, "completed_step_ids": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    ids = data.get("completed_step_ids", [])
    if not isinstance(ids, list):
        ids = []
    return {
        "schema_version": _STATE_VERSION,
        "completed_step_ids": [str(x) for x in ids],
    }


def save_onboarding_progress(
    project_root: Path | str,
    *,
    completed_step_ids: list[str],
) -> dict[str, Any]:
    path = _progress_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    unique_ids: list[str] = []
    seen: set[str] = set()
    for step_id in completed_step_ids:
        sid = str(step_id).strip()
        if sid and sid not in seen:
            seen.add(sid)
            unique_ids.append(sid)
    data = {
        "schema_version": _STATE_VERSION,
        "completed_step_ids": unique_ids,
        "updated_at": _now_iso(),
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def progress_pct(completed_step_ids: list[str], total_steps: int) -> int:
    if total_steps < 1:
        return 0
    return min(100, round(len(completed_step_ids) * 100 / total_steps))
