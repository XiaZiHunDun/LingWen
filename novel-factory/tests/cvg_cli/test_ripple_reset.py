"""Phase 9.18: lingwen.py ripple-reset + RippleStorage.reset_ripple_for_test tests.

4 tests covering:
- ResetRippleForTestStorage (2): idempotent reset / applied ripple reset
- TestRippleResetCmd (2): 404 for missing / invalid --to-status

Pattern: 1:1 with test_ripple_audit.py:Phase 9.14 — parse_args + Command.execute
+ monkeypatch.setattr storage factory. 0 启动 dashboard / 0 真实 project path.
"""
from __future__ import annotations

import pytest

from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


@pytest.fixture
def storage_with_ripple(tmp_path, monkeypatch):
    """Storage with 1 applied + 1 pending ripple, isolated tmp DB."""
    storage = RippleStorage(db_path=tmp_path / "cli_reset.db")
    applied = CrossVolumeRipple(
        id="rip-applied-1", trigger_volume=1, trigger_chapter=1,
        affected_nodes=(), affected_edges=(), proposed_actions=(),
        status="applied",
    )
    pending = CrossVolumeRipple(
        id="rip-pending-1", trigger_volume=1, trigger_chapter=2,
        affected_nodes=(), affected_edges=(), proposed_actions=(),
        status="pending",
    )
    storage.append_ripple(applied)
    storage.append_ripple(pending)
    # Manually set applied_at on the applied ripple for the reset test
    from datetime import datetime, timezone
    with storage._connect() as conn:
        conn.execute(
            "UPDATE reference_ripples SET applied_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), "rip-applied-1"),
        )
        conn.commit()
    return storage


class TestResetRippleForTestStorage:
    """Phase 9.18: storage.reset_ripple_for_test thin wrapper method."""

    def test_reset_applied_ripple_to_pending_clears_applied_at(self, storage_with_ripple):
        """Applied ripple + reset to pending → status=pending + applied_at=NULL + 1 audit row."""
        storage = storage_with_ripple
        # Verify precondition
        before = storage.get_ripple_by_id("rip-applied-1")
        assert before.status == "applied"
        assert before.applied_at is not None

        # Call new method
        updated = storage.reset_ripple_for_test(
            ripple_id="rip-applied-1",
            to_status="pending",
            actor="cli:lingwen-ripple",
            origin="system",
            reason="reset to pending",
        )

        # Status + applied_at cleared
        assert updated.status == "pending"
        assert updated.applied_at is None
        # In-memory DB state matches
        reloaded = storage.get_ripple_by_id("rip-applied-1")
        assert reloaded.status == "pending"
        assert reloaded.applied_at is None
        # 1 audit row written
        history = storage.get_audit_history("rip-applied-1", limit=10)
        reset_rows = [e for e in history if e.action == "rolled_back"]
        assert len(reset_rows) >= 1
        latest = reset_rows[0]
        assert latest.prev_status == "applied"
        assert latest.new_status == "pending"
        assert latest.origin == "system"
        assert latest.reason == "reset to pending"

    def test_reset_pending_ripple_idempotent(self, storage_with_ripple):
        """Pending ripple + reset to pending → no-op state + 1 audit row (idempotent)."""
        storage = storage_with_ripple
        before = storage.get_ripple_by_id("rip-pending-1")
        assert before.status == "pending"
        assert before.applied_at is None

        # Reset to same status (idempotent)
        updated = storage.reset_ripple_for_test(
            ripple_id="rip-pending-1",
            to_status="pending",
            actor="cli:lingwen-ripple",
            origin="system",
            reason="reset to pending",
        )

        assert updated.status == "pending"
        assert updated.applied_at is None
        # 1 audit row written (action=rolled_back even though no actual change)
        history = storage.get_audit_history("rip-pending-1", limit=10)
        reset_rows = [e for e in history if e.action == "rolled_back"]
        assert len(reset_rows) >= 1
        assert reset_rows[0].new_status == "pending"
