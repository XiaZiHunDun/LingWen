"""Dashboard-side golden path smoke (relocated from chapter_golden_path.py).

Phase 31 ARCHDEBT-MINI: split per architecture invariant I001 spirit — keep
FastAPI/TestClient assembly in apps/, keep MC-only golden path in lingwen-core.

The MC-side helpers (build_stub_master_controller, setup_golden_workflow_dir,
run_golden_path) remain in lingwen_core.agents.chapter_golden_path.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from lingwen_core.agents.chapter_golden_path import (
    GOLDEN_WORKFLOW_NAME,
    build_stub_master_controller,
    setup_golden_workflow_dir,
)

from apps.studio_api.app import create_app
from apps.studio_api.protocols import MasterControllerAdapter


@dataclass(frozen=True)
class HumanReviewSmokeResult:
    """Dashboard API resolve → resume smoke (Phase 9.69 F61)."""

    chapter_num: int
    run_paused: bool
    pending_before_resume: int
    pending_after_resume: int
    resume_paused: bool
    decision_resolved: bool
    resolved_option: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def create_golden_dashboard_client(state_dir: Path, db_path: Path) -> Any:
    """FastAPI TestClient wired to real MC + chapter_golden workflow (0 LLM)."""
    setup_golden_workflow_dir(state_dir)
    controller = build_stub_master_controller(state_dir)
    adapter = MasterControllerAdapter(controller)
    app = create_app(db_path=db_path, master_controller=adapter)
    return TestClient(app)


def run_human_review_smoke(
    state_dir: Path,
    db_path: Path,
    *,
    chapter_num: int = 5,
    resolve_option: str = "approve",
) -> HumanReviewSmokeResult:
    """Dashboard API: run → pending → resume; raises on HTTP or invariant failure."""
    client = create_golden_dashboard_client(state_dir, db_path)

    run_resp = client.post(
        "/api/workflows/run",
        json={
            "workflow_name": GOLDEN_WORKFLOW_NAME,
            "base_dir": str(state_dir),
            "start_nodes": ["write_chapter"],
            "initial_inputs": {"chapter_num": chapter_num},
            "max_backtracks": 0,
        },
    )
    if run_resp.status_code != 200:
        raise RuntimeError(f"human review smoke: run failed {run_resp.status_code}: {run_resp.text}")
    run_body = run_resp.json()
    if not run_body.get("paused"):
        raise RuntimeError("human review smoke: expected paused workflow after run")

    pending_resp = client.get("/api/decisions/pending")
    pending_before = pending_resp.json()
    if not pending_before:
        raise RuntimeError("human review smoke: expected pending decisions before resume")
    decision_id = pending_before[0]["decision_id"]

    resume_resp = client.post(
        "/api/workflows/resume",
        json={"decision_id": decision_id, "option": resolve_option},
    )
    if resume_resp.status_code != 200:
        raise RuntimeError(f"human review smoke: resume failed {resume_resp.status_code}: {resume_resp.text}")
    resume_body = resume_resp.json()

    pending_after = client.get("/api/decisions/pending").json()
    all_decisions = client.get("/api/decisions/all").json()
    decision_resolved = any(
        d.get("decision_id") == decision_id and d.get("status") == "resolved" for d in all_decisions
    )

    return HumanReviewSmokeResult(
        chapter_num=chapter_num,
        run_paused=True,
        pending_before_resume=len(pending_before),
        pending_after_resume=len(pending_after),
        resume_paused=bool(resume_body.get("paused")),
        decision_resolved=decision_resolved,
        resolved_option=resolve_option,
    )
