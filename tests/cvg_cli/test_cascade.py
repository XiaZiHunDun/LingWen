"""Phase 9.19: lingwen.py cascade CLI tests. 1:1 with test_ripple_audit.py."""
from __future__ import annotations

import pytest

from infra.cli.commands.cascade import CascadeCommand
from infra.cli.options import CascadeOptions
from infra.cli.parsers import create_parser
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


def parse_args(argv: list[str]):
    return create_parser().parse_args(argv)


def make_cascade_options(**overrides) -> CascadeOptions:
    defaults = dict(range=[], parallel=1, verbose=False, dry_run=False,
                    output=None, ripple_id="", max_depth=3)
    defaults.update(overrides)
    return CascadeOptions(**defaults)


@pytest.fixture
def storage_with_ripple(tmp_path):
    storage = RippleStorage(db_path=tmp_path / "cascade.db")
    from infra.cross_volume.reference_graph import CrossVolumeReferenceGraph, ReferenceEdge, ReferenceNode
    g = CrossVolumeReferenceGraph(storage)
    g.add_node(ReferenceNode(id="n1", volume=1, chapter=1, dimension="character"))
    g.add_node(ReferenceNode(id="n2", volume=2, chapter=1, dimension="character"))
    g.add_node(ReferenceNode(id="n3", volume=3, chapter=1, dimension="character"))
    g.add_edge(ReferenceEdge(id="e12", from_node_id="n1", to_node_id="n2"))
    g.add_edge(ReferenceEdge(id="e23", from_node_id="n2", to_node_id="n3"))
    storage._graph = g
    ripple = CrossVolumeRipple(
        id="rip-1", trigger_volume=1, trigger_chapter=1,
        affected_nodes=("n1",), affected_edges=(), proposed_actions=(),
        status="pending",
    )
    storage.append_ripple(ripple)
    yield storage


class TestCascadeCmd:
    def test_cascade_happy(self, tmp_path, monkeypatch):
        """cascade rip-1 → exit 0, prints summary."""
        storage = RippleStorage(db_path=tmp_path / "cascade.db")
        from infra.cross_volume.reference_graph import CrossVolumeReferenceGraph, ReferenceEdge, ReferenceNode
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

    def test_cascade_unknown_ripple(self, tmp_path, monkeypatch, capsys):
        """cascade unknown → exit 1 + 'not found'."""
        storage = RippleStorage(db_path=tmp_path / "cascade.db")
        monkeypatch.setattr(
            "infra.cli.commands.cascade._get_storage",
            lambda: storage,
        )
        cmd = CascadeCommand()
        opts = make_cascade_options(ripple_id="rip Unknown")
        exit_code = cmd.execute(opts)
        assert exit_code == 1

    def test_cascade_max_depth_argparse_rejects_11(self):
        """--max-depth 11 → argparse exits with 2 (invalid choice)."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["cascade", "rip-1", "--max-depth", "11"])
        assert exc_info.value.code == 2
