"""Phase 9.69 F61: human review loop smoke — Dashboard resolve → resume (0 LLM)."""
from __future__ import annotations

from pathlib import Path

from infra.agent_system.chapter_golden_path import (
    HumanReviewSmokeResult,
    run_golden_path,
    run_human_review_smoke,
)


class TestHumanReviewSmokeMc:
    """MC-level golden path (F59) still covers run → resume in-process."""

    def test_golden_path_covers_mc_resume(self, tmp_path: Path) -> None:
        result = run_golden_path(tmp_path, chapter_num=9, resolve_option="approve")
        assert result.completed_after_resume is True
        assert result.finalize_completed is True


class TestHumanReviewSmokeDashboard:
    """Dashboard API smoke: POST run → GET pending → POST resume."""

    def test_full_resolve_resume_smoke(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "state"
        db_path = tmp_path / "rp.db"
        result = run_human_review_smoke(
            state_dir, db_path, chapter_num=11, resolve_option="approve"
        )
        assert isinstance(result, HumanReviewSmokeResult)
        assert result.run_paused is True
        assert result.pending_before_resume >= 1
        assert result.pending_after_resume == 0
        assert result.resume_paused is False
        assert result.decision_resolved is True

    def test_smoke_repeatable_on_fresh_state(self, tmp_path: Path) -> None:
        for i in range(2):
            sub = tmp_path / f"run{i}"
            result = run_human_review_smoke(
                sub / "state", sub / "rp.db", chapter_num=3 + i
            )
            assert result.decision_resolved is True
            assert result.pending_after_resume == 0

    def test_active_workflow_not_paused_after_resume(self, tmp_path: Path) -> None:
        from infra.agent_system.chapter_golden_path import create_golden_dashboard_client

        state_dir = tmp_path / "state"
        client = create_golden_dashboard_client(state_dir, tmp_path / "rp.db")
        client.post(
            "/api/workflows/run",
            json={
                "workflow_name": "chapter_golden",
                "base_dir": str(state_dir),
                "start_nodes": ["write_chapter"],
                "initial_inputs": {"chapter_num": 4},
                "max_backtracks": 0,
            },
        )
        pending = client.get("/api/decisions/pending").json()
        client.post(
            "/api/workflows/resume",
            json={
                "decision_id": pending[0]["decision_id"],
                "option": "approve",
            },
        )
        active = client.get("/api/workflows/active").json()
        assert active.get("is_active") is True
        assert active.get("paused") is False
