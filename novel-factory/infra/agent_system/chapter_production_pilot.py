"""Phase 9.73 F65: real chapter production pilot (1 chapter, opt-in).

Gate: LINGWEN_REAL_LLM=1 (never default in CI).
Recommended env for production pilot:
  LINGWEN_REAL_LLM=1
  LINGWEN_INCREMENTAL_BACKFILL=1
  LINGWEN_MEMORY_RAG=live|stub

CLI:
  python -m infra.agent_system.chapter_production_pilot --preflight-only
  python -m infra.agent_system.chapter_production_pilot --chapter-num 360
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from infra.agent_system.agent_config import DEFAULT_STATE_DIR, load_default_config
from infra.agent_system.chapter_memory_hook import resolve_memory_rag_mode
from infra.cross_volume.incremental_backfill import incremental_backfill_enabled

PILOT_WORKFLOW_NAME = "novel_writing"
_PROVIDER_ENV_KEYS: tuple[tuple[str, str], ...] = (
    ("minimax", "MINIMAX_API_KEY"),
    ("anthropic", "ANTHROPIC_API_KEY"),
    ("openai", "OPENAI_API_KEY"),
)
_NOVEL_WRITING_YAML = (
    Path(__file__).resolve().parents[1] / "got" / "workflows" / "novel_writing.yaml"
)

PRODUCTION_PILOT_BEHAVIOR: tuple[dict[str, str], ...] = (
    {
        "trigger": "env LINGWEN_REAL_LLM",
        "behavior": "1/true/yes required to run pilot (default off; CI never sets)",
    },
    {
        "trigger": "workflow",
        "behavior": "novel_writing (7 nodes, no DECISION pause — runs to emit_chapter)",
    },
    {
        "trigger": "hooks",
        "behavior": "LINGWEN_INCREMENTAL_BACKFILL + LINGWEN_MEMORY_RAG from env",
    },
    {
        "trigger": "record",
        "behavior": "PilotResult JSON — cost, backfill, memory source, summary counts",
    },
)


def real_llm_enabled(explicit: bool | None = None) -> bool:
    """Opt-in gate for real LLM pilot runs (default off)."""
    if explicit is not None:
        return explicit
    return os.environ.get("LINGWEN_REAL_LLM", "").lower() in ("1", "true", "yes")


def detect_available_provider() -> str | None:
    """Return first configured provider (minimax > anthropic > openai)."""
    for name, env_key in _PROVIDER_ENV_KEYS:
        if os.environ.get(env_key, "").strip():
            return name
    return None


@dataclass(frozen=True)
class PreflightCheck:
    name: str
    passed: bool
    message: str
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PilotResult:
    chapter_num: int
    workflow_name: str
    provider: str | None
    preflight_ok: bool
    preflight_checks: list[PreflightCheck] = field(default_factory=list)
    paused: bool = False
    pending_count: int = 0
    completed: int = 0
    failed: int = 0
    emit_chapter_completed: bool = False
    total_cost_usd: float | None = None
    incremental_backfill: dict[str, Any] | None = None
    memory_context_source: str | None = None
    memory_rag_mode: str = "off"
    incremental_backfill_enabled: bool = False
    real_llm_gate: bool = False
    preflight_only: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["preflight_checks"] = [c.to_dict() for c in self.preflight_checks]
        return data


def build_pilot_initial_inputs(
    chapter_num: int,
    *,
    outline: dict[str, Any] | None = None,
    word_count_target: int = 800,
) -> dict[str, Any]:
    """Minimal novel_writing seed inputs (short chapter for pilot cost control)."""
    if outline is None:
        outline = {
            "chapters": [{
                "num": chapter_num,
                "title": f"第{chapter_num}章 pilot",
                "events": ["pilot_event_1"],
                "word_count_target": word_count_target,
            }],
        }
    return {
        "chapter_num": chapter_num,
        "outline": outline,
        "characters": [],
        "memory_context": {},
        "style_guide": {},
        "timeline": [],
        "use_llm": True,
    }


def preflight_checklist(
    *,
    state_dir: Path | None = None,
    chapter_num: int = 1,
    require_real_llm_gate: bool = True,
) -> list[PreflightCheck]:
    """Production checklist before a real LLM chapter pilot."""
    checks: list[PreflightCheck] = []

    gate_ok = real_llm_enabled()
    checks.append(PreflightCheck(
        name="real_llm_gate",
        passed=gate_ok or not require_real_llm_gate,
        message=(
            "LINGWEN_REAL_LLM=1 set"
            if gate_ok
            else "set LINGWEN_REAL_LLM=1 to opt in (never in default CI)"
        ),
        required=require_real_llm_gate,
    ))

    provider = detect_available_provider()
    checks.append(PreflightCheck(
        name="api_key",
        passed=provider is not None,
        message=(
            f"provider={provider} key present"
            if provider
            else "set MINIMAX_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY"
        ),
    ))

    resolved_dir = Path(state_dir or DEFAULT_STATE_DIR)
    try:
        resolved_dir.mkdir(parents=True, exist_ok=True)
        probe = resolved_dir / ".pilot_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        dir_ok, dir_msg = True, f"state_dir writable: {resolved_dir}"
    except OSError as exc:
        dir_ok, dir_msg = False, f"state_dir not writable: {resolved_dir} ({exc})"
    checks.append(PreflightCheck(name="state_dir", passed=dir_ok, message=dir_msg))

    wf_ok = _NOVEL_WRITING_YAML.is_file()
    checks.append(PreflightCheck(
        name="workflow_yaml",
        passed=wf_ok,
        message=(
            f"found {_NOVEL_WRITING_YAML.name}"
            if wf_ok
            else f"missing {_NOVEL_WRITING_YAML}"
        ),
    ))

    try:
        cfg = load_default_config(state_dir=str(resolved_dir))
        config_ok = bool(cfg.providers)
        config_msg = f"primary_provider={cfg.primary_provider}"
    except RuntimeError as exc:
        config_ok = False
        config_msg = str(exc)
    checks.append(PreflightCheck(
        name="master_controller_config",
        passed=config_ok,
        message=config_msg,
    ))

    mem_mode = resolve_memory_rag_mode()
    if mem_mode == "live":
        qdrant_hint = os.environ.get("QDRANT_URL") or os.environ.get("QDRANT_HOST")
        checks.append(PreflightCheck(
            name="memory_rag_live",
            passed=True,
            message=(
                "LINGWEN_MEMORY_RAG=live; Qdrant env detected"
                if qdrant_hint
                else "LINGWEN_MEMORY_RAG=live; QDRANT_URL unset — may fall back or fail at runtime"
            ),
            required=False,
        ))
    else:
        checks.append(PreflightCheck(
            name="memory_rag_mode",
            passed=True,
            message=f"LINGWEN_MEMORY_RAG={mem_mode or 'off'} (stub recommended for first pilot)",
            required=False,
        ))

    backfill_on = incremental_backfill_enabled()
    checks.append(PreflightCheck(
        name="incremental_backfill",
        passed=True,
        message=(
            "LINGWEN_INCREMENTAL_BACKFILL enabled"
            if backfill_on
            else "LINGWEN_INCREMENTAL_BACKFILL off (optional for pilot)"
        ),
        required=False,
    ))

    if chapter_num < 1:
        checks.append(PreflightCheck(
            name="chapter_num",
            passed=False,
            message=f"chapter_num must be >= 1, got {chapter_num}",
        ))

    return checks


def preflight_ok(checks: list[PreflightCheck]) -> bool:
    return all(c.passed for c in checks if c.required)


def configure_pilot_hooks(master: Any) -> None:
    """Apply env-driven hooks on MasterController before run_workflow."""
    mem_mode = resolve_memory_rag_mode()
    if mem_mode != "off":
        master._memory_rag_mode = mem_mode
    if incremental_backfill_enabled():
        master._incremental_backfill_enabled = True


def run_production_pilot(
    *,
    chapter_num: int = 1,
    state_dir: Path | None = None,
    preflight_only: bool = False,
    cost_budget_usd: float | None = None,
    max_backtracks: int = 0,
) -> PilotResult:
    """Run (or preflight-only) one real-LLM chapter pilot."""
    checks = preflight_checklist(
        state_dir=state_dir,
        chapter_num=chapter_num,
        require_real_llm_gate=not preflight_only,
    )
    mem_mode = resolve_memory_rag_mode()
    backfill_on = incremental_backfill_enabled()
    provider = detect_available_provider()

    result = PilotResult(
        chapter_num=chapter_num,
        workflow_name=PILOT_WORKFLOW_NAME,
        provider=provider,
        preflight_ok=preflight_ok(checks),
        preflight_checks=checks,
        memory_rag_mode=mem_mode,
        incremental_backfill_enabled=backfill_on,
        real_llm_gate=real_llm_enabled(),
        preflight_only=preflight_only,
    )

    if preflight_only:
        return result

    if not result.preflight_ok:
        result.error = "preflight failed; fix checklist before running pilot"
        return result

    from infra.agent_system.master_controller import MasterController
    from infra.ai_service.cost_tracker import CostTracker
    from infra.got.data_structures import NodeStatus

    resolved_dir = Path(state_dir or DEFAULT_STATE_DIR)
    cost_tracker = CostTracker()
    master = MasterController(
        state_dir=str(resolved_dir),
        cost_tracker=cost_tracker,
    )
    configure_pilot_hooks(master)

    try:
        run_out = master.run_workflow(
            workflow_name=PILOT_WORKFLOW_NAME,
            initial_inputs=build_pilot_initial_inputs(chapter_num),
            cost_budget_usd=cost_budget_usd,
            max_backtracks=max_backtracks,
        )
    except Exception as exc:
        result.error = str(exc)
        return result

    summary = run_out["summary"]
    executions = run_out.get("executions") or {}
    emit_exec = executions.get("emit_chapter")
    emit_ok = (
        emit_exec is not None
        and emit_exec.status == NodeStatus.COMPLETED
    )
    mem_ctx = run_out.get("memory_context") or master._last_initial_inputs.get(
        "memory_context", {},
    )

    result.paused = bool(summary.paused)
    result.pending_count = len(run_out.get("pending_decisions") or [])
    result.completed = summary.completed
    result.failed = summary.failed
    result.emit_chapter_completed = emit_ok
    result.incremental_backfill = run_out.get("incremental_backfill")
    result.memory_context_source = (
        mem_ctx.get("source") if isinstance(mem_ctx, dict) else None
    )
    result.total_cost_usd = cost_tracker.total_cost()
    result.provider = master._config.primary_provider if master._config else provider
    return result


def describe_production_pilot() -> list[dict[str, str]]:
    """Runbook / CI sync table."""
    return list(PRODUCTION_PILOT_BEHAVIOR)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Real chapter production pilot (requires LINGWEN_REAL_LLM=1)",
    )
    parser.add_argument("--chapter-num", type=int, default=1)
    parser.add_argument("--state-dir", type=Path, default=None)
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Run checklist only (no LLM, no gate required)",
    )
    parser.add_argument("--cost-budget-usd", type=float, default=None)
    args = parser.parse_args(argv)

    result = run_production_pilot(
        chapter_num=args.chapter_num,
        state_dir=args.state_dir,
        preflight_only=args.preflight_only,
        cost_budget_usd=args.cost_budget_usd,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

    if args.preflight_only:
        return 0 if result.preflight_ok else 1
    if result.error:
        return 2
    if result.failed > 0 or not result.emit_chapter_completed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
