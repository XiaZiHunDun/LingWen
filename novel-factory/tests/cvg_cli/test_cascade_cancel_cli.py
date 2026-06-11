"""Phase 9.21 Task 3: lingwen.py cascade cancel subcommand.

⚠️ Breaking change: 'cascade rip-1' 旧用法变 'cascade run rip-1'.
测试走 CascadeCommand.execute() 直接调, 0 破既 Phase 9.19+9.20 风格.
"""
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
                    output=None, ripple_id="", max_depth=3, persist=False,
                    action="run", run_id=0, reason="")
    defaults.update(overrides)
    return CascadeOptions(**defaults)


@pytest.fixture
def storage_with_run(tmp_path, monkeypatch):
    storage = RippleStorage(db_path=tmp_path / "cascade_cancel_cli.db")
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
    cascaded = storage.preview_cascade("rip-1", max_depth=2)
    run_id = storage.record_cascade_run("rip-1", cascaded, max_depth=2)
    monkeypatch.setattr("infra.cli.commands.cascade._get_storage", lambda: storage)
    yield storage, run_id


class TestCascadeCancelCLI:
    def test_cascade_cancel_marks_run(self, storage_with_run):
        """cascade cancel <run_id> → exit 0, run.status='cancelled'."""
        storage, run_id = storage_with_run
        cmd = CascadeCommand()
        opts = make_cascade_options(action="cancel", run_id=run_id, reason="误触")
        exit_code = cmd.execute(opts)
        assert exit_code == 0
        run = storage.get_cascade_run_by_id(run_id)
        assert run.status == "cancelled"

    def test_cascade_cancel_missing_run_returns_1(self, storage_with_run):
        """cascade cancel 999 (missing) → exit 1 + 'not found'."""
        storage, _ = storage_with_run
        cmd = CascadeCommand()
        opts = make_cascade_options(action="cancel", run_id=999)
        exit_code = cmd.execute(opts)
        assert exit_code == 1
