/**
 * API Client for LingWen Dashboard
 * Communicates with FastAPI backend on port 8765
 *
 * Phase 6.2 扩展:
 * - 决策 API:pendingDecisions, allDecisions, resolveDecision, deferDecision, cancelDecision
 * - 工作流 API:listWorkflows, runWorkflow, resumeWorkflow, activeWorkflow
 * - request() helper 支持 method + body
 */

/**
 * @typedef {{id:number, action:string, actor:string, origin:string, reason:string|null, created_at:string}} AuditEntryResponse
 */

// Same-origin when UI is served by FastAPI (LINGWEN_SERVE_UI=1) or via Vite proxy.
const BASE_URL = import.meta.env.VITE_API_BASE || '/api';

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
 * Phase 9.82 F74: pilot/batch production records (read-only).
 * @param {{ chapterNum?: number, limit?: number }} [opts]
 */
export async function fetchProductionRecords(opts = {}) {
  const params = new URLSearchParams();
  if (opts.chapterNum != null) params.set('chapter_num', String(opts.chapterNum));
  if (opts.limit != null) params.set('limit', String(opts.limit));
  const q = params.toString();
  return request(`/production-records${q ? `?${q}` : ''}`);
}

/**
 * Phase 9.89 F81: aggregated pilot/batch stats for Analytics.
 * @param {{ limit?: number }} [opts]
 */
export async function fetchProductionRollup(opts = {}) {
  const params = new URLSearchParams();
  if (opts.limit != null) params.set('limit', String(opts.limit));
  const q = params.toString();
  return request(`/production-records/rollup${q ? `?${q}` : ''}`);
}

/**
 * Phase 9.96 F87: time-ordered production cost trend for Analytics chart.
 * @param {{ limit?: number }} [opts]
 */
export async function fetchProductionCostTrend(opts = {}) {
  const params = new URLSearchParams();
  if (opts.limit != null) params.set('limit', String(opts.limit));
  const q = params.toString();
  return request(`/production-records/trend${q ? `?${q}` : ''}`);
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
 * @property {Object|null} [incremental_backfill] - Phase 9.68 F60: CVG incremental backfill stats
 * @property {Object|null} [production_summary] - Phase 9.74 F66: chapter_num + memory source + backfill
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

/**
 * Phase 9.41 F30: persisted CVG reference graph for ImpactGraph.vue
 * @param {object} [options] - { volume?: number, dimension?: string, limit?: number }
 * @returns {Promise<{nodes:Array, edges:Array, total_node_count:number, total_edge_count:number, truncated:boolean}>}
 */
export async function fetchReferenceGraph(options = {}) {
  const params = new URLSearchParams();
  if (options.volume != null) params.set('volume', String(options.volume));
  if (options.dimension) params.set('dimension', options.dimension);
  if (options.limit != null) params.set('limit', String(options.limit));
  const qs = params.toString();
  return request(`/cvg/reference-graph${qs ? `?${qs}` : ''}`);
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

// === Phase 9.15: cascade BFS + dry-run preview API methods ===

/**
 * Phase 9.15: fetch cascaded ripple (nodes/edges/actions downstream of trigger).
 * Returns CascadedRipple JSON { trigger_ripple_id, cascade_nodes, cascade_edges,
 *   cascade_actions, depth_reached, generated_at, bfs_algorithm_version }.
 * @param {string} rippleId
 * @returns {Promise<object>}
 */
export async function fetchRippleCascade(rippleId) {
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}/cascade`);
}

/**
 * Phase 9.15: fetch dry-run preview summary (what apply would modify).
 * Returns CascadePreviewResponse JSON { ripple_id, nodes_to_add, edges_to_add,
 *   actions_to_apply, totals: { nodes, edges, actions } }.
 * @param {string} rippleId
 * @returns {Promise<object>}
 */
export async function fetchRipplePreview(rippleId) {
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}/cascade/preview`);
}

// === Phase 9.22: cascade_runs list + cancel + replay-readonly API methods ===

