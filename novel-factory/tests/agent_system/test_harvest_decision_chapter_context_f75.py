"""Phase 9.83 F75: harvest decision context includes chapter_num."""
from __future__ import annotations

from pathlib import Path

from infra.agent_system.chapter_golden_path import (
    GOLDEN_WORKFLOW_NAME,
    build_stub_master_controller,
    setup_golden_workflow_dir,
)


class TestHarvestDecisionChapterContextF75:
    def test_pending_decision_context_has_chapter_num(self, tmp_path: Path) -> None:
        setup_golden_workflow_dir(tmp_path)
        controller = build_stub_master_controller(tmp_path)
        run_out = controller.run_workflow(
            workflow_name=GOLDEN_WORKFLOW_NAME,
            base_dir=str(tmp_path),
            start_nodes=["write_chapter"],
            initial_inputs={"chapter_num": 12},
            max_backtracks=0,
        )
        pending = run_out.get("pending_decisions") or []
        assert pending
        assert pending[0]["context"].get("chapter_num") == 12
