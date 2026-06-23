"""Persist creator onboarding wizard step completion per project."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_STATE_VERSION = "2"
_MAX_NOTE_LEN = 500


def _progress_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_onboarding_progress.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_step_notes(raw: Any) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    notes: dict[str, str] = {}
    for key, value in raw.items():
        sid = str(key).strip()
        text = str(value).strip()[:_MAX_NOTE_LEN]
        if sid and text:
            notes[sid] = text
    return notes


def load_onboarding_progress(project_root: Path | str) -> dict[str, Any]:
    path = _progress_path(project_root)
    if not path.is_file():
        return {
            "schema_version": _STATE_VERSION,
            "completed_step_ids": [],
            "dismissed_auto_step_ids": [],
            "step_notes": {},
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    ids = data.get("completed_step_ids", [])
    dismissed = data.get("dismissed_auto_step_ids", [])
    if not isinstance(ids, list):
        ids = []
    if not isinstance(dismissed, list):
        dismissed = []
    return {
        "schema_version": _STATE_VERSION,
        "completed_step_ids": [str(x) for x in ids],
        "dismissed_auto_step_ids": [str(x) for x in dismissed],
        "step_notes": _normalize_step_notes(data.get("step_notes", {})),
    }


def save_onboarding_progress(
    project_root: Path | str,
    *,
    completed_step_ids: list[str],
    dismissed_auto_step_ids: list[str] | None = None,
    step_notes: dict[str, str] | None = None,
) -> dict[str, Any]:
    path = _progress_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_onboarding_progress(project_root) if path.is_file() else {
        "step_notes": {},
    }
    unique_ids: list[str] = []
    seen: set[str] = set()
    for step_id in completed_step_ids:
        sid = str(step_id).strip()
        if sid and sid not in seen:
            seen.add(sid)
            unique_ids.append(sid)
    dismissed_unique: list[str] = []
    dismissed_seen: set[str] = set()
    for step_id in dismissed_auto_step_ids or []:
        sid = str(step_id).strip()
        if sid and sid not in dismissed_seen:
            dismissed_seen.add(sid)
            dismissed_unique.append(sid)
    merged_notes = dict(existing.get("step_notes", {}))
    if step_notes is not None:
        for key, value in step_notes.items():
            sid = str(key).strip()
            text = str(value).strip()[:_MAX_NOTE_LEN]
            if sid and text:
                merged_notes[sid] = text
            elif sid in merged_notes:
                del merged_notes[sid]
    data = {
        "schema_version": _STATE_VERSION,
        "completed_step_ids": unique_ids,
        "dismissed_auto_step_ids": dismissed_unique,
        "step_notes": merged_notes,
        "updated_at": _now_iso(),
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def merge_step_notes(
    existing: dict[str, str],
    incoming: dict[str, str],
    *,
    valid_step_ids: set[str] | None = None,
) -> dict[str, str]:
    merged = dict(existing)
    for key, value in incoming.items():
        sid = str(key).strip()
        if valid_step_ids is not None and sid not in valid_step_ids:
            continue
        text = str(value).strip()[:_MAX_NOTE_LEN]
        if sid and text:
            merged[sid] = text
    return merged


def effective_completed_step_ids(
    *,
    step_ids: list[str],
    auto_completed: list[str],
    manual_completed: list[str],
    dismissed_auto: list[str],
) -> list[str]:
    """Merge auto + manual completion, respecting user-dismissed auto steps."""
    valid = set(step_ids)
    dismissed = set(dismissed_auto) & valid
    auto = [sid for sid in auto_completed if sid in valid and sid not in dismissed]
    manual = [sid for sid in manual_completed if sid in valid]
    combined: list[str] = []
    seen: set[str] = set()
    for sid in auto + manual:
        if sid not in seen:
            seen.add(sid)
            combined.append(sid)
    return combined


def reconcile_onboarding_toggle(
    *,
    step_ids: list[str],
    auto_completed: list[str],
    manual_completed: list[str],
    dismissed_auto: list[str],
    desired_completed: list[str],
) -> tuple[list[str], list[str]]:
    """Compute manual + dismissed lists from checkbox state."""
    valid = set(step_ids)
    desired = set(desired_completed) & valid
    auto = set(auto_completed) & valid
    manual = [sid for sid in desired if sid not in auto]
    dismissed = [sid for sid in auto if sid not in desired]
    for sid in dismissed_auto:
        if sid in valid and sid not in desired and sid not in dismissed:
            dismissed.append(sid)
    dismissed = list(dict.fromkeys(dismissed))
    return manual, dismissed


def progress_pct(completed_step_ids: list[str], total_steps: int) -> int:
    if total_steps < 1:
        return 0
    return min(100, round(len(completed_step_ids) * 100 / total_steps))
