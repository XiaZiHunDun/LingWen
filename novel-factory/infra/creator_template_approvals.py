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


def _sla_config_path(project_root: Path | str) -> Path:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    return root / ".state" / "creator_template_approval_sla.json"


_MAX_SLA_HOURS = 720


def load_approval_sla_config(project_root: Path | str) -> dict[str, Any]:
    path = _sla_config_path(project_root)
    if not path.is_file():
        return {
            "schema_version": "1",
            "timeout_hours": 72,
            "email_on_submit": True,
            "email_on_reject": True,
            "email_on_overdue": True,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    hours = int(data.get("timeout_hours", 72))
    hours = max(1, min(hours, _MAX_SLA_HOURS))
    return {
        "schema_version": "1",
        "timeout_hours": hours,
        "email_on_submit": bool(data.get("email_on_submit", True)),
        "email_on_reject": bool(data.get("email_on_reject", True)),
        "email_on_overdue": bool(data.get("email_on_overdue", True)),
    }


def save_approval_sla_config(
    project_root: Path | str,
    *,
    timeout_hours: int,
    email_on_submit: bool = True,
    email_on_reject: bool = True,
    email_on_overdue: bool = True,
) -> dict[str, Any]:
    hours = max(1, min(int(timeout_hours), _MAX_SLA_HOURS))
    data = {
        "schema_version": "1",
        "timeout_hours": hours,
        "email_on_submit": bool(email_on_submit),
        "email_on_reject": bool(email_on_reject),
        "email_on_overdue": bool(email_on_overdue),
    }
    path = _sla_config_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def list_overdue_template_approvals(project_root: Path | str) -> list[dict[str, Any]]:
    """List pending approvals exceeding SLA timeout."""
    config = load_approval_sla_config(project_root)
    timeout_hours = float(config["timeout_hours"])
    now = datetime.now(timezone.utc)
    store = _load_store(project_root)
    overdue: list[dict[str, Any]] = []
    assignees = _approval_step_assignees(project_root)
    for row in store.get("approvals") or []:
        if str(row.get("status", "")).lower() != "pending":
            continue
        submitted = _parse_iso(row.get("submitted_at"))
        if submitted is None:
            continue
        hours_pending = (now - submitted).total_seconds() / 3600
        if hours_pending >= timeout_hours:
            public = _public_approval_row(row, step_assignees=assignees)
            public["hours_pending"] = round(hours_pending, 1)
            overdue.append(public)
    return overdue


def notify_overdue_template_approvals(project_root: Path | str) -> dict[str, Any]:
    """Send overdue reminder emails once per pending approval."""
    sla = load_approval_sla_config(project_root)
    if not sla.get("email_on_overdue"):
        return {"notified": 0, "skipped": True}
    config = load_approval_chain_config(project_root)
    assignees = config.get("step_assignees") or []
    timeout_hours = float(sla["timeout_hours"])
    now = datetime.now(timezone.utc)
    store = _load_store(project_root)
    notified = 0
    for row in store.get("approvals") or []:
        if str(row.get("status", "")).lower() != "pending":
            continue
        if row.get("overdue_notified_at"):
            continue
        submitted = _parse_iso(row.get("submitted_at"))
        if submitted is None:
            continue
        if (now - submitted).total_seconds() / 3600 < timeout_hours:
            continue
        public = _public_approval_row(row, step_assignees=assignees)
        try:
            from infra.creator_onboarding_email import dispatch_approval_email

            dispatch_approval_email(project_root, "overdue", public)
        except Exception:
            pass
        row["overdue_notified_at"] = _now_iso()
        notified += 1
    if notified:
        _save_store(project_root, store)
    return {"notified": notified}


def _parse_iso(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None


def load_approval_chain_config(project_root: Path | str) -> dict[str, Any]:
    path = _chain_config_path(project_root)
    if not path.is_file():
        return {"schema_version": "1", "required_steps": 2, "step_assignees": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    steps = int(data.get("required_steps", 2))
    steps = max(1, min(steps, _MAX_CHAIN_STEPS))
    assignees_raw = data.get("step_assignees") or []
    assignees = (
        [str(a).strip() for a in assignees_raw if str(a).strip()][:steps]
        if isinstance(assignees_raw, list)
        else []
    )
    return {"schema_version": "1", "required_steps": steps, "step_assignees": assignees}


def save_approval_chain_config(
    project_root: Path | str,
    *,
    required_steps: int,
    step_assignees: list[str] | None = None,
) -> dict[str, Any]:
    steps = max(1, min(int(required_steps), _MAX_CHAIN_STEPS))
    existing = load_approval_chain_config(project_root) if _chain_config_path(project_root).is_file() else {}
    assignees = existing.get("step_assignees") or []
    if step_assignees is not None:
        assignees = [str(a).strip() for a in step_assignees if str(a).strip()][:steps]
    data = {"schema_version": "1", "required_steps": steps, "step_assignees": assignees}
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
    submit_note: str = "",
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
        "submit_note": str(submit_note).strip()[:240],
        "resolve_note": "",
        "overdue_notified_at": None,
        "chain_step": 1,
        "chain_total": chain_total,
        "chain_log": [],
    }
    approvals.insert(0, entry)
    store["approvals"] = approvals[:_MAX_APPROVALS]
    _save_store(project_root, store)
    _notify_approval_event(project_root, "submitted", entry)
    return _public_approval_row(entry, step_assignees=load_approval_chain_config(project_root).get("step_assignees") or [])


def _public_approval_row(
    row: dict[str, Any],
    *,
    include_chain_log: bool = False,
    step_assignees: list[str] | None = None,
) -> dict[str, Any]:
    chain_step = int(row.get("chain_step") or 1)
    chain_total = int(row.get("chain_total") or 1)
    assignees = step_assignees or []
    current_assignee = assignees[chain_step - 1] if chain_step - 1 < len(assignees) else ""
    public = {
        "id": str(row["id"]),
        "template_id": str(row.get("template_id", "")),
        "scope": str(row.get("scope", "custom")),
        "status": str(row.get("status", "pending")),
        "version_label": row.get("version_label"),
        "previous_label": row.get("previous_label"),
        "submitted_at": row.get("submitted_at"),
        "resolved_at": row.get("resolved_at"),
        "reject_reason": str(row.get("reject_reason", "")),
        "submit_note": str(row.get("submit_note", "")),
        "resolve_note": str(row.get("resolve_note", "")),
        "current_assignee": current_assignee,
        "has_volumes_snapshot": bool(row.get("volumes_snapshot")),
        "chain_step": chain_step,
        "chain_total": chain_total,
        "chain_progress": f"{chain_step}/{chain_total}",
    }
    if include_chain_log:
        public["chain_log"] = list(row.get("chain_log") or [])
    return public


def export_template_approval_audit(project_root: Path | str) -> dict[str, Any]:
    """Export full approval audit trail including chain_log entries."""
    store = _load_store(project_root)
    rows = list(store.get("approvals") or [])
    audit_rows = [
        _public_approval_row(row, include_chain_log=True, step_assignees=_approval_step_assignees(project_root))
        for row in rows
    ]
    return {
        "schema_version": "1",
        "count": len(audit_rows),
        "approvals": audit_rows,
    }


def list_template_approval_history(
    project_root: Path | str,
    *,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """List resolved approvals (approved/rejected) with audit chain_log."""
    store = _load_store(project_root)
    rows = [
        row
        for row in store.get("approvals") or []
        if str(row.get("status", "")).lower() in {"approved", "rejected"}
    ]
    assignees = _approval_step_assignees(project_root)
    return [
        _public_approval_row(row, include_chain_log=True, step_assignees=assignees)
        for row in rows[:limit]
    ]


def _approval_step_assignees(project_root: Path | str) -> list[str]:
    return load_approval_chain_config(project_root).get("step_assignees") or []


def _notify_approval_event(
    project_root: Path | str,
    event: str,
    row: dict[str, Any],
) -> None:
    assignees = _approval_step_assignees(project_root)
    public = _public_approval_row(row, step_assignees=assignees)
    try:
        from infra.creator_onboarding_webhook import dispatch_approval_webhook

        dispatch_approval_webhook(project_root, event, public)
    except Exception:
        pass
    sla = load_approval_sla_config(project_root)
    send_email = (
        (event == "submitted" and sla.get("email_on_submit"))
        or (event == "rejected" and sla.get("email_on_reject"))
    )
    if send_email:
        try:
            from infra.creator_onboarding_email import dispatch_approval_email

            dispatch_approval_email(project_root, event, public)
        except Exception:
            pass


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
    assignees = _approval_step_assignees(project_root)
    return [_public_approval_row(row, step_assignees=assignees) for row in rows]


def approve_template_approval(
    project_root: Path | str,
    approval_id: str,
    *,
    assignee: str = "",
    resolve_note: str = "",
) -> dict[str, Any]:
    store = _load_store(project_root)
    aid = str(approval_id).strip()
    chain_cfg = load_approval_chain_config(project_root)
    assignees = chain_cfg.get("step_assignees") or []
    for row in store.get("approvals") or []:
        if row.get("id") != aid:
            continue
        if row.get("status") != "pending":
            raise ValueError(f"approval is not pending: {approval_id!r}")
        chain_step = int(row.get("chain_step") or 1)
        expected = assignees[chain_step - 1] if chain_step - 1 < len(assignees) else ""
        actor = str(assignee).strip()
        if expected and actor and actor != expected:
            raise ValueError(f"approval step {chain_step} assigned to {expected!r}, not {actor!r}")
        chain_total = int(row.get("chain_total") or 1)
        chain_log: list[dict[str, Any]] = list(row.get("chain_log") or [])
        chain_log.append(
            {
                "step": chain_step,
                "approved_at": _now_iso(),
                "assignee": actor or expected,
                "note": str(resolve_note).strip()[:240],
            },
        )
        row["chain_log"] = chain_log
        if resolve_note:
            row["resolve_note"] = str(resolve_note).strip()[:240]
        if chain_step < chain_total:
            row["chain_step"] = chain_step + 1
            _save_store(project_root, store)
            _notify_approval_event(project_root, "chain_advanced", row)
            public = _public_approval_row(row, step_assignees=assignees)
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
        _notify_approval_event(project_root, "approved", row)
        public = _public_approval_row(row, step_assignees=assignees)
        public["applied"] = result
        public["chain_advanced"] = False
        return public
    raise ValueError(f"unknown approval: {approval_id!r}")


def reject_template_approval(
    project_root: Path | str,
    approval_id: str,
    *,
    reason: str = "",
    resolve_note: str = "",
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
        if resolve_note:
            row["resolve_note"] = str(resolve_note).strip()[:240]
        _save_store(project_root, store)
        _notify_approval_event(project_root, "rejected", row)
        assignees = load_approval_chain_config(project_root).get("step_assignees") or []
        return _public_approval_row(row, step_assignees=assignees)
    raise ValueError(f"unknown approval: {approval_id!r}")
