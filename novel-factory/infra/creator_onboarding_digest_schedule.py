"""Scheduled digest dispatch for creator onboarding notifications."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_STATE_VERSION = "1"
_MIN_INTERVAL_HOURS = 1
_MAX_INTERVAL_HOURS = 168
_MAX_RETRY_ITEMS = 20
_MAX_BACKOFF_SEC = 3600
_BASE_BACKOFF_SEC = 60


def _retry_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_onboarding_digest_retry.json"


def _dead_letter_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_onboarding_digest_dead_letter.json"


def _stats_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_onboarding_digest_stats.json"


def _backoff_seconds(attempts: int) -> int:
    return min(_MAX_BACKOFF_SEC, _BASE_BACKOFF_SEC * (2 ** max(0, attempts - 1)))


def load_digest_dispatch_stats(project_root: Path | str) -> dict[str, Any]:
    path = _stats_path(project_root)
    if not path.is_file():
        return {
            "schema_version": "1",
            "sent_total": 0,
            "failed_total": 0,
            "last_sent_at": None,
            "last_failure_at": None,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "schema_version": "1",
        "sent_total": int(data.get("sent_total") or 0),
        "failed_total": int(data.get("failed_total") or 0),
        "last_sent_at": data.get("last_sent_at"),
        "last_failure_at": data.get("last_failure_at"),
    }


def record_digest_dispatch(
    project_root: Path | str,
    *,
    success: bool,
) -> dict[str, Any]:
    path = _stats_path(project_root)
    stats = load_digest_dispatch_stats(project_root)
    now = _now_iso()
    if success:
        stats["sent_total"] = int(stats["sent_total"]) + 1
        stats["last_sent_at"] = now
    else:
        stats["failed_total"] = int(stats["failed_total"]) + 1
        stats["last_failure_at"] = now
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return stats


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


def load_digest_dead_letter(project_root: Path | str) -> dict[str, Any]:
    path = _dead_letter_path(project_root)
    if not path.is_file():
        return {"item_count": 0, "items": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items") or []
    return {"item_count": len(items), "items": items[:_MAX_RETRY_ITEMS]}


def _append_dead_letter(project_root: Path | str, item: dict[str, Any]) -> None:
    path = _dead_letter_path(project_root)
    existing = load_digest_dead_letter(project_root)
    items = [item, *existing["items"]]
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
    now = datetime.now(timezone.utc)
    items.insert(
        0,
        {
            "channel": str(channel).strip().lower(),
            "digest": digest,
            "error": str(error)[:240],
            "queued_at": _now_iso(),
            "attempts": 0,
            "next_retry_at": now.isoformat(),
        },
    )
    _save_retry_queue(project_root, items)
    record_digest_dispatch(project_root, success=False)


def process_digest_retries(project_root: Path | str) -> dict[str, Any]:
    """Retry failed digest channel dispatches with exponential backoff."""
    items = _load_retry_queue(project_root)
    if not items:
        return {"retried": 0, "remaining": 0}
    kept: list[dict[str, Any]] = []
    retried = 0
    now = datetime.now(timezone.utc)
    for item in items:
        next_at = _parse_iso(item.get("next_retry_at"))
        if next_at and now < next_at:
            kept.append(item)
            continue
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
            record_digest_dispatch(project_root, success=True)
        elif attempts < 5:
            item["attempts"] = attempts
            item["last_error"] = str(item.get("error", ""))
            delay = _backoff_seconds(attempts)
            item["next_retry_at"] = (now + timedelta(seconds=delay)).isoformat()
            kept.append(item)
        else:
            item["dead_lettered_at"] = _now_iso()
            _append_dead_letter(project_root, item)
    _save_retry_queue(project_root, kept)
    dead = load_digest_dead_letter(project_root)
    return {"retried": retried, "remaining": len(kept), "dead_letter_count": dead["item_count"]}


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


def _normalize_handle_channels(raw: Any) -> dict[str, list[str]]:
    if not isinstance(raw, dict):
        return {}
    routing: dict[str, list[str]] = {}
    for handle, channels in raw.items():
        key = str(handle).strip().lower()
        if not key:
            continue
        if isinstance(channels, list):
            normalized = list(
                dict.fromkeys(str(ch).strip().lower() for ch in channels if str(ch).strip()),
            )
            if normalized:
                routing[key] = normalized
    return routing


def _normalize_handle_quiet_hours(raw: Any) -> dict[str, dict[str, int]]:
    if not isinstance(raw, dict):
        return {}
    result: dict[str, dict[str, int]] = {}
    for handle, window in raw.items():
        if not isinstance(window, dict):
            continue
        start = _normalize_quiet_hour(window.get("start", window.get("quiet_hours_start")))
        end = _normalize_quiet_hour(window.get("end", window.get("quiet_hours_end")))
        key = str(handle).strip().lower()
        if key and start is not None and end is not None:
            result[key] = {"start": start, "end": end}
    return result


def _hour_in_quiet_range(start_h: int, end_h: int) -> bool:
    hour = datetime.now(timezone.utc).hour
    if start_h <= end_h:
        return start_h <= hour < end_h
    return hour >= start_h or hour < end_h


def _in_quiet_hours(schedule: dict[str, Any], *, handle: str | None = None) -> bool:
    if handle:
        windows = schedule.get("handle_quiet_hours") or {}
        key = str(handle).strip().lower() or "default"
        window = windows.get(key) or windows.get("*")
        if window:
            return _hour_in_quiet_range(int(window["start"]), int(window["end"]))
    start = schedule.get("quiet_hours_start")
    end = schedule.get("quiet_hours_end")
    if start is None or end is None:
        return False
    return _hour_in_quiet_range(int(start), int(end))


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


def _channels_for_handle(schedule: dict[str, Any], handle: str) -> list[str]:
    routing = schedule.get("handle_channels") or {}
    key = str(handle).strip().lower() or "default"
    if key in routing:
        return routing[key]
    if "*" in routing:
        return routing["*"]
    return schedule.get("channels") or ["webhook"]


def load_digest_schedule(project_root: Path | str) -> dict[str, Any]:
    path = _schedule_path(project_root)
    if not path.is_file():
        return {
            "schema_version": _STATE_VERSION,
            "enabled": False,
            "interval_hours": 24,
            "last_sent_at": None,
            "channels": ["webhook"],
            "handle_channels": {},
            "quiet_hours_start": None,
            "quiet_hours_end": None,
            "handle_quiet_hours": {},
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
        "handle_channels": _normalize_handle_channels(data.get("handle_channels")),
        "quiet_hours_start": _normalize_quiet_hour(data.get("quiet_hours_start")),
        "quiet_hours_end": _normalize_quiet_hour(data.get("quiet_hours_end")),
        "handle_quiet_hours": _normalize_handle_quiet_hours(data.get("handle_quiet_hours")),
    }


def save_digest_schedule(
    project_root: Path | str,
    *,
    enabled: bool,
    interval_hours: int = 24,
    channels: list[str] | None = None,
    handle_channels: dict[str, list[str]] | None = None,
    quiet_hours_start: int | None = None,
    quiet_hours_end: int | None = None,
    handle_quiet_hours: dict[str, dict[str, int]] | None = None,
) -> dict[str, Any]:
    hours = max(_MIN_INTERVAL_HOURS, min(int(interval_hours), _MAX_INTERVAL_HOURS))
    normalized_channels = ["webhook"]
    if channels is not None:
        normalized_channels = list(
            dict.fromkeys(str(ch).strip().lower() for ch in channels if str(ch).strip()),
        ) or ["webhook"]
    path = _schedule_path(project_root)
    existing = load_digest_schedule(project_root) if path.is_file() else {}
    routing = existing.get("handle_channels") or {}
    if handle_channels is not None:
        routing = _normalize_handle_channels(handle_channels)
    handle_quiet = existing.get("handle_quiet_hours") or {}
    if handle_quiet_hours is not None:
        handle_quiet = _normalize_handle_quiet_hours(handle_quiet_hours)
    data = {
        "schema_version": _STATE_VERSION,
        "enabled": bool(enabled),
        "interval_hours": hours,
        "last_sent_at": existing.get("last_sent_at"),
        "channels": normalized_channels,
        "handle_channels": routing,
        "quiet_hours_start": _normalize_quiet_hour(quiet_hours_start),
        "quiet_hours_end": _normalize_quiet_hour(quiet_hours_end),
        "handle_quiet_hours": handle_quiet,
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


def _dispatch_digest_channels(
    project_root: Path | str,
    digest: dict[str, Any],
    channels: list[str],
    results: dict[str, Any],
) -> None:
    payload = {"schema_version": "1", "type": "digest", "digest": digest}
    channel_ok = False
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
        else:
            channel_ok = True
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
        else:
            channel_ok = True
    if channel_ok:
        record_digest_dispatch(project_root, success=True)


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
    results: dict[str, Any] = {"digest": digest, "channels": {}, "handle_routes": {}, "skipped_handles": []}
    routing = schedule.get("handle_channels") or {}
    groups = digest.get("groups") or []
    if routing and groups:
        for group in groups:
            handle = str(group.get("handle") or "default")
            if not force and _in_quiet_hours(schedule, handle=handle):
                results["skipped_handles"].append(handle)
                continue
            channels = _channels_for_handle(schedule, handle)
            partial = {
                **digest,
                "groups": [group],
                "group_count": 1,
                "unread": int(group.get("count") or 0),
            }
            results["handle_routes"][handle] = channels
            _dispatch_digest_channels(project_root, partial, channels, results)
    else:
        channels = schedule.get("channels") or ["webhook"]
        _dispatch_digest_channels(project_root, digest, channels, results)
    path = _schedule_path(project_root)
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        data["last_sent_at"] = _now_iso()
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    results["sent"] = True
    results["last_sent_at"] = _now_iso()
    return results
