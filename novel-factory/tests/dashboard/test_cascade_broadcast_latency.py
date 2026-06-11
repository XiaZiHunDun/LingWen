"""Phase 9.35: cascade WS broadcast latency_ms (F20).

append_ripple 测 cascade BFS+persist 耗时 → CascadeUpdatePayload.latency_ms;
cascade_notifier 写入 envelope 并 INFO log.
"""
from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

from dashboard import cascade_notifier
from dashboard.protocols import CascadeUpdatePayload
from infra.cross_volume.reference_graph import (
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


@pytest.fixture(autouse=True)
def _reset_ws_manager():
    cascade_notifier.set_ws_manager(None)
    yield
    cascade_notifier.set_ws_manager(None)


@pytest.fixture
def graph_storage(tmp_path):
    storage = RippleStorage(db_path=tmp_path / "latency.db")
    g = CrossVolumeReferenceGraph(storage)
    g.add_node(ReferenceNode(id="n1", volume=1, chapter=1, dimension="character"))
    g.add_node(ReferenceNode(id="n2", volume=2, chapter=1, dimension="character"))
    g.add_edge(ReferenceEdge(id="e12", from_node_id="n1", to_node_id="n2"))
    storage._graph = g
    return storage


class TestCascadeUpdatePayloadLatency:
    def test_latency_ms_optional_backward_compat(self):
        payload = CascadeUpdatePayload(
            ripple_id="r1",
            cascade_node_count=1,
            cascade_edge_count=0,
            depth_reached=1,
            bfs_algorithm_version="v2_weighted",
        )
        assert payload.latency_ms is None

    def test_latency_ms_rejects_negative(self):
        with pytest.raises(Exception):
            CascadeUpdatePayload(
                ripple_id="r1",
                cascade_node_count=0,
                cascade_edge_count=0,
                depth_reached=0,
                bfs_algorithm_version="v1",
                latency_ms=-1,
            )

    def test_notifier_envelope_includes_latency_ms(self):
        captured: list[dict] = []
        cascade_notifier.set_ws_manager(lambda e: captured.append(e))
        cascade_notifier.notify_cascade_update(
            CascadeUpdatePayload(
                ripple_id="r1",
                cascade_node_count=2,
                cascade_edge_count=1,
                depth_reached=1,
                bfs_algorithm_version="v2_weighted",
                latency_ms=42,
            )
        )
        assert captured[0]["payload"]["latency_ms"] == 42

    def test_notifier_logs_latency_ms(self, caplog):
        cascade_notifier.set_ws_manager(MagicMock())
        with caplog.at_level(logging.INFO, logger="dashboard.cascade_notifier"):
            cascade_notifier.notify_cascade_update(
                CascadeUpdatePayload(
                    ripple_id="r-log",
                    cascade_node_count=3,
                    cascade_edge_count=0,
                    depth_reached=1,
                    bfs_algorithm_version="v1",
                    latency_ms=17,
                )
            )
        assert any("latency_ms=17" in r.message for r in caplog.records)

    def test_notifier_skips_latency_log_when_none(self, caplog):
        cascade_notifier.set_ws_manager(MagicMock())
        with caplog.at_level(logging.INFO, logger="dashboard.cascade_notifier"):
            cascade_notifier.notify_cascade_update(
                CascadeUpdatePayload(
                    ripple_id="r-none",
                    cascade_node_count=0,
                    cascade_edge_count=0,
                    depth_reached=0,
                    bfs_algorithm_version="v1",
                )
            )
        assert not any("latency_ms=" in r.message for r in caplog.records)


class TestAppendRippleLatency:
    def test_append_ripple_passes_latency_ms_to_notifier(self, graph_storage, monkeypatch):
        captured: list = []

        def _capture(payload):
            captured.append(payload)

        monkeypatch.setattr(
            "dashboard.cascade_notifier.notify_cascade_update",
            _capture,
        )
        ripple = CrossVolumeRipple(
            id="rip-lat",
            trigger_volume=1,
            trigger_chapter=1,
            affected_nodes=("n1",),
            affected_edges=(),
            proposed_actions=(),
            status="pending",
        )
        graph_storage.append_ripple(ripple)
        assert len(captured) == 1
        payload = captured[0]
        assert isinstance(payload, CascadeUpdatePayload)
        assert payload.ripple_id == "rip-lat"
        assert payload.latency_ms is not None
        assert payload.latency_ms >= 0
