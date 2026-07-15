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
    chain_cfg = _approval_chain_config(project_root)
    for row in store.get("approvals") or []:
        if str(row.get("status", "")).lower() != "pending":
            continue
        submitted = _parse_iso(row.get("submitted_at"))
        if submitted is None:
            continue
        hours_pending = (now - submitted).total_seconds() / 3600
        if hours_pending >= timeout_hours:
            public = _public_approval_row(row, chain_cfg=chain_cfg)
            public["hours_pending"] = round(hours_pending, 1)
            overdue.append(public)
    return overdue


def notify_overdue_template_approvals(project_root: Path | str) -> dict[str, Any]:
    """Send overdue reminder emails once per pending approval."""
    sla = load_approval_sla_config(project_root)
    if not sla.get("email_on_overdue"):
        return {"notified": 0, "skipped": True}
    chain_cfg = load_approval_chain_config(project_root)
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
        public = _public_approval_row(row, chain_cfg=chain_cfg)
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
        return {"schema_version": "1", "required_steps": 2, "step_assignees": [], "step_assignee_groups": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    steps = int(data.get("required_steps", 2))
    steps = max(1, min(steps, _MAX_CHAIN_STEPS))
    assignees_raw = data.get("step_assignees") or []
    assignees = (
        [str(a).strip() for a in assignees_raw if str(a).strip()][:steps]
        if isinstance(assignees_raw, list)
        else []
    )
    groups = _normalize_assignee_groups(data.get("step_assignee_groups"), steps)
    if not groups and assignees:
        groups = [[name] for name in assignees]
    if groups and not assignees:
        assignees = [group[0] for group in groups if group]
    return {
        "schema_version": "1",
        "required_steps": steps,
        "step_assignees": assignees,
        "step_assignee_groups": groups,
    }


def _normalize_assignee_groups(raw: Any, steps: int) -> list[list[str]]:
    if not isinstance(raw, list):
        return []
    groups: list[list[str]] = []
    for item in raw[:steps]:
        if isinstance(item, list):
            group = [str(a).strip() for a in item if str(a).strip()]
            if group:
                groups.append(group)
        elif isinstance(item, str) and item.strip():
            groups.append([item.strip()])
    return groups


def _step_assignee_groups(chain_cfg: dict[str, Any]) -> list[list[str]]:
    groups = chain_cfg.get("step_assignee_groups") or []
    if groups:
        return groups
    assignees = chain_cfg.get("step_assignees") or []
    return [[name] for name in assignees]


def _current_step_assignees(
    chain_cfg: dict[str, Any],
    row: dict[str, Any],
    chain_step: int,
) -> list[str]:
    overrides = row.get("assignee_overrides") or {}
    override = str(overrides.get(str(chain_step), "")).strip()
    if override:
        return [override]
    groups = _step_assignee_groups(chain_cfg)
    idx = chain_step - 1
    if idx < len(groups):
        return list(groups[idx])
    return []


def save_approval_chain_config(
    project_root: Path | str,
    *,
    required_steps: int,
    step_assignees: list[str] | None = None,
    step_assignee_groups: list[list[str]] | None = None,
) -> dict[str, Any]:
    steps = max(1, min(int(required_steps), _MAX_CHAIN_STEPS))
    existing = load_approval_chain_config(project_root) if _chain_config_path(project_root).is_file() else {}
    groups = existing.get("step_assignee_groups") or []
    assignees = existing.get("step_assignees") or []
    if step_assignee_groups is not None and step_assignee_groups:
        groups = _normalize_assignee_groups(step_assignee_groups, steps)
        assignees = [group[0] for group in groups if group]
    elif step_assignees is not None:
        assignees = [str(a).strip() for a in step_assignees if str(a).strip()][:steps]
        groups = [[name] for name in assignees]
    data = {
        "schema_version": "1",
        "required_steps": steps,
        "step_assignees": assignees,
        "step_assignee_groups": groups,
    }
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
    return _public_approval_row(entry, chain_cfg=load_approval_chain_config(project_root))


def _public_approval_row(
    row: dict[str, Any],
    *,
    include_chain_log: bool = False,
    chain_cfg: dict[str, Any] | None = None,
    step_assignees: list[str] | None = None,
) -> dict[str, Any]:
    chain_step = int(row.get("chain_step") or 1)
    chain_total = int(row.get("chain_total") or 1)
    cfg = chain_cfg or {"step_assignees": step_assignees or [], "step_assignee_groups": []}
    current_assignees = _current_step_assignees(cfg, row, chain_step)
    current_assignee = current_assignees[0] if len(current_assignees) == 1 else ""
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
        "current_assignees": current_assignees,
        "or_signing": len(current_assignees) > 1,
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
        _public_approval_row(row, include_chain_log=True, chain_cfg=_approval_chain_config(project_root))
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
    chain_cfg = _approval_chain_config(project_root)
    return [
        _public_approval_row(row, include_chain_log=True, chain_cfg=chain_cfg)
        for row in rows[:limit]
    ]


def _approval_chain_config(project_root: Path | str) -> dict[str, Any]:
    return load_approval_chain_config(project_root)


def _notify_approval_event(
    project_root: Path | str,
    event: str,
    row: dict[str, Any],
) -> None:
    chain_cfg = _approval_chain_config(project_root)
    public = _public_approval_row(row, chain_cfg=chain_cfg)
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
    chain_cfg = _approval_chain_config(project_root)
    return [_public_approval_row(row, chain_cfg=chain_cfg) for row in rows]


def approve_template_approval(
    project_root: Path | str,
    approval_id: str,
    *,
    assignee: str = "",
    resolve_note: str = "",
    force: bool = False,
) -> dict[str, Any]:
    drift = check_approval_snapshot_drift(project_root, approval_id)
    if drift.get("drifted") and not force:
        raise ValueError(
            "approval volumes snapshot drifted from current template; "
            "re-submit approval or pass force=true",
        )
    store = _load_store(project_root)
    aid = str(approval_id).strip()
    chain_cfg = load_approval_chain_config(project_root)
    for row in store.get("approvals") or []:
        if row.get("id") != aid:
            continue
        if row.get("status") != "pending":
            raise ValueError(f"approval is not pending: {approval_id!r}")
        chain_step = int(row.get("chain_step") or 1)
        allowed = _current_step_assignees(chain_cfg, row, chain_step)
        actor = str(assignee).strip()
        if allowed and actor and actor not in allowed:
            raise ValueError(
                f"approval step {chain_step} assigned to {allowed!r}, not {actor!r}",
            )
        expected = allowed[0] if len(allowed) == 1 else ""
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
            public = _public_approval_row(row, chain_cfg=chain_cfg)
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
        public = _public_approval_row(row, chain_cfg=chain_cfg)
        public["applied"] = result
        public["chain_advanced"] = False
        return public
    raise ValueError(f"unknown approval: {approval_id!r}")


def check_approval_snapshot_drift(
    project_root: Path | str,
    approval_id: str,
) -> dict[str, Any]:
    """Return whether approval snapshot differs from current template volumes."""
    diff = preview_template_approval_snapshot_diff(project_root, approval_id)
    summary = diff.get("diff_summary") or {}
    return {
        "approval_id": diff["approval_id"],
        "template_id": diff["template_id"],
        "drifted": bool(summary.get("changed")),
        "diff_summary": summary,
    }


def batch_approve_template_approvals(
    project_root: Path | str,
    approval_ids: list[str],
    *,
    assignee: str = "",
    resolve_note: str = "",
    force: bool = False,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for aid in approval_ids:
        try:
            row = approve_template_approval(
                project_root,
                aid,
                assignee=assignee,
                resolve_note=resolve_note,
                force=force,
            )
            results.append({"id": aid, "ok": True, "status": row.get("status"), "chain_advanced": row.get("chain_advanced")})
        except ValueError as exc:
            results.append({"id": aid, "ok": False, "error": str(exc)})
    approved = sum(1 for row in results if row.get("ok"))
    return {"approved": approved, "total": len(approval_ids), "results": results}


def batch_reject_template_approvals(
    project_root: Path | str,
    approval_ids: list[str],
    *,
    reason: str = "",
    resolve_note: str = "",
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for aid in approval_ids:
        try:
            row = reject_template_approval(
                project_root,
                aid,
                reason=reason,
                resolve_note=resolve_note,
            )
            results.append({"id": aid, "ok": True, "status": row.get("status")})
        except ValueError as exc:
            results.append({"id": aid, "ok": False, "error": str(exc)})
    rejected = sum(1 for row in results if row.get("ok"))
    return {"rejected": rejected, "total": len(approval_ids), "results": results}


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
        chain_cfg = load_approval_chain_config(project_root)
        return _public_approval_row(row, chain_cfg=chain_cfg)
    raise ValueError(f"unknown approval: {approval_id!r}")


def transfer_template_approval(
    project_root: Path | str,
    approval_id: str,
    *,
    to_assignee: str,
    note: str = "",
) -> dict[str, Any]:
    """Delegate current approval step to another assignee."""
    store = _load_store(project_root)
    aid = str(approval_id).strip()
    target = str(to_assignee).strip()
    if not target:
        raise ValueError("to_assignee required")
    chain_cfg = load_approval_chain_config(project_root)
    for row in store.get("approvals") or []:
        if row.get("id") != aid:
            continue
        if row.get("status") != "pending":
            raise ValueError(f"approval is not pending: {approval_id!r}")
        chain_step = int(row.get("chain_step") or 1)
        previous = _current_step_assignees(chain_cfg, row, chain_step)
        overrides = dict(row.get("assignee_overrides") or {})
        overrides[str(chain_step)] = target
        row["assignee_overrides"] = overrides
        chain_log: list[dict[str, Any]] = list(row.get("chain_log") or [])
        chain_log.append(
            {
                "step": chain_step,
                "action": "transfer",
                "transferred_at": _now_iso(),
                "from_assignees": previous,
                "to_assignee": target,
                "note": str(note).strip()[:240],
            },
        )
        row["chain_log"] = chain_log
        _save_store(project_root, store)
        _notify_approval_event(project_root, "transferred", row)
        return _public_approval_row(row, chain_cfg=chain_cfg)
    raise ValueError(f"unknown approval: {approval_id!r}")


def preview_template_approval_snapshot_diff(
    project_root: Path | str,
    approval_id: str,
) -> dict[str, Any]:
    """Compare approval volumes snapshot against current template state."""
    from infra.creator_settings_docs import text_diff_summary
    from infra.creator_volume_templates import _build_visual_diff_lines, _volumes_repr

    store = _load_store(project_root)
    aid = str(approval_id).strip()
    for row in store.get("approvals") or []:
        if row.get("id") != aid:
            continue
        tid = str(row.get("template_id", ""))
        _, item = _find_template_item(project_root, tid)
        snapshot = row.get("volumes_snapshot") or []
        current = _snapshot_volumes(item.get("volumes"))
        before = _volumes_repr(snapshot)
        after = _volumes_repr(current)
        diff = text_diff_summary(before, after)
        return {
            "approval_id": aid,
            "template_id": tid,
            "has_volumes_snapshot": bool(snapshot),
            "diff_summary": {
                "changed": diff["changed"],
                "lines_added": diff["lines_added"],
                "lines_removed": diff["lines_removed"],
                "snippet": diff["snippet"][:5],
            },
            "visual_diff": {
                "before": before,
                "after": after,
                "lines": _build_visual_diff_lines(before, after),
            },
        }
    raise ValueError(f"unknown approval: {approval_id!r}")
