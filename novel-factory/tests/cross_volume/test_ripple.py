# tests/cross_volume/test_ripple.py
"""Phase 9.10: CrossVolumeRipple + trigger_cascade stub tests."""
from dataclasses import FrozenInstanceError

import pytest

from infra.cross_volume import CrossVolumeReferenceGraph, CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


@pytest.fixture
def storage(tmp_path):
    return RippleStorage(db_path=tmp_path / "ripple.db")


@pytest.fixture
def graph(storage):
    return CrossVolumeReferenceGraph(storage=storage)


class TestRipple:
    def test_ripple_is_frozen(self):
        ripple = CrossVolumeRipple(trigger_volume=2, trigger_chapter=5)
        with pytest.raises(FrozenInstanceError):
            ripple.status = "applied"  # mutation should fail

    def test_ripple_default_status_pending(self):
        ripple = CrossVolumeRipple(trigger_volume=2, trigger_chapter=5)
        assert ripple.status == "pending"
        assert ripple.payload == {}
        assert ripple.affected_nodes == ()
        assert ripple.affected_edges == ()

    def test_trigger_cascade_stub_returns_empty(self, graph):
        ripple = CrossVolumeRipple(trigger_volume=2, trigger_chapter=5)
        result = graph.trigger_cascade(ripple)
        assert result == []  # Phase 14 real BFS impl
