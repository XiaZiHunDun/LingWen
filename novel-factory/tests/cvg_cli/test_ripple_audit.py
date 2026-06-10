"""Phase 9.14: lingwen.py ripple-audit + ripple-rollback CLI tests.

6 tests covering the 2 new top-level subcommands (additive, 0 changes to
Phase 9.11 backfill):

TestRippleAuditCmd (3):
1. test_audit_happy              — applied ripple + 1 'created' entry printed
2. test_audit_404_for_missing    — unknown ripple_id → exit 1 + 'not found'
3. test_audit_empty_message      — limit=0 → 'No audit entries' / '0 entries'

TestRippleRollbackCmd (3):
4. test_rollback_happy            — applied → pending + applied_at NULL + exit 0
5. test_rollback_fails_without_reason — argparse MissingOption / exit 2
6. test_rollback_fails_for_pending_status — ValueError → exit 1

Pattern: parse_args(argv) + Command.execute(options) (1:1 with
test_cli_llm_flags.py:Phase 9.12). Storage is monkeypatched at the call
site so 0 启动 dashboard / 0 真实 project path。
"""
from __future__ import annotations

import pytest

from infra.cli.commands.ripple_audit import RippleAuditCommand
from infra.cli.commands.ripple_rollback import RippleRollbackCommand
from infra.cli.options import RippleAuditOptions, RippleRollbackOptions
from infra.cli.parsers import create_parser
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


def parse_args(argv: list[str]):
    """Helper: parse argv through the full lingwen.py parser."""
    return create_parser().parse_args(argv)


def make_audit_options(**overrides) -> RippleAuditOptions:
    defaults = dict(
        range=[],
        parallel=1,
        verbose=False,
        dry_run=False,
        output=None,
        ripple_id="",
        limit=20,
    )
    defaults.update(overrides)
    return RippleAuditOptions(**defaults)


def make_rollback_options(**overrides) -> RippleRollbackOptions:
    defaults = dict(
        range=[],
        parallel=1,
        verbose=False,
        dry_run=False,
        output=None,
        ripple_id="",
        reason="",
        actor="cli:lingwen-ripple",
    )
    defaults.update(overrides)
    return RippleRollbackOptions(**defaults)


@pytest.fixture
def storage_with_ripple(tmp_path, monkeypatch):
    """Storage with 1 applied ripple + 1 pending ripple (T2 audit hook
    auto-writes 'created' entries via append_ripple, so each ripple has
    at least 1 audit row by the time tests run)."""
    storage = RippleStorage(db_path=tmp_path / "cli_audit.db")
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
    return storage


class TestRippleAuditCmd:
    def test_audit_happy(self, storage_with_ripple, monkeypatch, capsys):
        """lingwen.py ripple-audit <id> prints audit entries for existing ripple."""
        # Patch the storage factory used inside the command module
        monkeypatch.setattr(
            "infra.cli.commands.ripple_audit._get_storage",
            lambda: storage_with_ripple,
        )
        options = make_audit_options(ripple_id="rip-applied-1")
        cmd = RippleAuditCommand()
        result = cmd.execute(options)
        assert result == 0
        captured = capsys.readouterr()
        # Header mentions ripple id
        assert "rip-applied-1" in captured.out
        # 'created' entry written by T2 hook in append_ripple()
        assert "created" in captured.out

    def test_audit_404_for_missing(self, storage_with_ripple, monkeypatch, capsys):
        """Unknown ripple_id → exit 1 + 'not found' on stderr/stdout."""
        monkeypatch.setattr(
            "infra.cli.commands.ripple_audit._get_storage",
            lambda: storage_with_ripple,
        )
        options = make_audit_options(ripple_id="rip-nonexistent")
        cmd = RippleAuditCommand()
        result = cmd.execute(options)
        assert result == 1
        captured = capsys.readouterr()
        # Error visible on either stream
        combined = captured.out + captured.err
        assert "not found" in combined.lower()

    def test_audit_empty_message(self, storage_with_ripple, monkeypatch, capsys):
        """limit=0 → empty list message (defensive case)."""
        monkeypatch.setattr(
            "infra.cli.commands.ripple_audit._get_storage",
            lambda: storage_with_ripple,
        )
        options = make_audit_options(ripple_id="rip-applied-1", limit=0)
        cmd = RippleAuditCommand()
        result = cmd.execute(options)
        assert result == 0
        captured = capsys.readouterr()
        # Either "No audit entries" or "0 entries" is acceptable
        combined = captured.out + captured.err
        assert "0 entries" in combined or "no audit" in combined.lower()


class TestRippleRollbackCmd:
    def test_rollback_happy(self, storage_with_ripple, monkeypatch, capsys):
        """applied ripple + --reason → status=pending + applied_at=NULL + exit 0."""
        monkeypatch.setattr(
            "infra.cli.commands.ripple_rollback._get_storage",
            lambda: storage_with_ripple,
        )
        options = make_rollback_options(ripple_id="rip-applied-1", reason="CLI test")
        cmd = RippleRollbackCommand()
        result = cmd.execute(options)
        assert result == 0
        captured = capsys.readouterr()
        assert "rolled back" in captured.out.lower()
        # Verify DB state
        updated = storage_with_ripple.get_ripple_by_id("rip-applied-1")
        assert updated.status == "pending"
        assert updated.applied_at is None

    def test_rollback_fails_without_reason(self, storage_with_ripple, monkeypatch, capsys):
        """--reason missing → argparse rejects (exit 2 from parse_args).

        Pattern follows test_cli_llm_flags: validate at parse_args layer.
        """
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["ripple-rollback", "rip-applied-1"])
        # argparse uses exit 2 for usage errors
        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "--reason" in captured.err or "required" in captured.err.lower()

    def test_rollback_fails_for_pending_status(self, storage_with_ripple, monkeypatch, capsys):
        """Rollback a 'pending' ripple → ValueError → exit 1."""
        monkeypatch.setattr(
            "infra.cli.commands.ripple_rollback._get_storage",
            lambda: storage_with_ripple,
        )
        options = make_rollback_options(ripple_id="rip-pending-1", reason="should fail")
        cmd = RippleRollbackCommand()
        result = cmd.execute(options)
        assert result == 1
        captured = capsys.readouterr()
        combined = captured.out + captured.err
        assert "can only rollback" in combined.lower() or "valueerror" in combined.lower()
