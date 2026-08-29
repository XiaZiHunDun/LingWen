// Phase 126 v16.5 #7: Workflows DTOs (manually declared, not codegen).
//
// Wraps endpoints:
//   GET /workflows/list, /workflows/active, /workflows/{name}/mermaid
//   POST /workflows/run, /workflows/resume
//
// Source: apps/studio_api/models/workflow.py
//
// v16.5 #N carryover: regenerate via tooling/contracts/generate.py
// after Python Pydantic DTOs are added to packages/lingwen-shared.

export interface WorkflowListItemDTO {
  name: string;
  path: string;
  node_count: number;
  has_decision_nodes: boolean;
}

export interface RunWorkflowRequestDTO {
  workflow_name: string;
  initial_inputs?: Record<string, unknown> | null;
  start_nodes?: string[] | null;
  max_backtracks?: number;
  base_dir?: string | null;
  cost_budget_usd?: number | null;
}

export interface ResumeWorkflowRequestDTO {
  decision_id: string;
  option: string;
  resolved_by?: string;
  cost_budget_usd?: number | null;
}

export interface WorkflowStatusResponseDTO {
  workflow_name?: string | null;
  is_active?: boolean;
  completed?: number;
  failed?: number;
  paused?: boolean;
  paused_nodes?: string[];
  node_count?: number;
  steps?: number;
  total_cost_usd?: number;
  pending_decisions?: Record<string, unknown>[];
  executions?: Record<string, string>;
  score_data?: Record<string, Record<string, unknown>>;
  cost_by_scenario?: Record<string, number>;
  cost_by_tier?: Record<string, number>;
  cost_by_day?: Record<string, number>;
  cost_by_day_per_tier?: Record<string, Record<string, number>>;
  cost_budget_status?: Record<string, unknown>;
  budget_per_day?: Record<string, unknown>;
  budget_per_week?: Record<string, unknown>;
  budget_by_tier?: Record<string, Record<string, unknown> | null>;
  incremental_backfill?: Record<string, unknown> | null;
  production_summary?: Record<string, unknown> | null;
}

export interface WorkflowMermaidResponseDTO {
  workflow_name: string;
  mermaid: string;
  node_count: number;
  has_decision_nodes: boolean;
  status_applied?: boolean;
  node_statuses?: Record<string, string>;
}
