/**
 * Workflow API client — typed wrapper around /workflows/* endpoints.
 *
 * Path convention: relative paths (no `/api/` prefix) — `core.js`'s `request()`
 * prepends `BASE_URL='/api'`.
 *
 * NOTE: This is a NEW typed wrapper added in v16.2.8 (Phase 126 cleanup).
 * Existing api/workflows.js continues to handle backward-compatible calls.
 * v16.2.8 T5 deletes api/workflows.js after consumers migrate.
 */
import { request } from './core.js';

// ---------------------------------------------------------------------------
// /workflows/list (all registered workflows)
// ---------------------------------------------------------------------------

export async function fetchWorkflows(): Promise<unknown> {
  return request('/workflows/list');
}

// ---------------------------------------------------------------------------
// /workflows/run (start a workflow by name with payload)
// ---------------------------------------------------------------------------

export async function runWorkflow(req: unknown): Promise<unknown> {
  return request('/workflows/run', { method: 'POST', body: req });
}

// ---------------------------------------------------------------------------
// /workflows/resume (resume a paused workflow at a decision point)
// ---------------------------------------------------------------------------

export async function resumeWorkflow(
  decisionId: string,
  option: string,
  resolvedBy: string = 'human',
): Promise<unknown> {
  return request('/workflows/resume', {
    method: 'POST',
    body: { decision_id: decisionId, option, resolved_by: resolvedBy },
  });
}

// ---------------------------------------------------------------------------
// /workflows/active (currently running workflow)
// ---------------------------------------------------------------------------

export async function fetchActiveWorkflow(): Promise<unknown> {
  return request('/workflows/active');
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
): Promise<unknown> {
  const params = new URLSearchParams();
  if (opts.includeStatus) params.set('include_status', 'true');
  const qs = params.toString();
  return request(`/workflows/${encodeURIComponent(workflowName)}/mermaid${qs ? `?${qs}` : ''}`);
}