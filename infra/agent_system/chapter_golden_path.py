"""Phase 9.67 F59: stub golden path for chapter production pipeline verification.

Runs a minimal DECISION-pause workflow (0 real LLM) through:
  run_workflow → pending decision → resume_workflow → completed downstream.

Used by pytest and `python -m infra.agent_system.chapter_golden_path`.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

GOLDEN_WORKFLOW_NAME = "chapter_golden"

GOLDEN_WORKFLOW_YAML = """\
workflow: chapter_golden
version: 1
nodes:
  - id: write_chapter
    type: generation
    name: Write Chapter
    description: stub write (no LLM)
    depends_on: []
  - id: outline_judgment
    type: decision
    name: Outline Judgment
    description: outline_judgment
    depends_on: [write_chapter]
  - id: finalize
    type: generation
    name: Finalize
    description: stub finalize after human approve
    depends_on: [outline_judgment]
"""


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


@dataclass(frozen=True)
class GoldenPathResult:
    """Outcome of run_golden_path (assert-friendly fields)."""

    chapter_num: int
    paused_after_run: bool
    pending_count: int
    decision_id: str
    resolved_option: str
    completed_after_resume: bool
    finalize_completed: bool
    decisions_json_exists: bool
    memory_context_attached: bool = False
    memory_context_source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def setup_golden_workflow_dir(state_dir: Path) -> Path:
    """Write chapter_golden.yaml under state_dir (idempotent)."""
    state_dir.mkdir(parents=True, exist_ok=True)
    wf_path = state_dir / f"{GOLDEN_WORKFLOW_NAME}.yaml"
    wf_path.write_text(GOLDEN_WORKFLOW_YAML, encoding="utf-8")
    return wf_path


def build_stub_master_controller(state_dir: Path) -> Any:
    """Minimal MasterController for golden path (skips __init__, 0 LLM)."""
    from infra.agent_system.decision_queue import HumanDecisionQueue
    from infra.agent_system.master_controller import MasterController

    controller = MasterController.__new__(MasterController)
    controller._decision_queue = HumanDecisionQueue(state_dir=str(state_dir))
    controller._config = None
    controller._router = None
    controller._orchestrator = None
    controller._skill_registry = None
    controller._state_manager = None
    controller._last_scheduler = None
    controller._last_graph = None
    controller._last_workflow_name = None
    controller._last_start_nodes = []
    controller._last_initial_inputs = {}
    controller._incremental_backfill_enabled = None
    controller._memory_rag_mode = "stub"
    return controller


def run_golden_path(
    state_dir: Path,
    *,
    chapter_num: int = 5,
    resolve_option: str = "approve",
) -> GoldenPathResult:
    """Execute stub golden path; raises on invariant violation."""
    from infra.got.data_structures import NodeStatus

    setup_golden_workflow_dir(state_dir)
    controller = build_stub_master_controller(state_dir)

    run1 = controller.run_workflow(
        workflow_name=GOLDEN_WORKFLOW_NAME,
        base_dir=str(state_dir),
        start_nodes=["write_chapter"],
        initial_inputs={"chapter_num": chapter_num},
        max_backtracks=0,
    )
    summary1 = run1["summary"]
    pending = run1.get("pending_decisions") or []
    if not summary1.paused:
        raise RuntimeError("golden path: expected paused workflow after first run")
    if not pending:
        raise RuntimeError("golden path: expected pending_decisions after harvest")

    decision_id = pending[0]["decision_id"]
    run2 = controller.resume_workflow(decision_id, resolve_option)
    summary2 = run2["summary"]
    graph = run2["graph"]
    finalize_exec = graph.get_execution("finalize")
    finalize_ok = (
        finalize_exec is not None
        and finalize_exec.status == NodeStatus.COMPLETED
    )
    decisions_path = state_dir / "decisions.json"
    memory_ctx = controller._last_initial_inputs.get("memory_context") or {}
    memory_attached = bool(memory_ctx)
    memory_source = memory_ctx.get("source") if memory_ctx else None

    return GoldenPathResult(
        chapter_num=chapter_num,
        paused_after_run=True,
        pending_count=len(pending),
        decision_id=decision_id,
        resolved_option=resolve_option,
        completed_after_resume=summary2.paused is False,
        finalize_completed=finalize_ok,
        decisions_json_exists=decisions_path.is_file(),
        memory_context_attached=memory_attached,
        memory_context_source=memory_source,
    )


def create_golden_dashboard_client(state_dir: Path, db_path: Path) -> Any:
    """FastAPI TestClient wired to real MC + chapter_golden workflow (0 LLM)."""
    from fastapi.testclient import TestClient

    from dashboard.app import create_app
    from dashboard.protocols import MasterControllerAdapter

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
        raise RuntimeError(
            f"human review smoke: run failed {run_resp.status_code}: {run_resp.text}"
        )
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
        raise RuntimeError(
            f"human review smoke: resume failed {resume_resp.status_code}: {resume_resp.text}"
        )
    resume_body = resume_resp.json()

    pending_after = client.get("/api/decisions/pending").json()
    all_decisions = client.get("/api/decisions/all").json()
    decision_resolved = any(
        d.get("decision_id") == decision_id and d.get("status") == "resolved"
        for d in all_decisions
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


def main(argv: list[str] | None = None) -> int:
    import argparse
    import tempfile

    parser = argparse.ArgumentParser(
        description="Run chapter production golden path (stub, 0 LLM)",
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="infra/.state subdir (default: temp dir)",
    )
    parser.add_argument("--chapter-num", type=int, default=5)
    parser.add_argument("--resolve-option", default="approve")
    args = parser.parse_args(argv)

    state_dir = args.state_dir
    if state_dir is None:
        state_dir = Path(tempfile.mkdtemp(prefix="lingwen-golden-")) / "state"
    result = run_golden_path(
        state_dir,
        chapter_num=args.chapter_num,
        resolve_option=args.resolve_option,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.completed_after_resume and result.finalize_completed else 1


if __name__ == "__main__":
    raise SystemExit(main())

