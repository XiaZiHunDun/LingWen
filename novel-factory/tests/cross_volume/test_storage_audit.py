"""Phase 9.14: ripple_audit table schema + audit method tests."""
import sqlite3
from datetime import datetime, timezone

import pytest

from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import AuditEntry, RippleStorage


@pytest.fixture
def storage(tmp_path):
    return RippleStorage(db_path=tmp_path / "audit_schema.db")


class TestRippleAuditSchema:
    def test_ripple_audit_table_exists(self, storage):
        """ripple_audit table created in __init__ via _SCHEMA_SQL."""
        with storage._connect() as conn:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='ripple_audit'"
            ).fetchone()
        assert row is not None, "ripple_audit table should exist"

    def test_ripple_audit_indexes_exist(self, storage):
        """idx_audit_ripple + idx_audit_actor 2 indexes created."""
        with storage._connect() as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_audit_%'"
            ).fetchall()
        index_names = {r["name"] for r in rows}
        assert "idx_audit_ripple" in index_names
        assert "idx_audit_actor" in index_names

    def test_ripple_audit_idempotent_migration(self, tmp_path):
        """Re-init on existing DB should not raise (CREATE TABLE IF NOT EXISTS)."""
        db_path = tmp_path / "audit_idem.db"
        RippleStorage(db_path=db_path)  # first init
        # Second init must not raise
        RippleStorage(db_path=db_path)

    def test_ripple_audit_check_constraint_action(self, storage):
        """Invalid action value rejected by CHECK constraint."""
        with storage._connect() as conn:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO ripple_audit (ripple_id, action, new_status, actor, origin, created_at)"
                    " VALUES ('rip-x', 'bogus_action', 'pending', 'user', 'ui', '2026-06-10T10:00:00')"
                )
                conn.commit()

    def test_ripple_audit_check_constraint_origin(self, storage):
        """Invalid origin value rejected by CHECK constraint."""
        with storage._connect() as conn:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO ripple_audit (ripple_id, action, new_status, actor, origin, created_at)"
                    " VALUES ('rip-x', 'created', 'pending', 'user', 'bogus_origin', '2026-06-10T10:00:00')"
                )
                conn.commit()


@pytest.fixture
def seeded_storage(tmp_path):
    """Storage with 1 reference_ripple pre-seeded (for audit tests)."""
    s = RippleStorage(db_path=tmp_path / "audit_method.db")
    ripple = CrossVolumeRipple(
        id="rip-audit-1", trigger_volume=1, trigger_chapter=1,
        affected_nodes=(), affected_edges=(), proposed_actions=(),
        status="applied",
    )
    s.append_ripple(ripple)
    return s


class TestRecordAudit:
    def test_record_audit_writes_row_and_returns_id(self, seeded_storage):
        """record_audit inserts 1 row, returns lastrowid."""
        audit_id = seeded_storage.record_audit(
            ripple_id="rip-audit-1", action="rolled_back",
            prev_status="applied", new_status="pending",
            actor="user", origin="ui", reason="test",
        )
        assert isinstance(audit_id, int)
        assert audit_id >= 1

    def test_record_audit_with_null_prev_status(self, seeded_storage):
        """created entry prev_status=NULL allowed (append_ripple hook writes 1 'created' first)."""
        seeded_storage.record_audit(
            ripple_id="rip-audit-1", action="created",
            prev_status=None, new_status="pending",
            actor="system:phase9.11-backfill", origin="system", reason=None,
        )
        entries = seeded_storage.get_audit_history("rip-audit-1")
        # append_ripple hook already wrote 1 'created' entry; record_audit writes 1 more = 2 total
        assert len(entries) == 2
        # newest entry is the one we just wrote
        assert entries[0].prev_status is None
        assert entries[0].actor == "system:phase9.11-backfill"


