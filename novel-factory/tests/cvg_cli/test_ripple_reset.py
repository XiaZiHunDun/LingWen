"""Phase 9.18: lingwen.py ripple-reset + RippleStorage.reset_ripple_for_test tests.

4 tests covering:
- ResetRippleForTestStorage (2): idempotent reset / applied ripple reset
- TestRippleResetCmd (2): 404 for missing / invalid --to-status

Pattern: 1:1 with test_ripple_audit.py:Phase 9.14 — parse_args + Command.execute
+ monkeypatch.setattr storage factory. 0 启动 dashboard / 0 真实 project path.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from infra.cli.commands.ripple_reset import RippleResetCommand
from infra.cli.options import RippleResetOptions
from infra.cli.parsers import create_parser
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


def parse_args(argv: list[str]):
    """Helper: parse argv through the full lingwen.py parser."""
    return create_parser().parse_args(argv)


def make_reset_options(**overrides) -> RippleResetOptions:
    defaults = dict(
        range=[],
        parallel=1,
        verbose=False,
        dry_run=False,
        output=None,
        ripple_id="",
        to_status="",
    )
    defaults.update(overrides)
    return RippleResetOptions(**defaults)


@pytest.fixture
def storage_with_ripple(tmp_path):
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


class TestRippleResetCmd:
    """Phase 9.18: lingwen.py ripple-reset CLI command tests."""

    def test_reset_404_for_missing_ripple(self, storage_with_ripple, monkeypatch, capsys):
        """Unknown ripple_id → exit 1 + 'not found' on stderr."""
        monkeypatch.setattr(
            "infra.cli.commands.ripple_reset._get_storage",
            lambda: storage_with_ripple,
        )
        options = make_reset_options(ripple_id="rip-nonexistent", to_status="pending")
        cmd = RippleResetCommand()
        result = cmd.execute(options)
        assert result == 1
        captured = capsys.readouterr()
        combined = captured.out + captured.err
        assert "not found" in combined.lower()

    def test_reset_rejects_invalid_status_via_parser(self, capsys):
        """--to-status foo → argparse exit 2 (invalid choice)."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["ripple-reset", "rip-pending-1", "--to-status", "foo"])
        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        # argparse 错误走 stderr
        assert "invalid choice" in captured.err.lower() or "foo" in captured.err.lower()