/**
 * Phase 9.22: fetch historical cascade_runs for a ripple (Phase 9.20 endpoint).
 * Phase 9.23: options extended with minDepth, maxDepth, algorithm (all optional).
 * Returns CascadeRun[] JSON array sorted by id DESC.
 * @param {string} rippleId
 * @param {object} [options] - {
 *   limit?: number, offset?: number,
 *   status?: 'running'|'completed'|'cancelled'|'failed',
 *   minDepth?: number, maxDepth?: number,    // Phase 9.23
 *   algorithm?: 'v1'|'v2_weighted',            // Phase 9.23
 * }
 * @returns {Promise<Array<{id:number, ripple_id:string, started_at:string, completed_at:string|null,
 *   max_depth:number, depth_reached:number, status:'running'|'completed'|'cancelled'|'failed',
 *   algorithm:string, cascade_nodes:Array, cascade_edges:Array, cascade_actions:Array}>>}
 */
export async function fetchCascadeRuns(rippleId, options = {}) {
  const params = new URLSearchParams();
  if (options.limit) params.set('limit', String(options.limit));
  if (options.offset) params.set('offset', String(options.offset));
  if (options.status) params.set('status', options.status);
  if (options.minDepth) params.set('min_depth', String(options.minDepth));
  if (options.maxDepth) params.set('max_depth', String(options.maxDepth));
  if (options.algorithm) params.set('algorithm', options.algorithm);
  const qs = params.toString();
  return request(`/ripples/cascade/${encodeURIComponent(rippleId)}/runs${qs ? '?' + qs : ''}`);
}

/**
 * Phase 9.46 F35: fetch cascade_runs across all ripples.
 * @param {object} [options] - {
 *   limit?, offset?, status?, minDepth?, maxDepth?, algorithm?,
 *   rippleId?, sinceDays?,
 * }
 */
export async function fetchAllCascadeRuns(options = {}) {
  const params = new URLSearchParams();
  if (options.limit) params.set('limit', String(options.limit));
  if (options.offset) params.set('offset', String(options.offset));
  if (options.status) params.set('status', options.status);
  if (options.minDepth) params.set('min_depth', String(options.minDepth));
  if (options.maxDepth) params.set('max_depth', String(options.maxDepth));
  if (options.algorithm) params.set('algorithm', options.algorithm);
  if (options.rippleId) params.set('ripple_id', options.rippleId);
  if (options.sinceDays) params.set('since_days', String(options.sinceDays));
  const qs = params.toString();
  return request(`/cascade/runs${qs ? '?' + qs : ''}`);
}

/**
 * Phase 9.22: cancel a running cascade run (Phase 9.21 endpoint).
 * Idempotent — calling on already-cancelled run returns 200 with current state.
 * @param {string} rippleId
 * @param {number} runId
 * @param {string} [reason] - audit reason (optional, default "")
 * @returns {Promise<object>} Updated CascadeRunResponse
 */
export async function cancelCascadeRun(rippleId, runId, reason = '') {
  return request(
    `/ripples/cascade/${encodeURIComponent(rippleId)}/runs/${runId}/cancel`,
    { method: 'POST', body: JSON.stringify({ reason }) }
  );
}

/**
 * Phase 9.22: Replay-readonly fetch with a given max_depth.
 * Hits Phase 9.20 GET /api/ripples/cascade/{id}?max_depth=N&persist=false.
 * persist=false avoids polluting cascade_runs table with replay reads.
 * Returns Phase 9.19 CascadeResponse (same shape as fetchRippleCascade).
 * @param {string} rippleId
 * @param {number} maxDepth - 1..10
 * @returns {Promise<{trigger_ripple_id:string, cascade_nodes:Array, cascade_edges:Array,
 *   cascade_actions:Array, depth_reached:number, generated_at:string,
 *   bfs_algorithm_version:string}>}
 */
export async function fetchCascadeWithDepth(rippleId, maxDepth) {
  return request(
    `/ripples/cascade/${encodeURIComponent(rippleId)}?max_depth=${encodeURIComponent(maxDepth)}&persist=false`
  );
}

// === Budgets (Phase 8.12 / 8.15 — Settings read-only F68, write F78) ===

/**
 * @returns {Promise<{ per_run: object, per_day: object, per_week: object }>}
 */
export async function fetchBudgets() {
  return request('/budgets');
}

/**
 * @returns {Promise<Record<string, { usd: number, set_at: string }|null>>}
 */
export async function fetchBudgetsByTier() {
  return request('/budgets/by-tier');
}