class TestGetAuditHistory:
    def test_get_audit_history_orders_newest_first(self, seeded_storage):
        """4 entries written in order → get returns newest first
        (append_ripple hook wrote 1 'created' first, then 3 more)."""
        seeded_storage.record_audit("rip-audit-1", "created", None, "pending", "sys", "system", None)
        seeded_storage.record_audit("rip-audit-1", "applied", "pending", "applied", "user", "ui", None)
        seeded_storage.record_audit("rip-audit-1", "rolled_back", "applied", "pending", "user", "ui", "r1")
        entries = seeded_storage.get_audit_history("rip-audit-1")
        # 4 entries: 1 from append_ripple (created) + 3 from this test
        assert [e.action for e in entries] == ["rolled_back", "applied", "created", "created"]

    def test_get_audit_history_pagination(self, seeded_storage):
        """limit + offset paginate correctly."""
        for i in range(5):
            seeded_storage.record_audit("rip-audit-1", "applied", "p", "a", f"user-{i}", "ui", None)
        page1 = seeded_storage.get_audit_history("rip-audit-1", limit=2, offset=0)
        page2 = seeded_storage.get_audit_history("rip-audit-1", limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id

    def test_get_audit_history_empty_ripple(self, seeded_storage):
        """Non-existent ripple_id returns []."""
        assert seeded_storage.get_audit_history("rip-nonexistent") == []


class TestRollbackRipple:
    def test_rollback_happy_path_atomic(self, seeded_storage):
        """applied → pending + applied_at NULL + audit entry written."""
        before = seeded_storage.get_ripple_by_id("rip-audit-1")
        assert before.status == "applied"
        updated = seeded_storage.rollback_ripple(
            "rip-audit-1", actor="user", origin="ui", reason="误操作",
        )
        assert updated.status == "pending"
        assert updated.applied_at is None
        entries = seeded_storage.get_audit_history("rip-audit-1")
        # append_ripple hook wrote 1 'created' entry, rollback writes 1 'rolled_back' = 2 total
        assert len(entries) == 2
        assert entries[0].action == "rolled_back"
        assert entries[0].prev_status == "applied"
        assert entries[0].new_status == "pending"
        assert entries[0].reason == "误操作"

    def test_rollback_raises_keyerror_for_missing(self, seeded_storage):
        with pytest.raises(KeyError):
            seeded_storage.rollback_ripple("rip-nonexistent", actor="u", origin="ui", reason="r")

    def test_rollback_raises_valueerror_for_pending(self, seeded_storage):
        """Cannot rollback a pending ripple (must be applied or rejected)."""
        with seeded_storage._connect() as conn:
            conn.execute("UPDATE reference_ripples SET status='pending' WHERE id=?", ("rip-audit-1",))
            conn.commit()
        with pytest.raises(ValueError, match="can only rollback applied/rejected"):
            seeded_storage.rollback_ripple("rip-audit-1", actor="u", origin="ui", reason="r")

    def test_rollback_raises_valueerror_for_empty_reason(self, seeded_storage):
        with pytest.raises(ValueError, match="reason is required"):
            seeded_storage.rollback_ripple("rip-audit-1", actor="u", origin="ui", reason="")

    def test_rollback_raises_valueerror_for_whitespace_reason(self, seeded_storage):
        with pytest.raises(ValueError, match="reason is required"):
            seeded_storage.rollback_ripple("rip-audit-1", actor="u", origin="ui", reason="   ")


class TestUpdateRippleStatusAuditHook:
    def test_update_status_writes_audit_entry(self, seeded_storage):
        """update_ripple_status internally calls record_audit."""
        with seeded_storage._connect() as conn:
            conn.execute("UPDATE reference_ripples SET status='pending' WHERE id=?", ("rip-audit-1",))
            conn.commit()
        seeded_storage.update_ripple_status("rip-audit-1", "applied", actor="user")
        entries = seeded_storage.get_audit_history("rip-audit-1")
        actions = [e.action for e in entries]
        # append_ripple hook wrote 'created' + update_ripple_status wrote 'applied'
        assert "applied" in actions
        assert "created" in actions
