"""
Phase 15.0 T1.3: workflow + workflow result helpers.

Extracted from dashboard/app.py (lines 304-356 + 4286-4346). Unchanged.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from dashboard.models import WorkflowListItem, WorkflowStatusResponse


def _list_workflow_yamls() -> list[WorkflowListItem]:
    """扫描 infra/got/workflows/*.yaml → WorkflowListItem 列表

    简化:不调 workflow_loader,只读 YAML 文本粗略统计
    - node_count: text 中 `- id:` 出现次数
    - has_decision_nodes: text 中是否含 `type: decision`
    """
    wf_dir = Path(__file__).parent.parent.parent / "infra" / "got" / "workflows"
    if not wf_dir.exists():
        return []
    items: list[WorkflowListItem] = []
    for yaml_path in sorted(wf_dir.glob("*.yaml")):
        try:
            text = yaml_path.read_text(encoding="utf-8")
        except OSError:
            continue
        node_count = text.count("- id:")
        has_decision = "type: decision" in text
        items.append(
            WorkflowListItem(
                name=yaml_path.stem,
                path=str(yaml_path.relative_to(wf_dir.parent.parent)),
                node_count=node_count,
                has_decision_nodes=has_decision,
            )
        )
    return items


def _workflow_result_to_response(
    result: dict[str, Any],
    score_data: dict[str, dict[str, Any]] | None = None,
    cost_by_scenario: dict[str, float] | None = None,  # Phase 8.7
    cost_by_tier: dict[str, float] | None = None,  # Phase 8.13
    cost_by_day: dict[str, float] | None = None,  # Phase 8.23
    cost_by_day_per_tier: dict[str, dict[str, float]] | None = None,  # Phase 9.28 F12
    total_cost_usd: float = 0.0,  # Phase 8.7: 修 Phase 8.5 gap
    budget_by_tier: dict[str, dict[str, Any] | None] | None = None,  # Phase 8.15 T5
) -> WorkflowStatusResponse:
    """run_workflow / resume_workflow 返回 dict → WorkflowStatusResponse

    summary 可能是 dict (adapter 转换后) 或 dataclass (测试 stub 直接返回)

    Phase 8.7: 修 Phase 8.5 gap — 显式接 cost_by_scenario + total_cost_usd params
    透传到 response (不再 hardcoded 0)
    Phase 8.13: 增 cost_by_tier param (additive, default None → empty dict)
    Phase 8.15 T5: 增 budget_by_tier param (additive, default None → empty dict).
    Pydantic v2 默认 extra='ignore', 未在 model 注册的 field 静默忽略; T6 会
    在 WorkflowStatusResponse 加 budget_by_tier Field (Task 6 范围).
    Phase 8.23: 增 cost_by_day param (additive, default None → empty dict)
    给 dashboard trend chart.
    Phase 9.28 F12: 增 cost_by_day_per_tier param (day × tier cross-dim).
    """
    summary = result.get("summary") or {}
    if not isinstance(summary, dict):
        # dataclass → 用 getattr
        paused_nodes = list(getattr(summary, "paused_nodes", []) or [])
        summary_dict = {
            "completed": getattr(summary, "completed", 0),
            "failed": getattr(summary, "failed", 0),
            "paused": getattr(summary, "paused", False),
            "paused_nodes": paused_nodes,
            "node_count": getattr(summary, "node_count", 0),
            "steps": getattr(summary, "steps", 0),
        }
    else:
        summary_dict = summary
    executions = result.get("executions") or {}
    paused_nodes = list(summary_dict.get("paused_nodes", []))
    return WorkflowStatusResponse(
        workflow_name=result.get("workflow_name"),
        is_active=True,
        completed=int(summary_dict.get("completed", 0)),
        failed=int(summary_dict.get("failed", 0)),
        paused=bool(summary_dict.get("paused", False)),
        paused_nodes=paused_nodes,
        node_count=int(summary_dict.get("node_count", len(executions))),
        steps=int(summary_dict.get("steps", 0)),
        pending_decisions=list(result.get("pending_decisions", [])),
        score_data=score_data or {},
        cost_by_scenario=cost_by_scenario or {},  # Phase 8.7
        cost_by_tier=cost_by_tier or {},  # Phase 8.13
        cost_by_day=cost_by_day or {},  # Phase 8.23
        cost_by_day_per_tier=cost_by_day_per_tier or {},  # Phase 9.28 F12
        total_cost_usd=total_cost_usd,  # Phase 8.7: 修 Phase 8.5 gap
        budget_by_tier=budget_by_tier or {},  # Phase 8.15 T5 (Pydantic 暂 ignore, T6 补 model Field)
        incremental_backfill=result.get("incremental_backfill"),  # Phase 9.68 F60
        production_summary=result.get("production_summary"),  # Phase 9.74 F66
    )

