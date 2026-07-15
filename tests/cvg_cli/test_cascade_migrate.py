"""Phase 9.36 F21: cascade v1→v2_weighted migration tests."""
from __future__ import annotations

import pytest

from infra.cli.commands.cascade import CascadeCommand
from infra.cli.options import CascadeOptions
from infra.cli.parsers import create_parser
from infra.cross_volume.cascade_migration import migrate_v1_cascade_runs
from infra.cross_volume.reference_graph import (
    CascadedRipple,
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


def _seed_graph_storage(tmp_path) -> RippleStorage:
    storage = RippleStorage(db_path=tmp_path / "migrate.db")
    g = CrossVolumeReferenceGraph(storage)
    for nid, vol, ch in [("n1", 1, 1), ("n2", 2, 1), ("n3", 2, 2)]:
        g.add_node(ReferenceNode(id=nid, volume=vol, chapter=ch, dimension="character"))
    g.add_edge(ReferenceEdge(id="e12", from_node_id="n1", to_node_id="n2", weight=0.3))
    g.add_edge(ReferenceEdge(id="e13", from_node_id="n1", to_node_id="n3", weight=0.9))
    storage._graph = g
    ripple = CrossVolumeRipple(
        id="rip-m1",
        trigger_volume=1,
        trigger_chapter=1,
        affected_nodes=("n1",),
        affected_edges=(),
        proposed_actions=(),
        status="pending",
    )
    storage.append_ripple(ripple)
    return storage


def _insert_v1_run(storage: RippleStorage, ripple_id: str = "rip-m1", max_depth: int = 3) -> int:
    ripple = storage.get_ripple_by_id(ripple_id)
    assert ripple is not None
    v1 = storage._graph.trigger_cascade(ripple, max_depth=max_depth, weighted=False)
    assert v1.bfs_algorithm_version == "v1"
    return storage.record_cascade_run(ripple_id, v1, max_depth=max_depth)


def make_cascade_options(**overrides) -> CascadeOptions:
    defaults = dict(
        range=[],
        parallel=1,
        verbose=False,
        dry_run=False,
        ripple_id="",
        max_depth=3,
        persist=False,
        action="migrate",
        execute=False,
    )
    defaults.update(overrides)
    return CascadeOptions(**defaults)


class TestCascadeMigrationStorage:
    def test_list_cascade_runs_v1_filters_algorithm(self, tmp_path):
        storage = _seed_graph_storage(tmp_path)
        run_v1 = _insert_v1_run(storage)
        ripple = storage.get_ripple_by_id("rip-m1")
        v2 = storage._graph.trigger_cascade(ripple, max_depth=2, weighted=True)
        run_v2 = storage.record_cascade_run("rip-m1", v2, max_depth=2)

        v1_rows = storage.list_cascade_runs_v1()
        assert len(v1_rows) == 1
        assert v1_rows[0].id == run_v1
        assert v1_rows[0].algorithm == "v1"

        all_runs = storage.get_cascade_runs("rip-m1")
        assert {r.id for r in all_runs} == {run_v1, run_v2}

    def test_update_cascade_run_v2_rewrites_row(self, tmp_path):
        storage = _seed_graph_storage(tmp_path)
        run_id = _insert_v1_run(storage)
        before = storage.get_cascade_run_by_id(run_id)
        assert before.algorithm == "v1"

        ripple = storage.get_ripple_by_id("rip-m1")
        v2 = storage._graph.trigger_cascade(ripple, max_depth=3, weighted=True)
        assert storage.update_cascade_run_v2(run_id, v2) is True

        after = storage.get_cascade_run_by_id(run_id)
        assert after.algorithm == "v2_weighted"
        assert after.depth_reached == v2.depth_reached
        assert {n.id for n in after.cascade_nodes} == {n.id for n in v2.cascade_nodes}

    def test_update_cascade_run_v2_idempotent(self, tmp_path):
        storage = _seed_graph_storage(tmp_path)
        run_id = _insert_v1_run(storage)
        ripple = storage.get_ripple_by_id("rip-m1")
        v2 = storage._graph.trigger_cascade(ripple, max_depth=3, weighted=True)
        assert storage.update_cascade_run_v2(run_id, v2) is True
        assert storage.update_cascade_run_v2(run_id, v2) is False


class TestMigrateV1CascadeRuns:
    def test_dry_run_counts_without_writing(self, tmp_path):
        storage = _seed_graph_storage(tmp_path)
        _insert_v1_run(storage)

        stats = migrate_v1_cascade_runs(storage, execute=False)
        assert stats.scanned == 1
        assert stats.migrated == 1
        assert stats.failed == 0

        run = storage.get_cascade_runs("rip-m1")[0]
        assert run.algorithm == "v1"

    def test_execute_migrates_v1_rows(self, tmp_path):
        storage = _seed_graph_storage(tmp_path)
        run_id = _insert_v1_run(storage)

        stats = migrate_v1_cascade_runs(storage, execute=True)
        assert stats.scanned == 1
        assert stats.migrated == 1
        assert stats.failed == 0

        run = storage.get_cascade_run_by_id(run_id)
        assert run.algorithm == "v2_weighted"

    def test_execute_idempotent_second_run(self, tmp_path):
        storage = _seed_graph_storage(tmp_path)
        _insert_v1_run(storage)

        migrate_v1_cascade_runs(storage, execute=True)
        stats2 = migrate_v1_cascade_runs(storage, execute=True)
        assert stats2.scanned == 0
        assert stats2.migrated == 0

    def test_ripple_id_filter(self, tmp_path):
        storage = _seed_graph_storage(tmp_path)
        _insert_v1_run(storage, ripple_id="rip-m1")

        stats = migrate_v1_cascade_runs(storage, execute=False, ripple_id="rip-other")
        assert stats.scanned == 0


class TestCascadeMigrateCLI:
    def test_migrate_parser_registers(self):
        args = create_parser().parse_args(["cascade", "migrate"])
        assert args.cascade_action == "migrate"
        assert args.execute is False

    def test_migrate_execute_flag(self):
        args = create_parser().parse_args(["cascade", "migrate", "--execute"])
        assert args.execute is True

    def test_cli_dry_run_exit_zero(self, tmp_path, monkeypatch):
        storage = _seed_graph_storage(tmp_path)
        _insert_v1_run(storage)
        monkeypatch.setattr("infra.cli.commands.cascade._get_storage", lambda: storage)

        cmd = CascadeCommand()
        code = cmd.execute(make_cascade_options(action="migrate", execute=False))
        assert code == 0
        assert storage.get_cascade_runs("rip-m1")[0].algorithm == "v1"

    def test_cli_execute_migrates(self, tmp_path, monkeypatch):
        storage = _seed_graph_storage(tmp_path)
        _insert_v1_run(storage)
        monkeypatch.setattr("infra.cli.commands.cascade._get_storage", lambda: storage)

        cmd = CascadeCommand()
        code = cmd.execute(make_cascade_options(action="migrate", execute=True))
        assert code == 0
        assert storage.get_cascade_runs("rip-m1")[0].algorithm == "v2_weighted"
