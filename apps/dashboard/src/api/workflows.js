/**
 * Workflow API
 */

import { request } from './core.js';

export async function fetchWorkflows() {
  return request('/workflows/list');
}

export async function runWorkflow(req) {
  return request('/workflows/run', { method: 'POST', body: req });
}

export async function resumeWorkflow(decisionId, option, resolvedBy = 'human') {
  return request('/workflows/resume', {
    method: 'POST',
    body: { decision_id: decisionId, option, resolved_by: resolvedBy },
  });
}

export async function fetchActiveWorkflow() {
  return request('/workflows/active');
}

export async function fetchWorkflowGraph(workflowName, opts = {}) {
  const params = new URLSearchParams();
  if (opts.includeStatus) params.set('include_status', 'true');
  const qs = params.toString();
  return request(`/workflows/${encodeURIComponent(workflowName)}/mermaid${qs ? `?${qs}` : ''}`);
}