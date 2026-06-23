"""Scheduled digest dispatch for creator onboarding notifications."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_STATE_VERSION = "1"
_MIN_INTERVAL_HOURS = 1
_MAX_INTERVAL_HOURS = 168
_MAX_RETRY_ITEMS = 20


def _retry_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_onboarding_digest_retry.json"


def _load_retry_queue(project_root: Path | str) -> list[dict[str, Any]]:
    path = _retry_path(project_root)
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("items") or []
    return [row for row in rows if isinstance(row, dict)]


def _save_retry_queue(project_root: Path | str, items: list[dict[str, Any]]) -> None:
    path = _retry_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"schema_version": "1", "items": items[:_MAX_RETRY_ITEMS]}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )


def load_digest_retry_queue(project_root: Path | str) -> dict[str, Any]:
    items = _load_retry_queue(project_root)
    return {"item_count": len(items), "items": items}


def enqueue_digest_retry(
    project_root: Path | str,
    *,
    channel: str,
    digest: dict[str, Any],
    error: str = "",
) -> None:
    items = _load_retry_queue(project_root)
    items.insert(
        0,
        {
            "channel": str(channel).strip().lower(),
            "digest": digest,
            "error": str(error)[:240],
            "queued_at": _now_iso(),
            "attempts": 0,
        },
    )
    _save_retry_queue(project_root, items)


def process_digest_retries(project_root: Path | str) -> dict[str, Any]:
    """Retry failed digest channel dispatches."""
    items = _load_retry_queue(project_root)
    if not items:
        return {"retried": 0, "remaining": 0}
    kept: list[dict[str, Any]] = []
    retried = 0
    for item in items:
        channel = str(item.get("channel", "")).lower()
        digest = item.get("digest") or {}
        attempts = int(item.get("attempts") or 0) + 1
        payload = {"schema_version": "1", "type": "digest", "digest": digest}
        ok = False
        if channel == "webhook":
            from infra.creator_onboarding_webhook import dispatch_digest_webhook

            result = dispatch_digest_webhook(project_root, payload)
            ok = bool(result.get("dispatched")) and not result.get("error")
        elif channel == "email":
            from infra.creator_onboarding_email import dispatch_digest_email

            result = dispatch_digest_email(project_root, digest)
            ok = bool(result.get("sent")) and not result.get("error")
        if ok:
            retried += 1
        elif attempts < 5:
            item["attempts"] = attempts
            item["last_error"] = str(item.get("error", ""))
            kept.append(item)
    _save_retry_queue(project_root, kept)
    return {"retried": retried, "remaining": len(kept)}


def _normalize_quiet_hour(raw: Any) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        hour = int(raw)
    except (TypeError, ValueError):
        return None
    if 0 <= hour <= 23:
        return hour
    return None


def _in_quiet_hours(schedule: dict[str, Any]) -> bool:
    start = schedule.get("quiet_hours_start")
    end = schedule.get("quiet_hours_end")
    if start is None or end is None:
        return False
    hour = datetime.now(timezone.utc).hour
    start_h = int(start)
    end_h = int(end)
    if start_h <= end_h:
        return start_h <= hour < end_h
    return hour >= start_h or hour < end_h


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
            "quiet_hours_start": None,
            "quiet_hours_end": None,
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
        "quiet_hours_start": _normalize_quiet_hour(data.get("quiet_hours_start")),
        "quiet_hours_end": _normalize_quiet_hour(data.get("quiet_hours_end")),
    }


def save_digest_schedule(
    project_root: Path | str,
    *,
    enabled: bool,
    interval_hours: int = 24,
    channels: list[str] | None = None,
    quiet_hours_start: int | None = None,
    quiet_hours_end: int | None = None,
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
        "quiet_hours_start": _normalize_quiet_hour(quiet_hours_start),
        "quiet_hours_end": _normalize_quiet_hour(quiet_hours_end),
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
    if not force and _in_quiet_hours(schedule):
        return {"sent": False, "skipped": True, "reason": "quiet hours"}
    digest = build_notification_digest(project_root)
    if digest.get("unread", 0) == 0:
        return {"sent": False, "skipped": True, "reason": "no unread notifications"}
    channels = schedule.get("channels") or ["webhook"]
    results: dict[str, Any] = {"digest": digest, "channels": {}}
    payload = {"schema_version": "1", "type": "digest", "digest": digest}
    if "webhook" in channels:
        from infra.creator_onboarding_webhook import dispatch_digest_webhook

        webhook_result = dispatch_digest_webhook(project_root, payload)
        results["channels"]["webhook"] = webhook_result
        if webhook_result.get("error") or not webhook_result.get("dispatched"):
            enqueue_digest_retry(
                project_root,
                channel="webhook",
                digest=digest,
                error=str(webhook_result.get("error", "webhook failed")),
            )
    if "email" in channels:
        from infra.creator_onboarding_email import dispatch_digest_email

        email_result = dispatch_digest_email(project_root, digest)
        results["channels"]["email"] = email_result
        if email_result.get("error") or not email_result.get("sent"):
            enqueue_digest_retry(
                project_root,
                channel="email",
                digest=digest,
                error=str(email_result.get("error", "email failed")),
            )
    path = _schedule_path(project_root)
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        data["last_sent_at"] = _now_iso()
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    results["sent"] = True
    results["last_sent_at"] = _now_iso()
    return results
