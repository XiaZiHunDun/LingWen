"""Phase 9.44 F33: cascade_broadcast_log SQLite persistence tests."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from infra.cross_volume.reference_graph import (
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


@pytest.fixture
def graph_storage(tmp_path):
    storage = RippleStorage(db_path=tmp_path / "broadcast_log.db")
    graph = CrossVolumeReferenceGraph(storage)
    graph.add_node(ReferenceNode(id="n1", volume=1, chapter=1, dimension="character"))
    graph.add_node(ReferenceNode(id="n2", volume=2, chapter=1, dimension="character"))
    graph.add_edge(ReferenceEdge(id="e12", from_node_id="n1", to_node_id="n2"))
    storage._graph = graph
    return storage


@pytest.fixture
def storage_only(tmp_path):
    return RippleStorage(db_path=tmp_path / "broadcast_only.db")


def _insert_ripple(storage: RippleStorage, ripple_id: str) -> None:
    storage.append_ripple(
        CrossVolumeRipple(
            id=ripple_id,
            trigger_volume=1,
            trigger_chapter=1,
            affected_nodes=(),
            affected_edges=(),
            proposed_actions=(),
            status="pending",
        )
    )


class TestCascadeBroadcastLogStorage:
    def test_append_and_list_returns_newest_first(self, storage_only):
        _insert_ripple(storage_only, "rip-a")
        storage_only.append_cascade_broadcast_log("rip-a", latency_ms=12)
        storage_only.append_cascade_broadcast_log("rip-a", latency_ms=34)
        rows = storage_only.get_cascade_broadcast_logs("rip-a")
        assert len(rows) == 2
        assert rows[0].latency_ms == 34
        assert rows[1].latency_ms == 12

    def test_list_respects_limit_offset(self, storage_only):
        _insert_ripple(storage_only, "rip-b")
        for ms in (10, 20, 30):
            storage_only.append_cascade_broadcast_log("rip-b", latency_ms=ms)
        page = storage_only.get_cascade_broadcast_logs("rip-b", limit=1, offset=1)
        assert len(page) == 1
        assert page[0].latency_ms == 20

    def test_append_rejects_negative_latency(self, storage_only):
        _insert_ripple(storage_only, "rip-x")
        with pytest.raises(ValueError, match="latency_ms"):
            storage_only.append_cascade_broadcast_log("rip-x", latency_ms=-1)

    def test_unknown_ripple_returns_empty_list(self, graph_storage):
        assert graph_storage.get_cascade_broadcast_logs("missing") == []

    def test_append_ripple_persists_broadcast_log(self, graph_storage, monkeypatch):
        monkeypatch.setattr(
            "dashboard.cascade_notifier.notify_cascade_update",
            MagicMock(),
        )
        ripple = CrossVolumeRipple(
            id="rip-log",
            trigger_volume=1,
            trigger_chapter=1,
            affected_nodes=("n1",),
            affected_edges=(),
            proposed_actions=(),
            status="pending",
        )
        graph_storage.append_ripple(ripple)
        rows = graph_storage.get_cascade_broadcast_logs("rip-log")
        assert len(rows) == 1
        assert rows[0].latency_ms >= 0
        assert rows[0].ripple_id == "rip-log"
