"""Phase 9.20: lingwen.py cascade --persist flag. 1:1 with test_cascade.py pattern."""
from __future__ import annotations

import pytest

from infra.cli.commands.cascade import CascadeCommand
from infra.cli.options import CascadeOptions
from infra.cross_volume.reference_graph import (
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


def make_cascade_options(**overrides) -> CascadeOptions:
    defaults = dict(range=[], parallel=1, verbose=False, dry_run=False,
                    output=None, ripple_id="", max_depth=3, persist=False)
    defaults.update(overrides)
    return CascadeOptions(**defaults)


@pytest.fixture
def storage_with_ripple(tmp_path):
    storage = RippleStorage(db_path=tmp_path / "cascade_persist.db")
    g = CrossVolumeReferenceGraph(storage)
    g.add_node(ReferenceNode(id="n1", volume=1, chapter=1, dimension="character"))
    g.add_node(ReferenceNode(id="n2", volume=2, chapter=1, dimension="character"))
    g.add_edge(ReferenceEdge(id="e12", from_node_id="n1", to_node_id="n2"))
    storage._graph = g
    ripple = CrossVolumeRipple(
        id="rip-1", trigger_volume=1, trigger_chapter=1,
        affected_nodes=("n1",), affected_edges=(), proposed_actions=(), status="pending",
    )
    storage.append_ripple(ripple)
    yield storage


class TestCascadePersist:
    def test_cascade_persist_flag_creates_run(self, tmp_path, monkeypatch):
        """--persist → exit 0, 1 cascade_runs row written, status=completed."""
        storage = RippleStorage(db_path=tmp_path / "cascade_persist.db")
        g = CrossVolumeReferenceGraph(storage)
        g.add_node(ReferenceNode(id="n1", volume=1, chapter=1, dimension="character"))
        g.add_node(ReferenceNode(id="n2", volume=2, chapter=1, dimension="character"))
        g.add_edge(ReferenceEdge(id="e12", from_node_id="n1", to_node_id="n2"))
        storage._graph = g
        ripple = CrossVolumeRipple(id="rip-1", trigger_volume=1, trigger_chapter=1,
            affected_nodes=("n1",), affected_edges=(), proposed_actions=(), status="pending")
        storage.append_ripple(ripple)
        monkeypatch.setattr(
            "infra.cli.commands.cascade._get_storage",
            lambda: storage,
        )
        cmd = CascadeCommand()
        opts = make_cascade_options(ripple_id="rip-1", max_depth=2, persist=True)
        exit_code = cmd.execute(opts)
        assert exit_code == 0
        runs = storage.get_cascade_runs("rip-1")
        assert len(runs) == 1
        assert runs[0].max_depth == 2
        assert runs[0].status == "completed"

    def test_cascade_default_no_persist(self, tmp_path, monkeypatch):
        """omit --persist (default False) → exit 0, 0 cascade_runs rows (Phase 9.19 compat)."""
        storage = RippleStorage(db_path=tmp_path / "cascade_persist.db")
        g = CrossVolumeReferenceGraph(storage)
        g.add_node(ReferenceNode(id="n1", volume=1, chapter=1, dimension="character"))
        g.add_node(ReferenceNode(id="n2", volume=2, chapter=1, dimension="character"))
        g.add_edge(ReferenceEdge(id="e12", from_node_id="n1", to_node_id="n2"))
        storage._graph = g
        ripple = CrossVolumeRipple(id="rip-1", trigger_volume=1, trigger_chapter=1,
            affected_nodes=("n1",), affected_edges=(), proposed_actions=(), status="pending")
        storage.append_ripple(ripple)
        monkeypatch.setattr(
            "infra.cli.commands.cascade._get_storage",
            lambda: storage,
        )
        cmd = CascadeCommand()
        opts = make_cascade_options(ripple_id="rip-1", max_depth=2)
        exit_code = cmd.execute(opts)
        assert exit_code == 0
        runs = storage.get_cascade_runs("rip-1")
        assert len(runs) == 0

    def test_cascade_persist_then_get_runs_lists_new_run(self, tmp_path, monkeypatch):
        """两次 --persist 调 → get_cascade_runs 返 2 行 (latest first)."""
        storage = RippleStorage(db_path=tmp_path / "cascade_persist.db")
        g = CrossVolumeReferenceGraph(storage)
        g.add_node(ReferenceNode(id="n1", volume=1, chapter=1, dimension="character"))
        g.add_node(ReferenceNode(id="n2", volume=2, chapter=1, dimension="character"))
        g.add_edge(ReferenceEdge(id="e12", from_node_id="n1", to_node_id="n2"))
        storage._graph = g
        ripple = CrossVolumeRipple(id="rip-1", trigger_volume=1, trigger_chapter=1,
            affected_nodes=("n1",), affected_edges=(), proposed_actions=(), status="pending")
        storage.append_ripple(ripple)
        monkeypatch.setattr(
            "infra.cli.commands.cascade._get_storage",
            lambda: storage,
        )
        cmd = CascadeCommand()
        cmd.execute(make_cascade_options(ripple_id="rip-1", max_depth=2, persist=True))
        cmd.execute(make_cascade_options(ripple_id="rip-1", max_depth=3, persist=True))
        runs = storage.get_cascade_runs("rip-1")
        assert len(runs) == 2
        assert runs[0].max_depth == 3
        assert runs[1].max_depth == 2
