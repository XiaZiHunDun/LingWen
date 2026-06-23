"""Webhook dispatch for creator onboarding @mention notifications."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

_STATE_VERSION = "1"
_MAX_URL = 512
_WEBHOOK_TIMEOUT_SEC = 5


def _webhook_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_onboarding_webhook.json"


def load_webhook_config(project_root: Path | str) -> dict[str, Any]:
    path = _webhook_path(project_root)
    if not path.is_file():
        return {
            "schema_version": _STATE_VERSION,
            "enabled": False,
            "url": "",
            "mention_handles": [],
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    handles = data.get("mention_handles") or []
    if not isinstance(handles, list):
        handles = []
    return {
        "schema_version": _STATE_VERSION,
        "enabled": bool(data.get("enabled")),
        "url": str(data.get("url", ""))[:_MAX_URL],
        "mention_handles": [str(h).strip().lower() for h in handles if str(h).strip()],
    }


def save_webhook_config(
    project_root: Path | str,
    *,
    url: str,
    enabled: bool = True,
    mention_handles: list[str] | None = None,
) -> dict[str, Any]:
    normalized_url = str(url).strip()[:_MAX_URL]
    if enabled and normalized_url and not normalized_url.startswith(("http://", "https://")):
        raise ValueError("webhook url must start with http:// or https://")
    handles: list[str] = []
    if mention_handles is not None:
        handles = list(
            dict.fromkeys(str(h).strip().lower() for h in mention_handles if str(h).strip()),
        )
    data = {
        "schema_version": _STATE_VERSION,
        "enabled": bool(enabled),
        "url": normalized_url,
        "mention_handles": handles,
    }
    path = _webhook_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def dispatch_mention_webhook(
    project_root: Path | str,
    notifications: list[dict[str, Any]],
) -> dict[str, Any]:
    """POST newly created mention notifications to configured webhook."""
    if not notifications:
        return {"dispatched": 0, "skipped": True}
    config = load_webhook_config(project_root)
    if not config.get("enabled"):
        return {"dispatched": 0, "skipped": True}
    url = str(config.get("url", "")).strip()
    if not url.startswith(("http://", "https://")):
        return {"dispatched": 0, "skipped": True, "error": "invalid webhook url"}
    allowed = set(config.get("mention_handles") or [])
    payload_rows = []
    for row in notifications:
        handle = str(row.get("handle", "")).lower()
        if allowed and handle not in allowed:
            continue
        payload_rows.append(row)
    if not payload_rows:
        return {"dispatched": 0, "skipped": True}
    body = json.dumps(
        {"schema_version": "1", "notifications": payload_rows},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=_WEBHOOK_TIMEOUT_SEC) as response:
            status = getattr(response, "status", 200)
        return {"dispatched": len(payload_rows), "status": status}
    except urllib.error.URLError as exc:
        return {"dispatched": 0, "error": str(exc.reason or exc)}


def dispatch_digest_webhook(
    project_root: Path | str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """POST notification digest summary to configured webhook."""
    config = load_webhook_config(project_root)
    if not config.get("enabled"):
        return {"dispatched": 0, "skipped": True}
    url = str(config.get("url", "")).strip()
    if not url.startswith(("http://", "https://")):
        return {"dispatched": 0, "skipped": True, "error": "invalid webhook url"}
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=_WEBHOOK_TIMEOUT_SEC) as response:
            status = getattr(response, "status", 200)
        return {"dispatched": 1, "status": status}
    except urllib.error.URLError as exc:
        return {"dispatched": 0, "error": str(exc.reason or exc)}
