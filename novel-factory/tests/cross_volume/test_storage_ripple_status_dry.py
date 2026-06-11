"""Phase 9.25 F9: DRY _update_ripple_status_internal helper tests."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


@pytest.fixture
def storage(tmp_path):
    return RippleStorage(db_path=tmp_path / "ripple_status_dry.db")


@pytest.fixture
def storage_with_applied_ripple(storage):
    ripple = CrossVolumeRipple(
        id="rip-dry-1",
        trigger_volume=1,
        trigger_chapter=1,
        affected_nodes=(),
        affected_edges=(),
        proposed_actions=(),
        status="applied",
    )
    storage.append_ripple(ripple)
    applied_at = datetime.now(timezone.utc).isoformat()
    with storage._connect() as conn:
        storage._update_ripple_status_internal(
            conn, "rip-dry-1", "applied", applied_at
        )
        conn.commit()
    return storage, applied_at


class TestUpdateRippleStatusInternal:
    def test_sets_status_and_null_applied_at(self, storage_with_applied_ripple):
        storage, _ = storage_with_applied_ripple
        with storage._connect() as conn:
            storage._update_ripple_status_internal(
                conn, "rip-dry-1", "pending", None
            )
            conn.commit()
        row = storage.get_ripple_by_id("rip-dry-1")
        assert row.status == "pending"
        assert row.applied_at is None

    def test_sets_status_and_iso_applied_at(self, storage_with_applied_ripple):
        storage, _ = storage_with_applied_ripple
        ts = "2026-06-11T12:00:00+00:00"
        with storage._connect() as conn:
            storage._update_ripple_status_internal(
                conn, "rip-dry-1", "applied", ts
            )
            conn.commit()
        row = storage.get_ripple_by_id("rip-dry-1")
        assert row.status == "applied"
        assert row.applied_at == datetime.fromisoformat(ts)

    def test_accepts_all_five_status_values(self, storage):
        for idx, status in enumerate(
            ("pending", "applied", "rejected", "failed", "created")
        ):
            ripple_id = f"rip-status-{idx}"
            storage.append_ripple(
                CrossVolumeRipple(
                    id=ripple_id,
                    trigger_volume=1,
                    trigger_chapter=idx + 1,
                    affected_nodes=(),
                    affected_edges=(),
                    proposed_actions=(),
                    status="pending",
                )
            )
            with storage._connect() as conn:
                storage._update_ripple_status_internal(
                    conn, ripple_id, status, None
                )
                conn.commit()
            assert storage.get_ripple_by_id(ripple_id).status == status


class TestRollbackAndResetUseInternalHelper:
    @pytest.fixture
    def spy_helper(self, monkeypatch):
        calls: list[tuple[str, str, str | None]] = []

        original = RippleStorage._update_ripple_status_internal

        def _spy(self, conn, ripple_id, new_status, applied_at):
            calls.append((ripple_id, new_status, applied_at))
            return original(self, conn, ripple_id, new_status, applied_at)

        monkeypatch.setattr(
            RippleStorage, "_update_ripple_status_internal", _spy
        )
        return calls

    def test_rollback_delegates_to_internal_helper(
        self, storage_with_applied_ripple, spy_helper
    ):
        storage, _ = storage_with_applied_ripple
        storage.rollback_ripple(
            "rip-dry-1", actor="user", origin="ui", reason="undo"
        )
        assert spy_helper == [("rip-dry-1", "pending", None)]

    def test_reset_for_test_delegates_to_internal_helper(
        self, storage_with_applied_ripple, spy_helper
    ):
        storage, _ = storage_with_applied_ripple
        storage.reset_ripple_for_test(
            ripple_id="rip-dry-1",
            to_status="rejected",
            actor="cli:lingwen-ripple",
            origin="system",
            reason="reset to rejected",
        )
        assert spy_helper == [("rip-dry-1", "rejected", None)]

    def test_rollback_and_reset_share_same_db_shape_for_pending(
        self, tmp_path
    ):
        """Both paths clear applied_at when targeting pending."""
        for ripple_id, reset_fn in (
            (
                "rip-rollback",
                lambda s: s.rollback_ripple(
                    "rip-rollback",
                    actor="user",
                    origin="ui",
                    reason="undo",
                ),
            ),
            (
                "rip-reset",
                lambda s: s.reset_ripple_for_test(
                    ripple_id="rip-reset",
                    to_status="pending",
                    reason="reset to pending",
                ),
            ),
        ):
            s = RippleStorage(db_path=tmp_path / f"{ripple_id}.db")
            s.append_ripple(
                CrossVolumeRipple(
                    id=ripple_id,
                    trigger_volume=1,
                    trigger_chapter=1,
                    affected_nodes=(),
                    affected_edges=(),
                    proposed_actions=(),
                    status="applied",
                )
            )
            with s._connect() as conn:
                conn.execute(
                    "UPDATE reference_ripples SET applied_at = ? WHERE id = ?",
                    (datetime.now(timezone.utc).isoformat(), ripple_id),
                )
                conn.commit()
            reset_fn(s)
            row = s.get_ripple_by_id(ripple_id)
            assert row.status == "pending"
            assert row.applied_at is None
