"""Phase 9.45 F34: cascade purge CLI + retention helper tests."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from infra.cli.commands.cascade import CascadeCommand
from infra.cli.options import CascadeOptions
from infra.cli.parsers import create_parser
from infra.cross_volume.cascade_retention import parse_older_than, purge_cascade_runs_older_than
from infra.cross_volume.reference_graph import (
    CascadedRipple,
    CrossVolumeReferenceGraph,
    ReferenceEdge,
    ReferenceNode,
)
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


def _make_cascaded(ripple_id: str) -> CascadedRipple:
    return CascadedRipple(
        trigger_ripple_id=ripple_id,
        cascade_nodes=(),
        cascade_edges=(),
        cascade_actions=(),
        depth_reached=1,
        generated_at=datetime.now(timezone.utc).isoformat(),
        bfs_algorithm_version="v2_weighted",
    )


@pytest.fixture
def storage_with_runs(tmp_path):
    storage = RippleStorage(db_path=tmp_path / "purge.db")
    graph = CrossVolumeReferenceGraph(storage)
    graph.add_node(ReferenceNode(id="n1", volume=1, chapter=1, dimension="character"))
    graph.add_node(ReferenceNode(id="n2", volume=2, chapter=1, dimension="character"))
    graph.add_edge(ReferenceEdge(id="e12", from_node_id="n1", to_node_id="n2"))
    storage._graph = graph
    storage.append_ripple(
        CrossVolumeRipple(
            id="rip-1",
            trigger_volume=1,
            trigger_chapter=1,
            affected_nodes=("n1",),
            affected_edges=(),
            proposed_actions=(),
            status="pending",
        )
    )
    run_id = storage.record_cascade_run("rip-1", _make_cascaded("rip-1"), max_depth=2)
    old_ts = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()
    with storage._connect() as conn:
        conn.execute(
            "UPDATE cascade_runs SET started_at = ?, completed_at = ? WHERE id = ?",
            (old_ts, old_ts, run_id),
        )
        conn.commit()
    storage.record_cascade_run("rip-1", _make_cascaded("rip-1"), max_depth=3)
    return storage


class TestCascadeRetentionHelpers:
    def test_parse_older_than_days(self):
        assert parse_older_than("90d") == timedelta(days=90)

    def test_parse_older_than_invalid(self):
        with pytest.raises(ValueError, match="invalid"):
            parse_older_than("90x")

    def test_purge_dry_run_counts_without_delete(self, storage_with_runs):
        result = purge_cascade_runs_older_than(
            storage_with_runs, timedelta(days=90), execute=False
        )
        assert result.matched == 1
        assert result.deleted == 0
        assert len(storage_with_runs.get_cascade_runs("rip-1")) == 2

    def test_purge_execute_deletes_old_rows(self, storage_with_runs):
        result = purge_cascade_runs_older_than(
            storage_with_runs, timedelta(days=90), execute=True
        )
        assert result.matched == 1
        assert result.deleted == 1
        assert len(storage_with_runs.get_cascade_runs("rip-1")) == 1

    def test_purge_execute_idempotent_second_pass(self, storage_with_runs):
        purge_cascade_runs_older_than(
            storage_with_runs, timedelta(days=90), execute=True
        )
        second = purge_cascade_runs_older_than(
            storage_with_runs, timedelta(days=90), execute=True
        )
        assert second.matched == 0
        assert second.deleted == 0


class TestCascadePurgeCLI:
    def test_parser_purge_flags(self):
        args = create_parser().parse_args(["cascade", "purge", "--older-than", "30d"])
        assert args.cascade_action == "purge"
        assert args.older_than == "30d"
        assert args.execute is False

    def test_purge_cli_dry_run(self, storage_with_runs, monkeypatch, capsys):
        monkeypatch.setattr(
            "infra.cli.commands.cascade._get_storage",
            lambda: storage_with_runs,
        )
        rc = CascadeCommand().execute(
            CascadeOptions(
                range=[],
                parallel=1,
                verbose=False,
                dry_run=False,
                action="purge",
                older_than="90d",
                execute=False,
            )
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "[PURGE]" in out
        assert "matched=1" in out
        assert "deleted=0" in out
