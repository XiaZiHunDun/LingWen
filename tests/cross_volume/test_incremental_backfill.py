"""Phase 9.63 F54: incremental backfill workflow hook tests."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from infra.agent_system.master_controller import MasterController
from infra.cross_volume.backfill import Backfiller, BackfillStats
from infra.cross_volume.incremental_backfill import (
    EMIT_CHAPTER_NODE,
    backfill_stats_to_dict,
    describe_incremental_backfill_hook,
    explain_incremental_backfill_skip,
    extract_chapter_num,
    incremental_backfill_enabled,
    maybe_after_workflow,
    run_incremental_backfill,
    should_run_incremental_backfill,
)
from infra.got.data_structures import NodeExecution, NodeStatus
from infra.got.scheduler import ExecutionSummary

RULES_YAML = """
character:
  name_pattern: "[李青云林凡]{2,3}"
  alias_map: {"凡": "林凡"}
  blacklist: []
  occurrence_threshold: 1
foreshadow:
  keywords: ["伏笔", "暗示"]
  pattern: "(?P<content>[\\u4e00-\\u9fff]{6,30}?(?:伏笔|暗示))"
  chapter_window: 5
setting:
  name_pattern: "[\\u4e00-\\u9fff]{2,6}(?:学院|山门|大陆|帝国|秘境|宗)"
  blacklist: []
  occurrence_threshold: 1
plot_point:
  pattern: "^##\\s+(.+)$"
  min_length: 8
  max_length: 50
  blacklist: []
