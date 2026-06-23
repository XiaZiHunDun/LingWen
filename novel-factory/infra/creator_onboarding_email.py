"""Email dispatch for creator onboarding @mention notifications."""
from __future__ import annotations

import json
import re
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Any

_STATE_VERSION = "1"
_MAX_ADDRESS = 128
_MAX_ADDRESSES = 5
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_SMTP_TIMEOUT_SEC = 8


def _email_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_onboarding_email.json"


def _normalize_addresses(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    seen: list[str] = []
    for item in raw:
        addr = str(item).strip()[:_MAX_ADDRESS]
        if addr and _EMAIL_RE.match(addr) and addr not in seen:
            seen.append(addr)
        if len(seen) >= _MAX_ADDRESSES:
            break
    return seen


def load_email_config(project_root: Path | str) -> dict[str, Any]:
    path = _email_path(project_root)
    if not path.is_file():
        return {
            "schema_version": _STATE_VERSION,
            "enabled": False,
            "to_addresses": [],
            "mention_handles": [],
            "smtp_host": "",
            "smtp_port": 587,
            "smtp_user": "",
            "smtp_use_tls": True,
            "from_address": "",
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    handles = data.get("mention_handles") or []
    if not isinstance(handles, list):
        handles = []
    port = data.get("smtp_port", 587)
    try:
        port = int(port)
    except (TypeError, ValueError):
        port = 587
    return {
        "schema_version": _STATE_VERSION,
        "enabled": bool(data.get("enabled")),
        "to_addresses": _normalize_addresses(data.get("to_addresses")),
        "mention_handles": [str(h).strip().lower() for h in handles if str(h).strip()],
        "smtp_host": str(data.get("smtp_host", "")).strip()[:_MAX_ADDRESS],
        "smtp_port": port,
        "smtp_user": str(data.get("smtp_user", "")).strip()[:_MAX_ADDRESS],
        "smtp_use_tls": bool(data.get("smtp_use_tls", True)),
        "from_address": str(data.get("from_address", "")).strip()[:_MAX_ADDRESS],
    }


def save_email_config(
    project_root: Path | str,
    *,
    enabled: bool = True,
    to_addresses: list[str] | None = None,
    mention_handles: list[str] | None = None,
    smtp_host: str = "",
    smtp_port: int = 587,
    smtp_user: str = "",
    smtp_password: str | None = None,
    smtp_use_tls: bool = True,
    from_address: str = "",
) -> dict[str, Any]:
    addresses = _normalize_addresses(to_addresses or [])
    if enabled and not addresses:
        raise ValueError("at least one recipient email required when enabled")
    host = str(smtp_host).strip()[:_MAX_ADDRESS]
    if enabled and not host:
        raise ValueError("smtp host required when email notifications are enabled")
    sender = str(from_address).strip()[:_MAX_ADDRESS] or (addresses[0] if addresses else "")
    if enabled and not _EMAIL_RE.match(sender):
        raise ValueError("valid from_address required when email notifications are enabled")
    handles: list[str] = []
    if mention_handles is not None:
        handles = list(
            dict.fromkeys(str(h).strip().lower() for h in mention_handles if str(h).strip()),
        )
    path = _email_path(project_root)
    existing: dict[str, Any] = {}
    if path.is_file():
        existing = json.loads(path.read_text(encoding="utf-8"))
    data = {
        "schema_version": _STATE_VERSION,
        "enabled": bool(enabled),
        "to_addresses": addresses,
        "mention_handles": handles,
        "smtp_host": host,
        "smtp_port": int(smtp_port),
        "smtp_user": str(smtp_user).strip()[:_MAX_ADDRESS],
        "smtp_use_tls": bool(smtp_use_tls),
        "from_address": sender,
    }
    if smtp_password is not None:
        data["smtp_password"] = str(smtp_password)
    elif existing.get("smtp_password"):
        data["smtp_password"] = existing["smtp_password"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    public = load_email_config(project_root)
    return public


def _build_email_body(notifications: list[dict[str, Any]]) -> str:
    lines = ["灵文创作向导 @提及通知", ""]
    for row in notifications:
        handle = row.get("handle", "")
        step_id = row.get("step_id", "")
        excerpt = row.get("note_excerpt", "")
        lines.append(f"- @{handle} · 步骤 {step_id}: {excerpt}")
    return "\n".join(lines)


def dispatch_mention_email(
    project_root: Path | str,
    notifications: list[dict[str, Any]],
) -> dict[str, Any]:
    """Send newly created mention notifications via SMTP."""
    if not notifications:
        return {"sent": 0, "skipped": True}
    path = _email_path(project_root)
    if not path.is_file():
        return {"sent": 0, "skipped": True}
    stored = json.loads(path.read_text(encoding="utf-8"))
    config = load_email_config(project_root)
    if not config.get("enabled"):
        return {"sent": 0, "skipped": True}
    recipients = config.get("to_addresses") or []
    host = str(config.get("smtp_host", "")).strip()
    if not recipients or not host:
        return {"sent": 0, "skipped": True, "error": "email not fully configured"}
    allowed = set(config.get("mention_handles") or [])
    payload_rows = []
    for row in notifications:
        handle = str(row.get("handle", "")).lower()
        if allowed and handle not in allowed:
            continue
        payload_rows.append(row)
    if not payload_rows:
        return {"sent": 0, "skipped": True}
    message = EmailMessage()
    message["Subject"] = "灵文创作向导 @提及通知"
    message["From"] = config.get("from_address") or recipients[0]
    message["To"] = ", ".join(recipients)
    message.set_content(_build_email_body(payload_rows))
    try:
        with smtplib.SMTP(host, int(config.get("smtp_port", 587)), timeout=_SMTP_TIMEOUT_SEC) as smtp:
            if config.get("smtp_use_tls", True):
                smtp.starttls()
            user = str(config.get("smtp_user", "")).strip()
            password = str(stored.get("smtp_password", "")).strip()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(message)
        return {"sent": len(payload_rows)}
    except smtplib.SMTPException as exc:
        return {"sent": 0, "error": str(exc)}
