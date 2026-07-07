"""Phase 9.65 F56: idempotent fixtures for Playwright live-backend e2e."""
from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from infra.agent_system.decision_queue import (
    DecisionKind,
    DecisionStatus,
    HumanDecision,
    HumanDecisionQueue,
    create_decision,
)
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage

E2E_PENDING_RIPPLE_ID = "rip-pending-1"
E2E_REJECTED_RIPPLE_ID = "rip-rejected-1"
E2E_DECISION_ID = "e2e-dec1"
E2E_CREATOR_SLUG = "e2e-live-creator"
E2E_COMPANION_SLUG = "e2e-live-companion"
E2E_STUDIO_SLUG = "e2e-live-studio"

_DEFAULT_STATE_DIR = Path(__file__).resolve().parents[2] / "infra" / ".state"


def _cvg_db_path(state_dir: Path | None = None) -> Path:
    _ = state_dir  # reserved for future override
    return Path(__file__).resolve().parents[2] / ".state" / "cross_volume.db"


def _state_dir(state_dir: Path | None = None) -> Path:
    return state_dir or _DEFAULT_STATE_DIR


def _make_pending_ripple(ripple_id: str, chapter: int, status: str) -> CrossVolumeRipple:
    return CrossVolumeRipple(
        id=ripple_id,
        trigger_volume=1,
        trigger_chapter=chapter,
        affected_nodes=(),
        affected_edges=(),
        proposed_actions=(),
        status=status,
        payload={"confidence": 4, "evidence": "e2e seed"},
    )


def ensure_e2e_ripples(db_path: Path | None = None) -> None:
    path = db_path or _cvg_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    storage = RippleStorage(db_path=path, graph=None)
    for ripple_id, chapter, status in (
        (E2E_PENDING_RIPPLE_ID, 2, "pending"),
        (E2E_REJECTED_RIPPLE_ID, 3, "rejected"),
    ):
        if storage.get_ripple_by_id(ripple_id) is None:
            storage.append_ripple(_make_pending_ripple(ripple_id, chapter, status))


def reset_e2e_ripple(ripple_id: str, to_status: str, db_path: Path | None = None) -> None:
    path = db_path or _cvg_db_path()
    storage = RippleStorage(db_path=path, graph=None)
    ensure_e2e_ripples(path)
    storage.reset_ripple_for_test(
        ripple_id=ripple_id,
        to_status=to_status,
        actor="e2e-seed",
        origin="system",
        reason=f"reset to {to_status}",
    )


def _make_e2e_decision() -> HumanDecision:
    base = create_decision(
        decision_kind=DecisionKind.OUTLINE_JUDGMENT,
        node_id="e2e-node",
        prompt="E2E: approve outline?",
        options=("approve", "reject"),
        priority=9,
    )
    return replace(
        base,
        decision_id=E2E_DECISION_ID,
        status=DecisionStatus.PENDING,
        resolution=None,
        resolved_by=None,
        resolved_at=None,
        reason=None,
    )


def ensure_e2e_decision(state_dir: Path | None = None) -> None:
    directory = _state_dir(state_dir)
    directory.mkdir(parents=True, exist_ok=True)
    queue = HumanDecisionQueue(state_dir=str(directory))
    with queue.with_lock():
        if E2E_DECISION_ID not in queue._decisions:
            queue.add(_make_e2e_decision())


def reset_e2e_decision(state_dir: Path | None = None) -> None:
    directory = _state_dir(state_dir)
    queue = HumanDecisionQueue(state_dir=str(directory))
    with queue.with_lock():
        if E2E_DECISION_ID in queue._decisions:
            del queue._decisions[E2E_DECISION_ID]
        queue.add(_make_e2e_decision())


def clear_inbox_pending(
    db_path: Path | None = None,
    state_dir: Path | None = None,
) -> None:
    """No pending ripples/decisions — for Today hub / companion-only smoke."""
    from infra.agent_system.decision_queue import DecisionStatus

    reset_e2e_ripple(E2E_PENDING_RIPPLE_ID, "applied", db_path)
    directory = _state_dir(state_dir)
    queue = HumanDecisionQueue(state_dir=str(directory))
    with queue.with_lock():
        if E2E_DECISION_ID in queue._decisions:
            dec = queue._decisions[E2E_DECISION_ID]
            if dec.status == DecisionStatus.PENDING:
                queue.resolve(E2E_DECISION_ID, "approve", resolved_by="e2e-seed")


