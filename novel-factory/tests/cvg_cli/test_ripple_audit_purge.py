"""Phase 9.61 F52: ripple-audit purge CLI + retention helper tests."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from infra.cli.commands.ripple_audit import RippleAuditCommand
from infra.cli.options import RippleAuditOptions
from infra.cli.parsers import create_parser
from infra.cross_volume.audit_retention import parse_older_than, purge_audit_entries_older_than
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


@pytest.fixture
def storage_with_audit_rows(tmp_path):
    storage = RippleStorage(db_path=tmp_path / "audit_purge.db")
    storage.append_ripple(
        CrossVolumeRipple(
            id="rip-1",
            trigger_volume=1,
            trigger_chapter=1,
            affected_nodes=(),
            affected_edges=(),
            proposed_actions=(),
            status="pending",
        )
    )
    entry_id = storage.record_audit(
        ripple_id="rip-1",
        action="applied",
        prev_status="pending",
        new_status="applied",
        actor="test",
        origin="cli",
        reason="old entry",
    )
    old_ts = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()
    with storage._connect() as conn:
        conn.execute(
            "UPDATE ripple_audit SET created_at = ? WHERE id = ?",
            (old_ts, entry_id),
        )
        conn.commit()
    storage.record_audit(
        ripple_id="rip-1",
        action="rolled_back",
        prev_status="applied",
        new_status="pending",
        actor="test",
        origin="cli",
        reason="recent entry",
    )
    return storage


class TestAuditRetentionHelpers:
    def test_parse_older_than_days(self):
        assert parse_older_than("30d") == timedelta(days=30)

    def test_purge_dry_run_counts_without_delete(self, storage_with_audit_rows):
        result = purge_audit_entries_older_than(
            storage_with_audit_rows, timedelta(days=90), execute=False
        )
        assert result.matched == 1
        assert result.deleted == 0
        assert storage_with_audit_rows.count_audit_entries_created_before("9999-01-01") == 3

    def test_purge_execute_deletes_old_rows(self, storage_with_audit_rows):
        result = purge_audit_entries_older_than(
            storage_with_audit_rows, timedelta(days=90), execute=True
        )
        assert result.matched == 1
        assert result.deleted == 1
        assert storage_with_audit_rows.count_audit_entries_created_before("9999-01-01") == 2

    def test_purge_execute_idempotent_second_pass(self, storage_with_audit_rows):
        purge_audit_entries_older_than(
            storage_with_audit_rows, timedelta(days=90), execute=True
        )
        second = purge_audit_entries_older_than(
            storage_with_audit_rows, timedelta(days=90), execute=True
        )
        assert second.matched == 0
        assert second.deleted == 0


class TestRippleAuditPurgeCLI:
    def test_parser_purge_flags(self):
        args = create_parser().parse_args(
            ["ripple-audit", "purge", "--older-than", "30d"]
        )
        assert args.command == "ripple-audit"
        assert args.audit_action == "purge"
        assert args.older_than == "30d"
        assert args.execute is False

    def test_purge_cli_dry_run(self, storage_with_audit_rows, monkeypatch, capsys):
        monkeypatch.setattr(
            "infra.cli.commands.ripple_audit._get_storage",
            lambda: storage_with_audit_rows,
        )
        rc = RippleAuditCommand().execute(
            RippleAuditOptions(
                range=[],
                parallel=1,
                verbose=False,
                dry_run=False,
                action="purge",
                older_than="90d",
                execute=False,
            )
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "[PURGE]" in out
        assert "matched=1" in out
        assert "deleted=0" in out
