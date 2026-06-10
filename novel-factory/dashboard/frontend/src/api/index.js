/**
 * API Client for LingWen Dashboard
 * Communicates with FastAPI backend on port 8765
 *
 * Phase 6.2 扩展:
 * - 决策 API:pendingDecisions, allDecisions, resolveDecision, deferDecision, cancelDecision
 * - 工作流 API:listWorkflows, runWorkflow, resumeWorkflow, activeWorkflow
 * - request() helper 支持 method + body
 */

const BASE_URL = 'http://localhost:8765/api';

/**
 * Make a request to the API with error handling
 * @param {string} path - API endpoint path
 * @param {object} [opts] - { method, body }
 * @returns {Promise<any>} Response JSON
 * @throws {Error} Descriptive error on failure
 */
async function request(path, opts = {}) {
  const { method = 'GET', body } = opts;
  const fetchOpts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body !== undefined) {
    fetchOpts.body = typeof body === 'string' ? body : JSON.stringify(body);
  }
  try {
    const response = await fetch(`${BASE_URL}${path}`, fetchOpts);

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      throw new Error(`API Error ${response.status}: ${response.statusText}. Details: ${errorText}`);
    }

    return response.json();
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(`Network error: Unable to connect to ${BASE_URL}. Is the server running?`);
    }
    throw error;
  }
}

// === Reading Power (Phase 1-3) ===

/**
 * Fetch overview data from the API
 * @returns {Promise<OverviewResponse>} Overview data
 */
export async function fetchOverview() {
  return request('/overview');
}

/**
 * Fetch chapters data from the API
 * @param {string} [range] - Optional range filter (e.g., "1-50")
 * @returns {Promise<ChaptersResponse>} Chapters data
 */
export async function fetchChapters(range) {
  const query = range ? `?range=${encodeURIComponent(range)}` : '';
  return request(`/chapters${query}`);
}

/**
 * Fetch health status from the API
 * @returns {Promise<HealthResponse>} Health data
 */
export async function fetchHealth() {
  return request('/health');
}

// === Decisions (Phase 6.2) ===

/**
 * 列出 PENDING 决策 (按 priority desc + due_at asc 排序)
 * @returns {Promise<Array<DecisionResponse>>}
 */
export async function fetchPendingDecisions() {
  return request('/decisions/pending');
}

/**
 * 列出全部决策 (含 RESOLVED/DEFERRED/CANCELLED)
 * @returns {Promise<Array<DecisionResponse>>}
 */
export async function fetchAllDecisions() {
  return request('/decisions/all');
}

/**
 * 解决决策 (PENDING → RESOLVED)
 * @param {string} decisionId
 * @param {string} option
 * @param {string} [resolvedBy='human']
 * @returns {Promise<DecisionResponse>}
 */
export async function resolveDecision(decisionId, option, resolvedBy = 'human') {
  return request(`/decisions/${encodeURIComponent(decisionId)}/resolve`, {
    method: 'POST',
    body: { option, resolved_by: resolvedBy },
  });
}

/**
 * 推迟决策 (PENDING → DEFERRED)
 * @param {string} decisionId
 * @param {string} [reason='']
 * @returns {Promise<DecisionResponse>}
 */
export async function deferDecision(decisionId, reason = '') {
  return request(`/decisions/${encodeURIComponent(decisionId)}/defer`, {
    method: 'POST',
    body: { reason },
  });
}

/**
 * 取消决策 (PENDING → CANCELLED)
 * @param {string} decisionId
 * @param {string} [reason='']
 * @returns {Promise<DecisionResponse>}
 */
export async function cancelDecision(decisionId, reason = '') {
  return request(`/decisions/${encodeURIComponent(decisionId)}/cancel`, {
    method: 'POST',
    body: { reason },
  });
}

// === Workflows (Phase 6.2) ===

/**
 * 列出 infra/got/workflows/*.yaml
 * @returns {Promise<Array<WorkflowListItem>>}
 */
export async function fetchWorkflows() {
  return request('/workflows/list');
}

/**
 * 启动工作流
 * @param {object} req - { workflow_name, initial_inputs?, start_nodes?, max_backtracks?, base_dir? }
 * @returns {Promise<WorkflowStatusResponse>}
 */
export async function runWorkflow(req) {
  return request('/workflows/run', { method: 'POST', body: req });
}

/**
 * 恢复 DECISION 暂停的工作流
 * @param {string} decisionId
 * @param {string} option
 * @param {string} [resolvedBy='human']
 * @returns {Promise<WorkflowStatusResponse>}
 */
export async function resumeWorkflow(decisionId, option, resolvedBy = 'human') {
  return request('/workflows/resume', {
    method: 'POST',
    body: { decision_id: decisionId, option, resolved_by: resolvedBy },
  });
}