def restore_inbox_fixture(db_path: Path | None = None, state_dir: Path | None = None) -> None:
    """Ensure pending ripple + decision for inbox/ripples live e2e."""
    ensure_e2e_ripples(db_path)
    ensure_e2e_decision(state_dir)
    reset_e2e_ripple(E2E_PENDING_RIPPLE_ID, "pending", db_path)
    reset_e2e_decision(state_dir)


_E2E_CREATOR_DISPLAY_NAME = "E2E 推进创作"
_E2E_COMPANION_DISPLAY_NAME = "E2E 陪伴创作"
_E2E_STUDIO_DISPLAY_NAME = "E2E 工厂模式"
_E2E_COMPANION_MAX_CHAPTER = 5


def _repair_e2e_creator_project_yaml(root: Path) -> None:
    """Keep advance fixture out of companion-branded UI (name must not contain 创作伴侣)."""
    import yaml

    cfg_path = root / "config" / "project.yaml"
    if not cfg_path.is_file():
        return
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    project = dict(data.get("project") or {})
    changed = False
    if project.get("name") != _E2E_CREATOR_DISPLAY_NAME:
        project["name"] = _E2E_CREATOR_DISPLAY_NAME
        changed = True
    if project.get("creation_mode") != "advance":
        project["creation_mode"] = "advance"
        changed = True
    if not changed:
        return
    data["project"] = project
    cfg_path.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def _repair_e2e_studio_project_yaml(root: Path) -> None:
    import yaml

    cfg_path = root / "config" / "project.yaml"
    if not cfg_path.is_file():
        return
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    project = dict(data.get("project") or {})
    changed = False
    if project.get("name") != _E2E_STUDIO_DISPLAY_NAME:
        project["name"] = _E2E_STUDIO_DISPLAY_NAME
        changed = True
    if project.get("creation_mode") != "studio":
        project["creation_mode"] = "studio"
        changed = True
    if not changed:
        return
    data["project"] = project
    cfg_path.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def _repair_e2e_companion_project_yaml(root: Path) -> None:
    """Keep companion fixture aligned with Today / chapter-preview live e2e."""
    import yaml

    cfg_path = root / "config" / "project.yaml"
    if not cfg_path.is_file():
        return
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    project = dict(data.get("project") or {})
    changed = False
    if project.get("name") != _E2E_COMPANION_DISPLAY_NAME:
        project["name"] = _E2E_COMPANION_DISPLAY_NAME
        changed = True
    if project.get("creation_mode") != "companion":
        project["creation_mode"] = "companion"
        changed = True
    if project.get("max_chapter") != _E2E_COMPANION_MAX_CHAPTER:
        project["max_chapter"] = _E2E_COMPANION_MAX_CHAPTER
        changed = True
    if not changed:
        return
    data["project"] = project
    cfg_path.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def ensure_e2e_cascade_run(db_path: Path | None = None) -> int:
    """Idempotent completed cascade run for rip-pending-1 (replay live e2e)."""
    from infra.cross_volume.reference_graph import CascadedRipple

    path = db_path or _cvg_db_path()
    ensure_e2e_ripples(path)
    storage = RippleStorage(db_path=path, graph=None)
    for run in storage.get_cascade_runs(E2E_PENDING_RIPPLE_ID, limit=10):
        if run.status == "completed":
            return run.id
    cascaded = CascadedRipple(
        trigger_ripple_id=E2E_PENDING_RIPPLE_ID,
        cascade_nodes=(),
        cascade_edges=(),
        cascade_actions=({"kind": "e2e", "label": "seed"},),
        depth_reached=1,
        generated_at=datetime.now(timezone.utc).isoformat(),
        bfs_algorithm_version="e2e",
    )
    return storage.record_cascade_run(
        E2E_PENDING_RIPPLE_ID,
        cascaded,
        max_depth=2,
        status="completed",
    )


