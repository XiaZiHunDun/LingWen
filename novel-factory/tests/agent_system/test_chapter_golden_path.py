"""Phase 9.67 F59: chapter production golden path tests (0 real LLM)."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from infra.agent_system.chapter_golden_path import (
    GOLDEN_WORKFLOW_NAME,
    GoldenPathResult,
    run_golden_path,
    setup_golden_workflow_dir,
)
from infra.cross_volume.incremental_backfill import maybe_after_workflow
from infra.got.data_structures import NodeExecution, NodeStatus
from infra.got.scheduler import ExecutionSummary


class TestChapterGoldenPathModule:
    def test_setup_writes_workflow_yaml(self, tmp_path):
        wf = setup_golden_workflow_dir(tmp_path)
        assert wf.is_file()
        assert GOLDEN_WORKFLOW_NAME in wf.read_text(encoding="utf-8")

    def test_golden_path_end_to_end(self, tmp_path):
        result = run_golden_path(tmp_path, chapter_num=7, resolve_option="approve")
        assert isinstance(result, GoldenPathResult)
        assert result.paused_after_run is True
        assert result.pending_count >= 1
        assert result.completed_after_resume is True
        assert result.finalize_completed is True
        assert result.decisions_json_exists is True
        assert result.memory_context_attached is True
        assert result.memory_context_source == "stub"
        assert (tmp_path / "decisions.json").is_file()

    def test_golden_path_cli_main_exit_zero(self, tmp_path):
        from infra.agent_system import chapter_golden_path as mod

        code = mod.main(
            ["--state-dir", str(tmp_path), "--chapter-num", "3"],
        )
        assert code == 0


class TestGoldenPathIncrementalBackfillOptional:
    """Documented optional step: incremental backfill after novel_writing emit."""

    def test_maybe_after_workflow_when_emit_completed(self):
        now = datetime.now(timezone.utc)
        executions = {
            "emit_chapter": NodeExecution(
                node_id="emit_chapter",
                status=NodeStatus.COMPLETED,
                started_at=now,
                finished_at=now,
                output={"chapter_num": 12},
            ),
        }
        summary = ExecutionSummary(completed=7, failed=0, paused=False)
        with patch(
            "infra.cross_volume.incremental_backfill.run_incremental_backfill",
            return_value=type("S", (), {"summary": lambda self: {"nodes_written": 1}})(),
        ):
            stats = maybe_after_workflow(
                "novel_writing",
                {"chapter_num": 12},
                executions,
                summary,
                enabled=True,
            )
        assert stats is not None

