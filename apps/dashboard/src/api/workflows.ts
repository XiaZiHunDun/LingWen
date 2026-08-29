/**
 * Workflow API client — typed wrapper around /workflows/* endpoints.
 *
 * Path convention: relative paths (no `/api/` prefix) — `core.js`'s `request()`
 * prepends `BASE_URL='/api'`.
 *
 * NOTE: This is a NEW typed wrapper added in v16.2.8 (Phase 126 cleanup).
 * Existing api/workflows.js continues to handle backward-compatible calls.
 * v16.2.8 T5 deletes api/workflows.js after consumers migrate.
 *
 * v16.5 #7: Promise<unknown> narrowed to concrete DTO types declared in
 * @lingwen/dashboard-contracts/shared/workflows.
 */
import type {
  WorkflowListItemDTO,
  WorkflowMermaidResponseDTO,
  WorkflowStatusResponseDTO,
} from '@lingwen/dashboard-contracts/shared';
import { request } from './core.js';

// ---------------------------------------------------------------------------
// /workflows/list (all registered workflows)
// ---------------------------------------------------------------------------

export async function fetchWorkflows(): Promise<WorkflowListItemDTO[]> {
  const data = await request('/workflows/list');
  return data as WorkflowListItemDTO[];
}

// ---------------------------------------------------------------------------
// /workflows/run (start a workflow by name with payload)
// ---------------------------------------------------------------------------

export interface RunWorkflowInput {
  workflow_name: string;
  initial_inputs?: Record<string, unknown>;
  start_nodes?: string[];
  max_backtracks?: number;
  base_dir?: string;
  cost_budget_usd?: number;
}

export async function runWorkflow(req: RunWorkflowInput): Promise<WorkflowStatusResponseDTO> {
  const data = await request('/workflows/run', { method: 'POST', body: req });
  return data as WorkflowStatusResponseDTO;
}

// ---------------------------------------------------------------------------
// /workflows/resume (resume a paused workflow at a decision point)
// ---------------------------------------------------------------------------

export async function resumeWorkflow(
  decisionId: string,
  option: string,
  resolvedBy: string = 'human',
): Promise<WorkflowStatusResponseDTO> {
  const data = await request('/workflows/resume', {
    method: 'POST',
    body: { decision_id: decisionId, option, resolved_by: resolvedBy },
  });
  return data as WorkflowStatusResponseDTO;
}

// ---------------------------------------------------------------------------
// /workflows/active (currently running workflow)
// ---------------------------------------------------------------------------

export async function fetchActiveWorkflow(): Promise<WorkflowStatusResponseDTO> {
  const data = await request('/workflows/active');
  return data as WorkflowStatusResponseDTO;
}

// ---------------------------------------------------------------------------
// /workflows/{name}/mermaid (mermaid graph definition)
// ---------------------------------------------------------------------------

export interface WorkflowGraphOptions {
  includeStatus?: boolean;
}

export async function fetchWorkflowGraph(
  workflowName: string,
  opts: WorkflowGraphOptions = {},
): Promise<WorkflowMermaidResponseDTO> {
  const params = new URLSearchParams();
  if (opts.includeStatus) params.set('include_status', 'true');
  const qs = params.toString();
  const data = await request(
    `/workflows/${encodeURIComponent(workflowName)}/mermaid${qs ? `?${qs}` : ''}`,
  );
  return data as WorkflowMermaidResponseDTO;
}
