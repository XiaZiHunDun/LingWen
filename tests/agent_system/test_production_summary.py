"""Phase 9.74 F66: production_summary builder tests."""
from __future__ import annotations

from datetime import datetime, timezone

from infra.agent_system.production_summary import (
    build_production_summary,
    build_production_summary_from_controller,
)
from infra.got.data_structures import NodeExecution, NodeStatus


class TestBuildProductionSummary:
    def test_novel_writing_full_summary(self):
        now = datetime.now(timezone.utc)
        executions = {
            "emit_chapter": NodeExecution(
                node_id="emit_chapter",
                status=NodeStatus.COMPLETED,
                started_at=now,
                finished_at=now,
                output={"chapter_num": 360},
            ),
        }
        summary = build_production_summary(
            workflow_name="novel_writing",
            initial_inputs={"chapter_num": 360, "memory_context": {"source": "stub"}},
            executions=executions,
            incremental_backfill={"nodes_written": 1, "total_count": 1},
            memory_context={"source": "stub"},
        )
        assert summary is not None
        assert summary["chapter_num"] == 360
        assert summary["memory_context_source"] == "stub"
        assert summary["emit_chapter_completed"] is True
        assert summary["incremental_backfill"]["nodes_written"] == 1

    def test_non_chapter_workflow_returns_none(self):
        assert build_production_summary(
            workflow_name="other_flow",
            initial_inputs={},
            executions={},
            incremental_backfill=None,
        ) is None

    def test_serialized_executions_dict(self):
        summary = build_production_summary(
            workflow_name="novel_writing",
            initial_inputs={"chapter_num": 5},
            executions={"emit_chapter": {"status": "completed"}},
            incremental_backfill=None,
        )
        assert summary is not None
        assert summary["chapter_num"] == 5
        assert summary["emit_chapter_completed"] is True


class TestBuildProductionSummaryFromController:
    def test_reads_last_cache(self):
        class _Graph:
            def node_ids(self):
                return ["emit_chapter"]

            def has_execution(self, nid):
                return True

            def get_execution(self, nid):
                now = datetime.now(timezone.utc)
                return NodeExecution(
                    node_id=nid,
                    status=NodeStatus.COMPLETED,
                    started_at=now,
                    finished_at=now,
                    output={"chapter_num": 12},
                )

        class _Controller:
            _last_graph = _Graph()
            _last_workflow_name = "novel_writing"
            _last_initial_inputs = {"chapter_num": 12}
            _last_incremental_backfill = None
            _last_memory_context = {"source": "live"}

        result = build_production_summary_from_controller(_Controller())
        assert result is not None
        assert result["chapter_num"] == 12
        assert result["memory_context_source"] == "live"
