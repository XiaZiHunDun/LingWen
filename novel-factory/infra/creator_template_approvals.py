"""Pending approval workflow for creator volume template version changes."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infra.creator_volume_templates import (
    _load_custom_store,
    _normalize_version_label,
    _save_custom_store,
    _snapshot_volumes,
    set_custom_template_version_label,
    set_factory_template_version_label,
)

_STATE_VERSION = "2"
_MAX_APPROVALS = 50
_MAX_CHAIN_STEPS = 5
_CUSTOM_PREFIX = "custom_"
_FACTORY_PREFIX = "factory_"


def _chain_config_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_template_approval_chain.json"


def load_approval_chain_config(project_root: Path | str) -> dict[str, Any]:
    path = _chain_config_path(project_root)
    if not path.is_file():
        return {"schema_version": "1", "required_steps": 2}
    data = json.loads(path.read_text(encoding="utf-8"))
    steps = int(data.get("required_steps", 2))
    steps = max(1, min(steps, _MAX_CHAIN_STEPS))
    return {"schema_version": "1", "required_steps": steps}


def save_approval_chain_config(project_root: Path | str, *, required_steps: int) -> dict[str, Any]:
    steps = max(1, min(int(required_steps), _MAX_CHAIN_STEPS))
    data = {"schema_version": "1", "required_steps": steps}
    path = _chain_config_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def _approvals_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_template_approvals.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_store(project_root: Path | str) -> dict[str, Any]:
    path = _approvals_path(project_root)
    if not path.is_file():
        return {"schema_version": _STATE_VERSION, "approvals": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_store(project_root: Path | str, data: dict[str, Any]) -> None:
    path = _approvals_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _find_template_item(
    project_root: Path | str,
    template_id: str,
) -> tuple[str, dict[str, Any]]:
    tid = template_id.strip().lower()
    if tid.startswith(_CUSTOM_PREFIX):
        store = _load_custom_store(project_root)
        for item in store.get("templates", []):
            if item.get("id") == tid:
                return "custom", item
        raise ValueError(f"unknown template: {template_id!r}")
    if tid.startswith(_FACTORY_PREFIX):
        from infra.creator_volume_templates import _load_factory_store

        factory = _load_factory_store()
        for item in factory.get("templates", []):
            if item.get("id") == tid:
                return "factory", item
        raise ValueError(f"unknown factory template: {template_id!r}")
    raise ValueError(f"unknown template: {template_id!r}")


def submit_template_version_approval(
    project_root: Path | str,
    template_id: str,
    *,
    version_label: str | None,
) -> dict[str, Any]:
    """Queue a template version label change for approval."""
    tid = template_id.strip().lower()
    scope, item = _find_template_item(project_root, tid)
    proposed = (
        _normalize_version_label(version_label, strict=True)
        if version_label and str(version_label).strip()
        else None
    )
    current = _normalize_version_label(item.get("version_label"))
    if proposed == current:
        raise ValueError("proposed version label matches current version")
    store = _load_store(project_root)
    approvals: list[dict[str, Any]] = list(store.get("approvals") or [])
    for row in approvals:
        if row.get("template_id") == tid and row.get("status") == "pending":
            raise ValueError("template already has a pending approval")
    chain_total = load_approval_chain_config(project_root)["required_steps"]
    entry = {
        "id": f"aprv_{uuid.uuid4().hex[:10]}",
        "template_id": tid,
        "scope": scope,
        "status": "pending",
        "version_label": proposed,
        "previous_label": current,
        "volumes_snapshot": _snapshot_volumes(item.get("volumes")),
        "submitted_at": _now_iso(),
        "resolved_at": None,
        "reject_reason": "",
        "chain_step": 1,
        "chain_total": chain_total,
        "chain_log": [],
    }
    approvals.insert(0, entry)
    store["approvals"] = approvals[:_MAX_APPROVALS]
    _save_store(project_root, store)
    return _public_approval_row(entry)


def _public_approval_row(row: dict[str, Any]) -> dict[str, Any]:
    chain_step = int(row.get("chain_step") or 1)
    chain_total = int(row.get("chain_total") or 1)
    return {
        "id": str(row["id"]),
        "template_id": str(row.get("template_id", "")),
        "scope": str(row.get("scope", "custom")),
        "status": str(row.get("status", "pending")),
        "version_label": row.get("version_label"),
        "previous_label": row.get("previous_label"),
        "submitted_at": row.get("submitted_at"),
        "resolved_at": row.get("resolved_at"),
        "reject_reason": str(row.get("reject_reason", "")),
        "has_volumes_snapshot": bool(row.get("volumes_snapshot")),
        "chain_step": chain_step,
        "chain_total": chain_total,
        "chain_progress": f"{chain_step}/{chain_total}",
    }


def list_template_approvals(
    project_root: Path | str,
    *,
    status: str | None = None,
    template_id: str | None = None,
) -> list[dict[str, Any]]:
    store = _load_store(project_root)
    rows = list(store.get("approvals") or [])
    status_norm = str(status).strip().lower() if status else None
    tid = template_id.strip().lower() if template_id else None
    if status_norm:
        rows = [row for row in rows if str(row.get("status", "")).lower() == status_norm]
    if tid:
        rows = [row for row in rows if str(row.get("template_id", "")).lower() == tid]
    return [_public_approval_row(row) for row in rows]


def approve_template_approval(project_root: Path | str, approval_id: str) -> dict[str, Any]:
    store = _load_store(project_root)
    aid = str(approval_id).strip()
    for row in store.get("approvals") or []:
        if row.get("id") != aid:
            continue
        if row.get("status") != "pending":
            raise ValueError(f"approval is not pending: {approval_id!r}")
        chain_step = int(row.get("chain_step") or 1)
        chain_total = int(row.get("chain_total") or 1)
        chain_log: list[dict[str, Any]] = list(row.get("chain_log") or [])
        chain_log.append({"step": chain_step, "approved_at": _now_iso()})
        row["chain_log"] = chain_log
        if chain_step < chain_total:
            row["chain_step"] = chain_step + 1
            _save_store(project_root, store)
            public = _public_approval_row(row)
            public["chain_advanced"] = True
            return public
        tid = str(row.get("template_id", ""))
        proposed = row.get("version_label")
        if row.get("scope") == "factory":
            result = set_factory_template_version_label(tid, version_label=proposed)
        else:
            result = set_custom_template_version_label(
                project_root,
                tid,
                version_label=proposed,
            )
        row["status"] = "approved"
        row["resolved_at"] = _now_iso()
        _save_store(project_root, store)
        public = _public_approval_row(row)
        public["applied"] = result
        public["chain_advanced"] = False
        return public
    raise ValueError(f"unknown approval: {approval_id!r}")


def reject_template_approval(
    project_root: Path | str,
    approval_id: str,
    *,
    reason: str = "",
) -> dict[str, Any]:
    store = _load_store(project_root)
    aid = str(approval_id).strip()
    for row in store.get("approvals") or []:
        if row.get("id") != aid:
            continue
        if row.get("status") != "pending":
            raise ValueError(f"approval is not pending: {approval_id!r}")
        row["status"] = "rejected"
        row["resolved_at"] = _now_iso()
        row["reject_reason"] = str(reason).strip()[:240]
        _save_store(project_root, store)
        return _public_approval_row(row)
    raise ValueError(f"unknown approval: {approval_id!r}")