/**
 * @typedef {Object} ScoreEntry
 * @property {Object<string, number>} scores_a - S1-S8 scores for variant A
 * @property {Object<string, number>} scores_b - S1-S8 scores for variant B
 * @property {number} scores_total_a - Total score for variant A
 * @property {number} scores_total_b - Total score for variant B
 * @property {number} scores_delta - Score delta (a - b)
 * @property {string} winner - Winning variant label
 * @property {string} label_a - Display label for variant A
 * @property {string} label_b - Display label for variant B
 * @property {string|null} fallback - Fallback reason if LLM scoring failed
 */

/**
 * @typedef {Object} BudgetStatus
 * @property {string} status - "ok" | "exceeded"
 * @property {number} budget_usd - threshold USD
 * @property {number} used_usd - cumulative USD
 * @property {number} used_pct - 0-100+ percent
 */

/**
 * @typedef {Object} WorkflowStatusResponse
 * @property {string} [workflow_name] - Active workflow name
 * @property {boolean} is_active - Whether a workflow is running
 * @property {number} completed - Number of completed nodes
 * @property {number} failed - Number of failed nodes
 * @property {boolean} paused - Whether the workflow is paused
 * @property {string[]} paused_nodes - List of paused node IDs
 * @property {number} node_count - Total number of nodes
 * @property {number} steps - Number of steps executed
 * @property {number} total_cost_usd - Total accumulated cost (USD) — Phase 8.5
 * @property {Object[]} pending_decisions - Pending human decisions
 * @property {Object<string, string>} executions - Node execution states
 * @property {Object<string, ScoreEntry>} score_data - S1-S8 score data — Phase 7.6
 * @property {Object<string, number>} cost_by_scenario - Cost breakdown by scenario — Phase 8.7
 * @property {BudgetStatus} cost_budget_status - Phase 8.8: budget alarm state (empty {} if no budget)
 */

/**
 * 查询当前活跃工作流状态
 * @returns {Promise<WorkflowStatusResponse>}
 */
export async function fetchActiveWorkflow() {
  return request('/workflows/active');
}

/**
 * 获取工作流 mermaid 图 (Phase 6.3 + 6.6.D)
 * @param {string} workflowName
 * @param {object} [opts] - { includeStatus?: boolean }
 * @returns {Promise<{workflow_name: string, mermaid: string, node_count: number, has_decision_nodes: boolean, status_applied: boolean, node_statuses: object<string, string>}>}
 */
export async function fetchWorkflowGraph(workflowName, opts = {}) {
  const params = new URLSearchParams();
  if (opts.includeStatus) params.set('include_status', 'true');
  const qs = params.toString();
  return request(`/workflows/${encodeURIComponent(workflowName)}/mermaid${qs ? `?${qs}` : ''}`);
}

// === CVG Ripples (Phase 9.13) ===

/**
 * Phase 9.13: 列出 ripple (filter: status / volume + pagination)
 * @param {URLSearchParams} [params] - 3-way filter
 * @returns {Promise<Array<RippleListItemResponse>>}
 */
export async function fetchRipples(params = new URLSearchParams()) {
  const qs = params.toString();
  return request(`/cvg/ripples${qs ? `?${qs}` : ''}`);
}

/**
 * Phase 9.13: 获取单个 ripple 详情
 * @param {string} rippleId
 * @returns {Promise<RippleDetailResponse>}
 */
export async function fetchRippleDetail(rippleId) {
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}`);
}

/**
 * Phase 9.13: apply ripple (PENDING → APPLIED)
 * @param {string} rippleId
 * @returns {Promise<RippleActionResponse>}
 */
export async function applyRipple(rippleId) {
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}/apply`, {
    method: 'POST',
  });
}

/**
 * Phase 9.13: reject ripple (PENDING → REJECTED)
 * @param {string} rippleId
 * @param {string} [reason='']
 * @returns {Promise<RippleActionResponse>}
 */
export async function rejectRipple(rippleId, reason = '') {
  const params = reason ? `?reason=${encodeURIComponent(reason)}` : '';
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}/reject${params}`, {
    method: 'POST',
  });
}

/**
 * Phase 9.13: 获取 ripple 统计
 * @returns {Promise<RippleStatsResponse>}
 */
export async function fetchRippleStats() {
  return request('/cvg/ripples/stats');
}

// === Phase 9.14: ripple audit + rollback API methods ===

/**
 * Phase 9.14: 获取 ripple audit log (时间线)
 * @param {string} rippleId
 * @returns {Promise<Array<AuditEntryResponse>>}
 */
export async function fetchRippleAudit(rippleId) {
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}/audit`);
}

/**
 * Phase 9.14: rollback ripple (APPLIED → PENDING, 不可逆操作的唯一后悔药)
 * @param {string} rippleId
 * @param {string} reason - 操作原因 (审计用)
 * @returns {Promise<RippleActionResponse>}
 */
export async function rollbackRipple(rippleId, reason) {
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}/rollback`, {
    method: 'POST',
    body: { reason },
  });
}