"""


@pytest.fixture
def corpus(tmp_path):
    root = tmp_path / "corpus"
    root.mkdir()
    (root / "ch005.md").write_text("李青云拜入凌霄宗, 林凡登场.", encoding="utf-8")
    return root


@pytest.fixture
def rules_yaml(tmp_path):
    p = tmp_path / "rules.yaml"
    p.write_text(RULES_YAML, encoding="utf-8")
    return p


def _completed_emit_execution() -> NodeExecution:
    now = datetime.now(timezone.utc)
    return NodeExecution(
        node_id=EMIT_CHAPTER_NODE,
        status=NodeStatus.COMPLETED,
        started_at=now,
        finished_at=now,
        output={"chapter_num": 5},
    )


def _summary_ok() -> ExecutionSummary:
    return ExecutionSummary(completed=7, failed=0, paused=False)


class TestIncrementalBackfillHelpers:
    def test_extract_chapter_num_from_initial_inputs(self):
        assert extract_chapter_num({"chapter_num": 12}, {}) == 12

    def test_extract_chapter_num_from_write_chapter_output(self):
        execution = NodeExecution(
            node_id="write_chapter",
            status=NodeStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            output={"chapter_num": 8, "content": "text"},
        )
        assert extract_chapter_num(None, {"write_chapter": execution}) == 8

    def test_should_run_when_emit_chapter_completed(self):
        executions = {EMIT_CHAPTER_NODE: _completed_emit_execution()}
        assert should_run_incremental_backfill(
            "novel_writing", _summary_ok(), executions
        )

    def test_should_not_run_when_workflow_failed(self):
        executions = {EMIT_CHAPTER_NODE: _completed_emit_execution()}
        summary = ExecutionSummary(completed=6, failed=1, paused=False)
        assert not should_run_incremental_backfill(
            "novel_writing", summary, executions
        )

    def test_incremental_backfill_enabled_env(self, monkeypatch):
        monkeypatch.delenv("LINGWEN_INCREMENTAL_BACKFILL", raising=False)
        assert not incremental_backfill_enabled()
        monkeypatch.setenv("LINGWEN_INCREMENTAL_BACKFILL", "1")
        assert incremental_backfill_enabled()

    def test_backfill_stats_to_dict_serializes_dataclass(self):
        stats = BackfillStats(
            character_count=1,
            foreshadow_count=0,
            setting_count=1,
            plot_point_count=0,
            total_count=2,
            elapsed_s=0.42,
            dry_run=False,
            nodes_written=2,
            nodes_skipped=1,
        )
        payload = backfill_stats_to_dict(stats)
        assert payload == {
            "character_count": 1,
            "foreshadow_count": 0,
            "setting_count": 1,
            "plot_point_count": 0,
            "total_count": 2,
            "elapsed_s": 0.42,
            "dry_run": False,
            "nodes_written": 2,
            "nodes_skipped": 1,
            "pre_node_count": None,
            "post_node_count": None,
        }

    def test_backfill_stats_to_dict_none(self):
        assert backfill_stats_to_dict(None) is None

    def test_describe_incremental_backfill_hook(self):
        rows = describe_incremental_backfill_hook()
        assert len(rows) >= 4
        triggers = {row["trigger"] for row in rows}
        assert "env LINGWEN_INCREMENTAL_BACKFILL" in triggers
        assert EMIT_CHAPTER_NODE in triggers

    def test_explain_skip_when_disabled(self):
        executions = {EMIT_CHAPTER_NODE: _completed_emit_execution()}
        reason = explain_incremental_backfill_skip(
            "novel_writing", {"chapter_num": 5}, executions, _summary_ok(), enabled=False
        )
        assert reason == "disabled: set LINGWEN_INCREMENTAL_BACKFILL=1"

    def test_explain_skip_when_paused(self):
        executions = {EMIT_CHAPTER_NODE: _completed_emit_execution()}
        summary = ExecutionSummary(completed=6, failed=0, paused=True)
        reason = explain_incremental_backfill_skip(
            "novel_writing", {"chapter_num": 5}, executions, summary, enabled=True
        )
        assert reason == "workflow_paused"

    def test_explain_skip_none_when_would_run(self):
        executions = {EMIT_CHAPTER_NODE: _completed_emit_execution()}
        assert (
            explain_incremental_backfill_skip(
                "novel_writing", {"chapter_num": 5}, executions, _summary_ok(), enabled=True
            )
            is None
        )


class TestIncrementalBackfillRunChapters:
    def test_run_chapters_writes_single_chapter(
        self, rules_yaml, corpus, tmp_path
    ):
        from infra.cross_volume.reference_graph import CrossVolumeReferenceGraph
        from infra.cross_volume.storage import RippleStorage

        storage = RippleStorage(db_path=tmp_path / "ripple.db")
        graph = CrossVolumeReferenceGraph(storage=storage)
        backfiller = Backfiller(
            rules_path=rules_yaml, corpus_root=corpus, graph=graph
        )
        stats = run_incremental_backfill(5, backfiller=backfiller)
        assert stats is not None
        assert stats.dry_run is False
        assert stats.nodes_written >= 1
        assert stats.total_count >= 1


class TestIncrementalBackfillWorkflowHook:
    def test_maybe_after_workflow_invokes_backfiller(self, monkeypatch):
        mock_stats = MagicMock()
        mock_stats.summary.return_value = "mock"
        mock_run = MagicMock(return_value=mock_stats)
        monkeypatch.setattr(
            "infra.cross_volume.incremental_backfill.run_incremental_backfill",
            mock_run,
        )
        executions = {EMIT_CHAPTER_NODE: _completed_emit_execution()}
        stats = maybe_after_workflow(
            "novel_writing",
            {"chapter_num": 5},
            executions,
            _summary_ok(),
            enabled=True,
        )
        assert stats is mock_stats
        mock_run.assert_called_once()
        assert mock_run.call_args.args[0] == 5

    def test_maybe_after_workflow_skipped_when_disabled(self, monkeypatch):
        mock_run = MagicMock()
        monkeypatch.setattr(
            "infra.cross_volume.incremental_backfill.run_incremental_backfill",
            mock_run,
        )
        executions = {EMIT_CHAPTER_NODE: _completed_emit_execution()}
        assert (
            maybe_after_workflow(
                "novel_writing",
                {"chapter_num": 5},
                executions,
                _summary_ok(),
                enabled=False,
            )
            is None
        )
        mock_run.assert_not_called()

    def test_master_controller_run_workflow_triggers_hook(
        self, monkeypatch, tmp_path
    ):
        mock_hook = MagicMock(return_value={"nodes_written": 2})
        monkeypatch.setattr(
            MasterController,
            "_maybe_incremental_backfill",
            mock_hook,
        )
        controller = MasterController.__new__(MasterController)
        controller._incremental_backfill_enabled = True
        controller._decision_queue = MagicMock()
        controller._decision_queue.create = MagicMock()
        controller._current_budget_usd = None
        controller._current_run_id = None
        controller.budget_service = None

        summary = _summary_ok()
        emit = _completed_emit_execution()
        graph = MagicMock()
        graph.node_ids.return_value = [EMIT_CHAPTER_NODE]
        graph.has_execution.return_value = True
        graph.get_execution.return_value = emit
        graph.get_node.return_value = MagicMock(depends_on=[])

        scheduler = MagicMock()
        scheduler.run.return_value = summary

        monkeypatch.setattr(
            "infra.agent_system.got_bridge.build_got_scheduler",
            lambda **kwargs: (scheduler, graph),
        )

        result = controller.run_workflow(
            "novel_writing",
            initial_inputs={"chapter_num": 5},
        )
        mock_hook.assert_called_once()
        assert result["incremental_backfill"] == {"nodes_written": 2}
