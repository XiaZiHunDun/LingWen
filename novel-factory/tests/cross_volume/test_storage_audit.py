"""Phase 9.14: ripple_audit table schema tests."""
import sqlite3

import pytest

from infra.cross_volume.storage import RippleStorage


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