def ensure_e2e_studio_project() -> Path:
    """Studio-mode project for factory produce-hub live e2e."""
    from infra.project_init import init_minimal_short_project
    from infra.studio_registry import factory_root, get_project_by_slug

    factory = factory_root()
    existing = get_project_by_slug(E2E_STUDIO_SLUG)
    if existing is None:
        init_minimal_short_project(
            slug=E2E_STUDIO_SLUG,
            title=_E2E_STUDIO_DISPLAY_NAME,
            factory_root=factory,
            creation_mode="studio",
            chapter_count=10,
        )
    project = get_project_by_slug(E2E_STUDIO_SLUG)
    assert project is not None
    _repair_e2e_studio_project_yaml(project.root)
    return project.root


def ensure_e2e_creator_project() -> Path:
    """Advance-mode project for creator share-link live e2e."""
    from infra.project_init import init_minimal_short_project
    from infra.studio_registry import activate_project, factory_root, get_project_by_slug

    factory = factory_root()
    existing = get_project_by_slug(E2E_CREATOR_SLUG)
    if existing is None:
        init_minimal_short_project(
            slug=E2E_CREATOR_SLUG,
            title=_E2E_CREATOR_DISPLAY_NAME,
            factory_root=factory,
            creation_mode="advance",
            chapter_count=12,
        )
    activate_project(E2E_CREATOR_SLUG)
    project = get_project_by_slug(E2E_CREATOR_SLUG)
    assert project is not None
    _repair_e2e_creator_project_yaml(project.root)
    return project.root


def ensure_e2e_companion_project() -> Path:
    """Companion-mode project for creator workspace live e2e."""
    import json

    from infra.project_init import init_minimal_short_project
    from infra.studio_registry import factory_root, get_project_by_slug

    factory = factory_root()
    existing = get_project_by_slug(E2E_COMPANION_SLUG)
    if existing is None:
        result = init_minimal_short_project(
            slug=E2E_COMPANION_SLUG,
            title="E2E 陪伴创作",
            factory_root=factory,
            creation_mode="companion",
            chapter_count=5,
        )
        root = result.root
    else:
        root = existing.root

    body_dir = root / "03_内容仓库/04_正文"
    body_dir.mkdir(parents=True, exist_ok=True)
    (body_dir / "ch001.md").write_text(
        "# 第一章\n\nE2E 陪伴模式正文种子，用于追读力与逻辑审查冒烟。\n",
        encoding="utf-8",
    )
    state_dir = root / ".state"
    state_dir.mkdir(parents=True, exist_ok=True)
    volume_plan = {
        "volumes": [
            {
                "label": "一",
                "start_chapter": 1,
                "end_chapter": 5,
                "core_conflict": "E2E 陪伴卷纲",
                "locked": True,
            }
        ]
    }
    (state_dir / "volume_plan.json").write_text(
        json.dumps(volume_plan, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    project = get_project_by_slug(E2E_COMPANION_SLUG)
    assert project is not None
    _repair_e2e_companion_project_yaml(project.root)
    return project.root


def ensure_e2e_fixtures() -> None:
    ensure_e2e_ripples()
    ensure_e2e_decision()
    ensure_e2e_cascade_run()
    ensure_e2e_companion_project()
    ensure_e2e_creator_project()
    ensure_e2e_studio_project()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="E2E fixture seed/reset (Phase 9.65 F56)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("ensure", help="Ensure ripples + decision fixtures exist")

    reset_ripple = sub.add_parser("reset-ripple", help="Reset ripple status for idempotency")
    reset_ripple.add_argument("ripple_id")
    reset_ripple.add_argument("to_status", choices=["pending", "applied", "rejected", "failed"])

    sub.add_parser("reset-decision", help="Reset e2e decision to pending")

    sub.add_parser("clear-inbox-pending", help="Resolve pending ripple/decision for Today smoke")
    sub.add_parser("restore-inbox-fixture", help="Reset pending ripple + decision for inbox e2e")

    args = parser.parse_args(argv)
    if args.command == "ensure":
        ensure_e2e_fixtures()
        return 0
    if args.command == "reset-ripple":
        reset_e2e_ripple(args.ripple_id, args.to_status)
        return 0
    if args.command == "reset-decision":
        reset_e2e_decision()
        return 0
    if args.command == "clear-inbox-pending":
        clear_inbox_pending()
        return 0
    if args.command == "restore-inbox-fixture":
        restore_inbox_fixture()
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
