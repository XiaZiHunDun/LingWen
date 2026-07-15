"""Encode/decode volume-plan diff share tokens (v1–v3)."""
from __future__ import annotations

import base64
import json
from typing import Any


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(token: str) -> bytes:
    padded = token.replace("-", "+").replace("_", "/")
    pad = "=" * ((4 - len(padded) % 4) % 4)
    return base64.b64decode(padded + pad)


def encode_share_token(
    *,
    changes: list[dict[str, Any]],
    change_count: int | None = None,
    global_outline_path: str = "",
    draft_volumes: list[dict[str, Any]] | None = None,
    collab_notes: dict[str, str] | None = None,
) -> str:
    version = 1
    if draft_volumes:
        version = 2
    if collab_notes:
        version = 3
    payload: dict[str, Any] = {
        "v": version,
        "c": change_count if change_count is not None else len(changes),
        "changes": changes,
        "p": global_outline_path or "",
    }
    if draft_volumes:
        payload["d"] = draft_volumes
    if collab_notes:
        payload["n"] = {
            str(label).strip(): str(note).strip()[:500]
            for label, note in collab_notes.items()
            if str(label).strip() and str(note).strip()
        }
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return _b64url_encode(raw.encode("utf-8"))


def decode_share_token(token: str) -> dict[str, Any]:
    try:
        data = json.loads(_b64url_decode(str(token or "")).decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return {
            "valid": False,
            "error": "corrupt_token",
            "error_label": "分享链接已损坏或无法解析",
        }

    version = data.get("v")
    if not isinstance(version, int) or version < 1 or version > 3:
        label = f"v{version}" if version is not None else "未知"
        return {
            "valid": False,
            "error": "unsupported_version",
            "error_label": f"不支持的分享版本 {label}",
        }
    if not isinstance(data.get("changes"), list):
        return {
            "valid": False,
            "error": "invalid_payload",
            "error_label": "分享数据缺少变更列表",
        }

    draft_volumes = None
    if isinstance(data.get("d"), list):
        draft_volumes = [
            {
                "label": row.get("label"),
                "start_chapter": int(row.get("start_chapter") or 1),
                "end_chapter": int(row.get("end_chapter") or 1),
                "core_conflict": row.get("core_conflict") or "",
                "locked": bool(row.get("locked")),
            }
            for row in data["d"]
            if isinstance(row, dict)
        ]

    collab_notes = {}
    if isinstance(data.get("n"), dict):
        collab_notes = {
            str(label).strip(): str(note).strip()[:500]
            for label, note in data["n"].items()
            if str(label).strip() and str(note).strip()
        }

    return {
        "valid": True,
        "version": version,
        "change_count": data.get("c", len(data["changes"])),
        "changes": data["changes"],
        "global_outline_path": data.get("p") or "",
        "draft_volumes": draft_volumes,
        "collab_notes": collab_notes,
        "can_apply": bool(draft_volumes),
        "has_collab_notes": bool(collab_notes),
    }
