# tests/cross_volume/test_storage.py
"""Phase 9.10: RippleStorage sqlite3 直写 tests."""
import json

import pytest

from infra.cross_volume import CrossVolumeRipple, ReferenceEdge, ReferenceNode
from infra.cross_volume.storage import RippleStorage


@pytest.fixture
def storage(tmp_path):
    return RippleStorage(db_path=tmp_path / "ripple.db")


class TestRippleStorage:
    def test_storage_node_roundtrip(self, storage):
        node = ReferenceNode(dimension="character", volume=1, chapter=3,
                              title="李青云", description="主角",
                              payload={"name": "李青云", "role": "主角"})
        storage.append_node(node)
        loaded = storage.load_all_nodes()
        assert len(loaded) == 1
        n = loaded[0]
        assert n.id == node.id
        assert n.dimension == "character"
        assert n.title == "李青云"
        assert n.payload == {"name": "李青云", "role": "主角"}

    def test_storage_edge_roundtrip(self, storage):
        n1 = ReferenceNode(dimension="character", volume=1, chapter=1, title="A", description="")
        n2 = ReferenceNode(dimension="foreshadow", volume=1, chapter=2, title="B", description="")
        storage.append_node(n1)
        storage.append_node(n2)
        edge = ReferenceEdge(from_node_id=n1.id, to_node_id=n2.id,
                              relationship_type="foreshadows", weight=0.85,
                              payload={"evidence_chapter": 1})
        storage.append_edge(edge)
        loaded = storage.load_all_edges()
        assert len(loaded) == 1
        e = loaded[0]
        assert e.from_node_id == n1.id
        assert e.to_node_id == n2.id
        assert e.relationship_type == "foreshadows"
        assert e.weight == 0.85

    def test_storage_ripple_roundtrip(self, storage):
        ripple = CrossVolumeRipple(
            trigger_volume=2, trigger_chapter=5,
            affected_nodes=("n1", "n2"), affected_edges=("e1",),
            proposed_actions=({"type": "update_node", "node_id": "n1"},),
            status="pending",
        )
        storage.append_ripple(ripple)
        loaded = storage.load_all_ripples()
        assert len(loaded) == 1
        r = loaded[0]
        assert r.id == ripple.id
        assert r.trigger_volume == 2
        assert r.affected_nodes == ("n1", "n2")
        assert r.proposed_actions == ({"type": "update_node", "node_id": "n1"},)

    def test_atomic_batch_rolls_back_on_exception(self, storage):
        n1 = ReferenceNode(dimension="character", volume=1, chapter=1, title="A", description="")
        with pytest.raises(RuntimeError, match="test failure"):
            with storage.atomic_batch() as conn:
                conn.execute(
                    "INSERT INTO reference_nodes VALUES (?,?,?,?,?,?,?,?,?)",
                    (n1.id, n1.dimension, n1.volume, n1.chapter, n1.title,
                     n1.description, json.dumps(n1.payload, ensure_ascii=False),
                     n1.created_at.isoformat(), n1.created_by),
                )
                raise RuntimeError("test failure")
        assert storage.load_all_nodes() == []  # rolled back

    def test_atomic_batch_commits_on_success(self, storage):
        n1 = ReferenceNode(dimension="character", volume=1, chapter=1, title="A", description="")
        n2 = ReferenceNode(dimension="character", volume=1, chapter=2, title="B", description="")
        with storage.atomic_batch() as conn:
            for n in (n1, n2):
                conn.execute(
                    "INSERT INTO reference_nodes VALUES (?,?,?,?,?,?,?,?,?)",
                    (n.id, n.dimension, n.volume, n.chapter, n.title,
                     n.description, json.dumps(n.payload, ensure_ascii=False),
                     n.created_at.isoformat(), n.created_by),
                )
        assert len(storage.load_all_nodes()) == 2

    def test_fk_violation_raises_value_error(self, storage):
        edge = ReferenceEdge(from_node_id="nonexistent", to_node_id="also_nonexistent",
                              relationship_type="mentions")
        with pytest.raises(ValueError, match="storage integrity"):
            storage.append_edge(edge)  # FK violation → ValueError wrap (per spec §4)

    def test_empty_db_init(self, tmp_path):
        storage = RippleStorage(db_path=tmp_path / "fresh.db")
        assert storage.load_all_nodes() == []
        assert storage.load_all_edges() == []
        assert storage.load_all_ripples() == []
