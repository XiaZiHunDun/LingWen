"""Phase 9.15: ripple_cascade table + storage method tests."""
import json

import pytest

from infra.cross_volume.reference_graph import CascadedRipple, ReferenceNode
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


@pytest.fixture
def storage(tmp_path):
    return RippleStorage(db_path=tmp_path / "cascade_storage.db")


@pytest.fixture
def seeded_cascade(storage):
    """Storage with 1 ripple + 1 cascade pre-seeded."""
    ripple = CrossVolumeRipple(
        id="rip-c1", trigger_volume=1, trigger_chapter=1,
        affected_nodes=("n1",), affected_edges=(), proposed_actions=(),
    )
    storage.append_ripple(ripple)
    cascaded = CascadedRipple(
        trigger_ripple_id="rip-c1",
        cascade_nodes=(ReferenceNode(id="n2", volume=2, chapter=1, dimension="character"),),
        cascade_edges=(),
        cascade_actions=({"action": "propagate", "from": "n1", "to": "n2", "depth": 1, "weight": 1.0},),
        depth_reached=1,
        generated_at="2026-06-10T10:00:00+00:00",
    )
    cascade_id = storage.record_cascade(cascaded)
    return storage, ripple, cascaded, cascade_id


class TestRippleCascadeTable:
    def test_ripple_cascade_table_exists(self, storage):
        """ripple_cascade table created in __init__ via _SCHEMA_SQL."""
        with storage._connect() as conn:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='ripple_cascade'"
            ).fetchone()
        assert row is not None, "ripple_cascade table should exist"

    def test_ripple_cascade_index_exists(self, storage):
        """idx_ripple_cascade_trigger index created."""
        with storage._connect() as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_ripple_cascade_trigger'"
            ).fetchall()
        assert len(rows) == 1


class TestRecordCascade:
    def test_record_cascade_inserts_row(self, seeded_cascade):
        storage, _, cascaded, cascade_id = seeded_cascade
        assert isinstance(cascade_id, int)
        assert cascade_id >= 1
        with storage._connect() as conn:
            row = conn.execute(
                "SELECT * FROM ripple_cascade WHERE id = ?", (cascade_id,)
            ).fetchone()
        assert row["trigger_ripple_id"] == "rip-c1"
        assert row["depth_reached"] == 1

    def test_record_cascade_stores_nodes_edges_actions_as_json(self, seeded_cascade):
        """cascade_nodes / cascade_edges / cascade_actions stored as JSON, parseable."""
        storage, _, cascaded, cascade_id = seeded_cascade
        with storage._connect() as conn:
            row = conn.execute(
                "SELECT cascade_nodes_json, cascade_edges_json, cascade_actions_json"
                " FROM ripple_cascade WHERE id = ?", (cascade_id,)
            ).fetchone()
        nodes = json.loads(row["cascade_nodes_json"])
        actions = json.loads(row["cascade_actions_json"])
        assert len(nodes) == 1
        assert nodes[0]["id"] == "n2"
        assert len(actions) == 1
        assert actions[0]["action"] == "propagate"

    def test_get_cascade_by_ripple_id_returns_latest(self, seeded_cascade):
        """Multiple cascade rows → get returns latest by created_at DESC."""
        storage, _, _, _ = seeded_cascade
        cascaded2 = CascadedRipple(
            trigger_ripple_id="rip-c1",
            cascade_nodes=(), cascade_edges=(), cascade_actions=(),
            depth_reached=0,
            generated_at="2026-06-10T11:00:00+00:00",  # later timestamp
        )
        storage.record_cascade(cascaded2)
        latest = storage.get_cascade_by_ripple_id("rip-c1")
        assert latest is not None
        assert latest.depth_reached == 0  # latest one wins

    def test_get_cascade_by_ripple_id_returns_none_for_missing(self, storage):
        assert storage.get_cascade_by_ripple_id("rip-nonexistent") is None
