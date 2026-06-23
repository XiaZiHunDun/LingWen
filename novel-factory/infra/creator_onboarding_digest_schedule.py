"""Scheduled digest dispatch for creator onboarding notifications."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_STATE_VERSION = "1"
_MIN_INTERVAL_HOURS = 1
_MAX_INTERVAL_HOURS = 168


def _schedule_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_onboarding_digest_schedule.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None


def load_digest_schedule(project_root: Path | str) -> dict[str, Any]:
    path = _schedule_path(project_root)
    if not path.is_file():
        return {
            "schema_version": _STATE_VERSION,
            "enabled": False,
            "interval_hours": 24,
            "last_sent_at": None,
            "channels": ["webhook"],
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    hours = int(data.get("interval_hours", 24))
    hours = max(_MIN_INTERVAL_HOURS, min(hours, _MAX_INTERVAL_HOURS))
    channels = data.get("channels") or ["webhook"]
    if not isinstance(channels, list):
        channels = ["webhook"]
    return {
        "schema_version": _STATE_VERSION,
        "enabled": bool(data.get("enabled")),
        "interval_hours": hours,
        "last_sent_at": data.get("last_sent_at"),
        "channels": [str(ch).strip().lower() for ch in channels if str(ch).strip()],
    }


def save_digest_schedule(
    project_root: Path | str,
    *,
    enabled: bool,
    interval_hours: int = 24,
    channels: list[str] | None = None,
) -> dict[str, Any]:
    hours = max(_MIN_INTERVAL_HOURS, min(int(interval_hours), _MAX_INTERVAL_HOURS))
    normalized_channels = ["webhook"]
    if channels is not None:
        normalized_channels = list(
            dict.fromkeys(str(ch).strip().lower() for ch in channels if str(ch).strip()),
        ) or ["webhook"]
    path = _schedule_path(project_root)
    existing = load_digest_schedule(project_root) if path.is_file() else {}
    data = {
        "schema_version": _STATE_VERSION,
        "enabled": bool(enabled),
        "interval_hours": hours,
        "last_sent_at": existing.get("last_sent_at"),
        "channels": normalized_channels,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return load_digest_schedule(project_root)


def _due_for_dispatch(schedule: dict[str, Any], *, force: bool = False) -> bool:
    if force:
        return True
    if not schedule.get("enabled"):
        return False
    last = _parse_iso(schedule.get("last_sent_at"))
    if last is None:
        return True
    elapsed_hours = (datetime.now(timezone.utc) - last).total_seconds() / 3600
    return elapsed_hours >= float(schedule.get("interval_hours", 24))


def dispatch_scheduled_digest(
    project_root: Path | str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Send notification digest when schedule interval elapsed."""
    from infra.creator_onboarding_notifications import build_notification_digest

    schedule = load_digest_schedule(project_root)
    if not _due_for_dispatch(schedule, force=force):
        return {"sent": False, "skipped": True, "reason": "not due"}
    digest = build_notification_digest(project_root)
    if digest.get("unread", 0) == 0:
        return {"sent": False, "skipped": True, "reason": "no unread notifications"}
    channels = schedule.get("channels") or ["webhook"]
    results: dict[str, Any] = {"digest": digest, "channels": {}}
    payload = {"schema_version": "1", "type": "digest", "digest": digest}
    if "webhook" in channels:
        from infra.creator_onboarding_webhook import dispatch_digest_webhook

        results["channels"]["webhook"] = dispatch_digest_webhook(project_root, payload)
    if "email" in channels:
        from infra.creator_onboarding_email import dispatch_digest_email

        results["channels"]["email"] = dispatch_digest_email(project_root, digest)
    path = _schedule_path(project_root)
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        data["last_sent_at"] = _now_iso()
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    results["sent"] = True
    results["last_sent_at"] = _now_iso()
    return results
