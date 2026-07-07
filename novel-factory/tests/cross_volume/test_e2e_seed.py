"""Phase 9.65 F56: e2e fixture seed/reset tests."""
from __future__ import annotations

from infra.agent_system.decision_queue import HumanDecisionQueue
from infra.cross_volume.e2e_seed import (
    E2E_DECISION_ID,
    E2E_PENDING_RIPPLE_ID,
    ensure_e2e_decision,
    ensure_e2e_ripples,
    reset_e2e_decision,
    reset_e2e_ripple,
)


class TestE2ERippleSeed:
    def test_ensure_e2e_ripples_idempotent(self, tmp_path, monkeypatch):
        db = tmp_path / "cross_volume.db"
        monkeypatch.setattr(
            "infra.cross_volume.e2e_seed._cvg_db_path",
            lambda state_dir=None: db,
        )
        ensure_e2e_ripples()
        ensure_e2e_ripples()
        from infra.cross_volume.storage import RippleStorage

        storage = RippleStorage(db_path=db, graph=None)
        assert storage.get_ripple_by_id(E2E_PENDING_RIPPLE_ID) is not None
        assert storage.get_ripple_by_id(E2E_PENDING_RIPPLE_ID).status == "pending"

    def test_reset_e2e_ripple_clears_applied_at(self, tmp_path, monkeypatch):
        db = tmp_path / "cross_volume.db"
        monkeypatch.setattr(
            "infra.cross_volume.e2e_seed._cvg_db_path",
            lambda state_dir=None: db,
        )
        ensure_e2e_ripples()
        from infra.cross_volume.storage import RippleStorage

        storage = RippleStorage(db_path=db, graph=None)
        storage.update_ripple_status(E2E_PENDING_RIPPLE_ID, "applied", actor="t", origin="ui")
        reset_e2e_ripple(E2E_PENDING_RIPPLE_ID, "pending")
        updated = storage.get_ripple_by_id(E2E_PENDING_RIPPLE_ID)
        assert updated.status == "pending"
        assert updated.applied_at is None


class TestE2EDecisionSeed:
    def test_ensure_and_reset_e2e_decision(self, tmp_path, monkeypatch):
        state_dir = tmp_path / "state"
        monkeypatch.setattr(
            "infra.cross_volume.e2e_seed._state_dir",
            lambda sd=None: state_dir,
        )
        ensure_e2e_decision()
        queue = HumanDecisionQueue(state_dir=str(state_dir))
        assert E2E_DECISION_ID in queue
        queue.resolve(E2E_DECISION_ID, "approve")
        queue.save()
        reset_e2e_decision()
        queue2 = HumanDecisionQueue(state_dir=str(state_dir))
        assert queue2.get(E2E_DECISION_ID).status.value == "pending"


class TestE2ECascadeRunSeed:
    def test_ensure_e2e_cascade_run_idempotent(self, tmp_path, monkeypatch):
        from infra.cross_volume.e2e_seed import ensure_e2e_cascade_run

        db = tmp_path / "cross_volume.db"
        monkeypatch.setattr(
            "infra.cross_volume.e2e_seed._cvg_db_path",
            lambda state_dir=None: db,
        )
        first = ensure_e2e_cascade_run()
        second = ensure_e2e_cascade_run()
        assert first == second
        from infra.cross_volume.storage import RippleStorage

        storage = RippleStorage(db_path=db, graph=None)
        runs = storage.get_cascade_runs(E2E_PENDING_RIPPLE_ID)
        assert len(runs) == 1
        assert runs[0].status == "completed"
