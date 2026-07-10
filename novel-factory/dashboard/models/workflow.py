"""
Phase 15.0 T1.1: Pydantic models split from dashboard/app.py (workflow domain).

Models unchanged — only relocated for code organization.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class WorkflowListItem(BaseModel):
    """工作流列表项"""
    name: str
    path: str
    node_count: int
    has_decision_nodes: bool

class RunWorkflowRequest(BaseModel):
    """运行工作流请求"""
    workflow_name: str
    initial_inputs: Optional[dict[str, Any]] = None
    start_nodes: Optional[list[str]] = None
    max_backtracks: int = 2
    base_dir: Optional[str] = None
    cost_budget_usd: Optional[float] = None  # Phase 8.8: budget alarm (None=unlimited)

class ResumeWorkflowRequest(BaseModel):
    """恢复工作流请求"""
    decision_id: str
    option: str
    resolved_by: str = "human"
    # Phase 8.8: 字段保留 (前端可传),但 master.resume_workflow 当前不接 (T3 留 followup)
    # 透传后 _current_budget_usd 仍为 None,resumed run 不受新 budget 影响
    cost_budget_usd: Optional[float] = None  # Phase 8.8: budget alarm (None=清空 budget)

class BudgetSetRequest(BaseModel):
    """Phase 8.12 T5: 设置 day/week budget (per-run 不暴露, run 启动时传)"""
    usd: float = Field(ge=0, le=10000)  # 0 表示"无限但仍写行 0"

class BudgetTierSetRequest(BaseModel):
    """Phase 8.15 T6: 设置 tier budget (haiku/sonnet/opus 各自)."""
    usd: float = Field(ge=0, le=10000)  # 0 表示"无限但仍写行 0"

class WorkflowStatusResponse(BaseModel):
    """工作流状态响应"""
    workflow_name: Optional[str] = None
    is_active: bool = False
    completed: int = 0
    failed: int = 0
    paused: bool = False
    paused_nodes: list[str] = Field(default_factory=list)
    node_count: int = 0
    steps: int = 0
    total_cost_usd: float = 0.0  # Phase 8.5: 0.0 if no cost_tracker wired
    pending_decisions: list[dict[str, Any]] = Field(default_factory=list)
    executions: dict[str, str] = Field(default_factory=dict)  # Phase 6.6.D
    score_data: dict[str, dict[str, Any]] = Field(default_factory=dict)  # Phase 7.6: S1-S8 评分数据
    cost_by_scenario: dict[str, float] = Field(default_factory=dict)  # Phase 8.7: by-scenario 累计 USD
    cost_by_tier: dict[str, float] = Field(default_factory=dict)  # Phase 8.13: by-tier 累计 USD (haiku/sonnet/opus)
    cost_by_day: dict[str, float] = Field(default_factory=dict)  # Phase 8.23: trend chart data (YYYY-MM-DD → USD)
    cost_by_day_per_tier: dict[str, dict[str, float]] = Field(  # Phase 9.28 F12
        default_factory=dict
    )
    cost_budget_status: dict[str, Any] = Field(default_factory=dict)  # Phase 8.8 T5: budget alarm 状态
    # Phase 8.12 T5 NEW: per-day / per-week budget status (per-run 仍走 cost_budget_status 旧 path)
    budget_per_day: dict[str, Any] = Field(default_factory=dict)
    budget_per_week: dict[str, Any] = Field(default_factory=dict)
    # Phase 8.15 T6 NEW: per-tier budget status (haiku/sonnet/opus, 跟 run/day/week 完全 orthogonal)
    budget_by_tier: dict[str, dict[str, Any] | None] = Field(default_factory=dict)
    # Phase 9.68 F60: incremental CVG backfill stats after novel_writing (null = skipped/disabled)
    incremental_backfill: dict[str, Any] | None = None
    # Phase 9.74 F66: per-run chapter production summary (chapter_num + memory + backfill)
    production_summary: dict[str, Any] | None = None

class WorkflowMermaidResponse(BaseModel):
    """工作流 mermaid 图响应 (Phase 6.3 + 6.6.D)"""
    workflow_name: str
    mermaid: str
    node_count: int
    has_decision_nodes: bool
    status_applied: bool = False  # Phase 6.6.D: true = 染色基于 active workflow
    node_statuses: dict[str, str] = Field(default_factory=dict)  # Phase 6.6.D