/**
 * Set day/week budget (per-run not exposed via this endpoint).
 * @param {'day'|'week'} scope
 * @param {number} usd
 * @returns {Promise<{ ok: boolean, scope: string, usd: number }>}
 */
export async function setBudget(scope, usd) {
  return request(`/budgets/${encodeURIComponent(scope)}`, {
    method: 'PUT',
    body: { usd },
  });
}

/**
 * Set model tier budget.
 * @param {'haiku'|'sonnet'|'opus'} tier
 * @param {number} usd
 * @returns {Promise<{ ok: boolean, tier: string, usd: number }>}
 */
export async function setBudgetByTier(tier, usd) {
  return request(`/budgets/by-tier/${encodeURIComponent(tier)}`, {
    method: 'PUT',
    body: { usd },
  });
}

// === Studio (Phase 10.04) ===

export async function fetchStudioProjects() {
  return request('/studio/projects');
}

export async function fetchStudioActive() {
  return request('/studio/active');
}

export async function setStudioActive(slug) {
  return request('/studio/active', { method: 'PUT', body: { slug } });
}

export async function fetchStudioSummary() {
  return request('/studio/summary');
}

export async function fetchStudioQuality() {
  return request('/studio/quality');
}

export async function fetchStudioQualityReport() {
  return request('/studio/quality-report');
}

export async function fetchStudioProseDiff() {
  return request('/studio/prose-diff');
}

export async function fetchStudioProseJudge() {
  return request('/studio/prose-judge');
}

export async function fetchCreatorOverview() {
  return request('/creator/overview');
}

export async function runCreatorLogicCheck() {
  return request('/creator/logic-check', { method: 'POST' });
}

export async function fetchCreatorVolumePlan() {
  return request('/creator/volume-plan');
}

export async function saveCreatorVolumePlan(volumes, expectedRevision) {
  const body = { volumes };
  if (expectedRevision) body.expected_revision = expectedRevision;
  return request('/creator/volume-plan', {
    method: 'PUT',
    body,
  });
}

export async function mergeCreatorVolumePlan(body) {
  return request('/creator/volume-plan/merge', {
    method: 'POST',
    body,
  });
}

