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


def ensure_e2e_fixtures() -> None:
    ensure_e2e_ripples()
    ensure_e2e_decision()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="E2E fixture seed/reset (Phase 9.65 F56)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("ensure", help="Ensure ripples + decision fixtures exist")

    reset_ripple = sub.add_parser("reset-ripple", help="Reset ripple status for idempotency")
    reset_ripple.add_argument("ripple_id")
    reset_ripple.add_argument("to_status", choices=["pending", "applied", "rejected", "failed"])

    sub.add_parser("reset-decision", help="Reset e2e decision to pending")

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
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