export async function splitCreatorVolumePlan(body) {
  return request('/creator/volume-plan/split', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorVolumeTemplates() {
  return request('/creator/volume-plan/templates');
}

export async function applyCreatorVolumeTemplate(body) {
  return request('/creator/volume-plan/apply-template', {
    method: 'POST',
    body,
  });
}

export async function saveCreatorVolumeTemplate(body) {
  return request('/creator/volume-plan/templates/save', {
    method: 'POST',
    body,
  });
}

export async function deleteCreatorVolumeTemplate(templateId) {
  return request(`/creator/volume-plan/templates/${encodeURIComponent(templateId)}`, {
    method: 'DELETE',
  });
}

export async function renameCreatorVolumeTemplate(templateId, body) {
  return request(`/creator/volume-plan/templates/${encodeURIComponent(templateId)}`, {
    method: 'PATCH',
    body,
  });
}

export async function exportCreatorVolumeTemplates() {
  return request('/creator/volume-plan/templates/export');
}

export async function importCreatorVolumeTemplates(body) {
  return request('/creator/volume-plan/templates/import', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorVolumeTemplateSyncSources() {
  return request('/creator/volume-plan/templates/sync-sources');
}

export async function syncCreatorVolumeTemplates(body) {
  return request('/creator/volume-plan/templates/sync', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorFactoryVolumeTemplates() {
  return request('/creator/volume-plan/templates/factory');
}

export async function publishCreatorVolumeTemplateToFactory(body) {
  return request('/creator/volume-plan/templates/factory/publish', {
    method: 'POST',
    body,
  });
}

export async function pullCreatorFactoryVolumeTemplates(body) {
  return request('/creator/volume-plan/templates/factory/pull', {
    method: 'POST',
    body,
  });
}

export async function deleteCreatorFactoryVolumeTemplate(templateId) {
  return request(`/creator/volume-plan/templates/factory/${encodeURIComponent(templateId)}`, {
    method: 'DELETE',
  });
}

export async function fetchCreatorOnboarding() {
  return request('/creator/onboarding');
}

export async function saveCreatorOnboardingProgress(body) {
  return request('/creator/onboarding/progress', {
    method: 'PUT',
    body,
  });
}

export async function applyCreatorOnboardingShare(body) {
  return request('/creator/onboarding/progress/apply-share', {
    method: 'POST',
    body,
  });
}

export async function saveCreatorOnboardingNotes(body) {
  return request('/creator/onboarding/notes', {
    method: 'PUT',
    body,
  });
}

export async function setCreatorVolumeTemplateVersion(templateId, body) {
  return request(`/creator/volume-plan/templates/${encodeURIComponent(templateId)}/version`, {
    method: 'PUT',
    body,
  });
}

export async function fetchCreatorVolumeTemplateChangelog(templateId) {
  return request(
    `/creator/volume-plan/templates/${encodeURIComponent(templateId)}/version-changelog`,
  );
}

export async function rollbackCreatorVolumeTemplate(templateId, body) {
  return request(
    `/creator/volume-plan/templates/${encodeURIComponent(templateId)}/version-rollback`,
    { method: 'POST', body },
  );
}

export async function fetchCreatorOnboardingNotifications(handle) {
  const params = handle ? `?handle=${encodeURIComponent(handle)}` : '';
  return request(`/creator/onboarding/notifications${params}`);
}

export async function ackCreatorOnboardingNotifications(body) {
  return request('/creator/onboarding/notifications/ack', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorOnboardingWebhook() {
  return request('/creator/onboarding/webhook');
}

export async function saveCreatorOnboardingWebhook(body) {
  return request('/creator/onboarding/webhook', {
    method: 'PUT',
    body,
  });
}

export async function fetchCreatorOnboardingEmail() {
  return request('/creator/onboarding/email');
}

export async function saveCreatorOnboardingEmail(body) {
  return request('/creator/onboarding/email', {
    method: 'PUT',
    body,
  });
}

export async function fetchCreatorOnboardingNotificationDigest(handle) {
  const params = handle ? `?handle=${encodeURIComponent(handle)}` : '';
  return request(`/creator/onboarding/notifications/digest${params}`);
}

export async function fetchCreatorOnboardingDigestSchedule() {
  return request('/creator/onboarding/notifications/digest/schedule');
}

export async function saveCreatorOnboardingDigestSchedule(body) {
  return request('/creator/onboarding/notifications/digest/schedule', {
    method: 'PUT',
    body,
  });
}

export async function dispatchCreatorOnboardingDigest(force = false) {
  const params = force ? '?force=true' : '';
  return request(`/creator/onboarding/notifications/digest/dispatch${params}`, {
    method: 'POST',
  });
}

export async function fetchCreatorOnboardingDigestRetryQueue() {
  return request('/creator/onboarding/notifications/digest/retry-queue');
}

export async function fetchCreatorOnboardingDigestStats() {
  return request('/creator/onboarding/notifications/digest/stats');
}

export async function processCreatorOnboardingDigestRetries() {
  return request('/creator/onboarding/notifications/digest/retry', {
    method: 'POST',
  });
}

export async function fetchCreatorTemplateApprovals(params = {}) {
  const search = new URLSearchParams();
  if (params.status) search.set('status', params.status);
  if (params.template_id) search.set('template_id', params.template_id);
  const qs = search.toString();
  return request(`/creator/volume-plan/templates/approvals${qs ? `?${qs}` : ''}`);
}

export async function submitCreatorTemplateVersionApproval(templateId, body) {
  return request(
    `/creator/volume-plan/templates/${encodeURIComponent(templateId)}/version-approval`,
    { method: 'POST', body },
  );
}

export async function approveCreatorTemplateApproval(approvalId, body = {}) {
  return request(
    `/creator/volume-plan/templates/approvals/${encodeURIComponent(approvalId)}/approve`,
    { method: 'POST', body },
  );
}

export async function rejectCreatorTemplateApproval(approvalId, body) {
  return request(
    `/creator/volume-plan/templates/approvals/${encodeURIComponent(approvalId)}/reject`,
    { method: 'POST', body },
  );
}

export async function fetchCreatorTemplateApprovalChainConfig() {
  return request('/creator/volume-plan/templates/approvals/chain-config');
}

export async function saveCreatorTemplateApprovalChainConfig(body) {
  return request('/creator/volume-plan/templates/approvals/chain-config', {
    method: 'PUT',
    body,
  });
}

export async function fetchCreatorTemplateApprovalHistory(limit = 20) {
  return request(`/creator/volume-plan/templates/approvals/history?limit=${limit}`);
}

export async function exportCreatorTemplateApprovalAudit() {
  return request('/creator/volume-plan/templates/approvals/audit-export');
}

export async function fetchCreatorTemplateApprovalSlaConfig() {
  return request('/creator/volume-plan/templates/approvals/sla-config');
}

export async function saveCreatorTemplateApprovalSlaConfig(body) {
  return request('/creator/volume-plan/templates/approvals/sla-config', {
    method: 'PUT',
    body,
  });
}

export async function fetchCreatorTemplateApprovalOverdue() {
  return request('/creator/volume-plan/templates/approvals/overdue');
}

export async function transferCreatorTemplateApproval(approvalId, body) {
  return request(
    `/creator/volume-plan/templates/approvals/${encodeURIComponent(approvalId)}/transfer`,
    { method: 'POST', body },
  );
}

export async function fetchCreatorTemplateApprovalSnapshotDiff(approvalId) {
  return request(
    `/creator/volume-plan/templates/approvals/${encodeURIComponent(approvalId)}/snapshot-diff`,
  );
}

export async function fetchCreatorTemplateApprovalSnapshotDrift(approvalId) {
  return request(
    `/creator/volume-plan/templates/approvals/${encodeURIComponent(approvalId)}/snapshot-drift`,
  );
}

export async function batchApproveCreatorTemplateApprovals(body) {
  return request('/creator/volume-plan/templates/approvals/batch-approve', {
    method: 'POST',
    body,
  });
}

export async function batchRejectCreatorTemplateApprovals(body) {
  return request('/creator/volume-plan/templates/approvals/batch-reject', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorOnboardingDigestDeadLetter() {
  return request('/creator/onboarding/notifications/digest/dead-letter');
}

export async function replayCreatorOnboardingDigestDeadLetter(body = {}) {
  return request('/creator/onboarding/notifications/digest/dead-letter/replay', {
    method: 'POST',
    body,
  });
}

export async function preflightCreatorFactoryMergePresetPull(body) {
  return request('/creator/settings-docs/merge-preferences/preset-packages/factory/pull/preflight', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorMergePresetChangelog(packageId, limit = 10) {
  return request(
    `/creator/settings-docs/merge-preferences/preset-packages/${encodeURIComponent(packageId)}/changelog?limit=${limit}`,
  );
}

export async function fetchCreatorMergePresetChangelogDiff(packageId, entryIndex = 0) {
  return request(
    `/creator/settings-docs/merge-preferences/preset-packages/${encodeURIComponent(packageId)}/changelog/diff?entry_index=${entryIndex}`,
  );
}

export async function fetchCreatorMergePresetPackages() {
  return request('/creator/settings-docs/merge-preferences/preset-packages');
}

export async function exportCreatorMergePresetPackages() {
  return request('/creator/settings-docs/merge-preferences/preset-packages/export');
}

export async function importCreatorMergePresetPackages(body) {
  return request('/creator/settings-docs/merge-preferences/preset-packages/import', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorFactoryMergePresetPackages() {
  return request('/creator/settings-docs/merge-preferences/preset-packages/factory');
}

export async function publishCreatorMergePresetToFactory(body) {
  return request('/creator/settings-docs/merge-preferences/preset-packages/factory/publish', {
    method: 'POST',
    body,
  });
}

export async function pullCreatorFactoryMergePresetPackages(body) {
  return request('/creator/settings-docs/merge-preferences/preset-packages/factory/pull', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorMergePresetGraph() {
  return request('/creator/settings-docs/merge-preferences/preset-packages/graph');
}

export async function fetchCreatorMergePresetConflicts() {
  return request('/creator/settings-docs/merge-preferences/preset-packages/conflicts');
}

export async function fetchCreatorMergePresetConflictFixes() {
  return request('/creator/settings-docs/merge-preferences/preset-packages/conflicts/fixes');
}

export async function applyCreatorMergePresetConflictFix(body) {
  return request('/creator/settings-docs/merge-preferences/preset-packages/conflicts/apply-fix', {
    method: 'POST',
    body,
  });
}

export async function applyAllCreatorMergePresetConflictFixes() {
  return request('/creator/settings-docs/merge-preferences/preset-packages/conflicts/apply-all', {
    method: 'POST',
  });
}

export async function preflightCreatorMergePresetImport(body) {
  return request('/creator/settings-docs/merge-preferences/preset-packages/import/preflight', {
    method: 'POST',
    body,
  });
}

export async function previewCreatorMergePresetImportDiff(body) {
  return request('/creator/settings-docs/merge-preferences/preset-packages/import/preview-diff', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorMergePresetToposort() {
  return request('/creator/settings-docs/merge-preferences/preset-packages/toposort');
}

export async function applyCreatorMergePresetToposort() {
  return request('/creator/settings-docs/merge-preferences/preset-packages/toposort/apply', {
    method: 'POST',
  });
}

export async function fetchCreatorFactoryMergePresetConflicts() {
  return request('/creator/settings-docs/merge-preferences/preset-packages/factory/conflicts');
}

export async function resolveCreatorFactoryMergePresetConflict(body) {
  return request('/creator/settings-docs/merge-preferences/preset-packages/factory/merge-conflicts', {
    method: 'POST',
    body,
  });
}

export async function deleteCreatorFactoryMergePresetPackage(packageId) {
  return request(
    `/creator/settings-docs/merge-preferences/preset-packages/factory/${encodeURIComponent(packageId)}`,
    { method: 'DELETE' },
  );
}

export async function fetchCreatorChapterPreview(chapterNum) {
  return request(`/creator/chapters/${chapterNum}`);
}

export async function fetchCreatorSettingsDocs() {
  return request('/creator/settings-docs');
}

export async function saveCreatorSettingsDocs(body) {
  return request('/creator/settings-docs', {
    method: 'PUT',
    body,
  });
}

export async function previewCreatorSettingsDocs(body) {
  return request('/creator/settings-docs/preview', {
    method: 'POST',
    body,
  });
}

export async function previewCreatorSettingsThreeWay(body) {
  return request('/creator/settings-docs/three-way-preview', {
    method: 'POST',
    body,
  });
}

export async function previewCreatorSettingsMerge(body) {
  return request('/creator/settings-docs/merge-preview', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorMergePreferences() {
  return request('/creator/settings-docs/merge-preferences');
}

export async function fetchCreatorGlobalMergePreferences() {
  return request('/creator/settings-docs/merge-preferences/global');
}

export async function exportCreatorMergePreferences() {
  return request('/creator/settings-docs/merge-preferences/export');
}

export async function importCreatorMergePreferences(body) {
  return request('/creator/settings-docs/merge-preferences/import', {
    method: 'POST',
    body,
  });
}

export async function fetchCreatorSettingsHistory() {
  return request('/creator/settings-docs/history');
}

export async function restoreCreatorSettingsSnapshot(snapshotId) {
  return request('/creator/settings-docs/restore', {
    method: 'POST',
    body: { snapshot_id: snapshotId },
  });
}

/**
 * @param {{ start_chapter: number, end_chapter: number, mode?: string, budget_usd?: number }} req
 */
export async function studioProductionPreflight(req) {
  const params = new URLSearchParams();
  if (req.budget_usd != null) params.set('budget_usd', String(req.budget_usd));
  const q = params.toString();
  return request(`/studio/production/preflight${q ? `?${q}` : ''}`, {
    method: 'POST',
    body: {
      start_chapter: req.start_chapter,
      end_chapter: req.end_chapter,
      mode: req.mode || 'canon',
    },
  });
}

/**
 * @param {{ start_chapter: number, end_chapter: number, mode?: string, budget_usd?: number, skip_preflight?: boolean }} req
 */
export async function studioProductionRun(req) {
  return request('/studio/production/run', {
    method: 'POST',
    body: {
      start_chapter: req.start_chapter,
      end_chapter: req.end_chapter,
      mode: req.mode || 'canon',
      budget_usd: req.budget_usd ?? 0.15,
      skip_preflight: Boolean(req.skip_preflight),
    },
  });
}

export async function fetchStudioActiveBatchJob() {
  return request('/studio/production/jobs/active');
}

export async function fetchStudioBatchJob(jobId) {
  return request(`/studio/production/jobs/${encodeURIComponent(jobId)}`);
}
