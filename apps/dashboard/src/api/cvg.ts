/**
 * CVG (Cross-Volume Graph) API client — typed wrapper around /cvg/* and
 * /ripples/cascade/* endpoints.
 *
 * Path convention: relative paths (no `/api/` prefix) — `core.js`'s `request()`
 * prepends `BASE_URL='/api'`.
 *
 * NOTE: This is a NEW typed wrapper added in v16.2.8 (Phase 126 cleanup).
 * Existing api/cvg.js continues to handle backward-compatible calls.
 * v16.2.8 T5 deletes api/cvg.js after consumers migrate.
 */
import { request } from './core.js';

// ---------------------------------------------------------------------------
// /cvg/ripples (list ripples with optional filters)
// ---------------------------------------------------------------------------

export async function fetchRipples(params: URLSearchParams = new URLSearchParams()): Promise<unknown> {
  const qs = params.toString();
  return request(`/cvg/ripples${qs ? `?${qs}` : ''}`);
}

// ---------------------------------------------------------------------------
// /cvg/ripples/{id} (single ripple detail)
// ---------------------------------------------------------------------------

export async function fetchRippleDetail(rippleId: string): Promise<unknown> {
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}`);
}

// ---------------------------------------------------------------------------
// /cvg/ripples/{id}/apply (apply a ripple to canon)
// ---------------------------------------------------------------------------

export async function applyRipple(rippleId: string): Promise<unknown> {
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}/apply`, {
    method: 'POST',
  });
}

// ---------------------------------------------------------------------------
// /cvg/ripples/{id}/reject (reject a ripple with optional reason)
// ---------------------------------------------------------------------------

export async function rejectRipple(rippleId: string, reason: string = ''): Promise<unknown> {
  const params = reason ? `?reason=${encodeURIComponent(reason)}` : '';
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}/reject${params}`, {
    method: 'POST',
  });
}

// ---------------------------------------------------------------------------
// /cvg/ripples/stats (aggregate ripple statistics)
// ---------------------------------------------------------------------------

export async function fetchRippleStats(): Promise<unknown> {
  return request('/cvg/ripples/stats');
}

// ---------------------------------------------------------------------------
// /cvg/reference-graph (cross-volume reference graph)
// ---------------------------------------------------------------------------

export interface ReferenceGraphOptions {
  volume?: number;
  dimension?: string;
  limit?: number;
}

export async function fetchReferenceGraph(options: ReferenceGraphOptions = {}): Promise<unknown> {
  const params = new URLSearchParams();
  if (options.volume != null) params.set('volume', String(options.volume));
  if (options.dimension) params.set('dimension', options.dimension);
  if (options.limit != null) params.set('limit', String(options.limit));
  const qs = params.toString();
  return request(`/cvg/reference-graph${qs ? `?${qs}` : ''}`);
}

// ---------------------------------------------------------------------------
// /cvg/ripples/{id}/audit (audit trail for a single ripple)
// ---------------------------------------------------------------------------

export async function fetchRippleAudit(rippleId: string): Promise<unknown> {
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}/audit`);
}

// ---------------------------------------------------------------------------
// /cvg/ripples/{id}/rollback (revert a previously-applied ripple)
// ---------------------------------------------------------------------------

export async function rollbackRipple(rippleId: string, reason: string): Promise<unknown> {
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}/rollback`, {
    method: 'POST',
    body: { reason },
  });
}

// ---------------------------------------------------------------------------
// /cvg/ripples/{id}/cascade (full cascade tree)
// ---------------------------------------------------------------------------

export async function fetchRippleCascade(rippleId: string): Promise<unknown> {
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}/cascade`);
}

// ---------------------------------------------------------------------------
// /cvg/ripples/{id}/cascade/preview (cascade preview without applying)
// ---------------------------------------------------------------------------

export async function fetchRipplePreview(rippleId: string): Promise<unknown> {
  return request(`/cvg/ripples/${encodeURIComponent(rippleId)}/cascade/preview`);
}

// ---------------------------------------------------------------------------
// /ripples/cascade/{id}/runs (cascade run history for one ripple)
// ---------------------------------------------------------------------------

export interface CascadeRunsOptions {
  limit?: number;
  offset?: number;
  status?: string;
  minDepth?: number;
  maxDepth?: number;
  algorithm?: string;
}

export async function fetchCascadeRuns(
  rippleId: string,
  options: CascadeRunsOptions = {},
): Promise<unknown> {
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

// ---------------------------------------------------------------------------
// /cascade/runs (project-wide cascade run history)
// ---------------------------------------------------------------------------

export interface AllCascadeRunsOptions extends CascadeRunsOptions {
  rippleId?: string;
  sinceDays?: number;
}

export async function fetchAllCascadeRuns(options: AllCascadeRunsOptions = {}): Promise<unknown> {
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

// ---------------------------------------------------------------------------
// /ripples/cascade/{id}/runs/{runId}/cancel (cancel an in-flight cascade run)
// ---------------------------------------------------------------------------

export async function cancelCascadeRun(
  rippleId: string,
  runId: string,
  reason: string = '',
): Promise<unknown> {
  return request(
    `/ripples/cascade/${encodeURIComponent(rippleId)}/runs/${runId}/cancel`,
    { method: 'POST', body: JSON.stringify({ reason }) },
  );
}

// ---------------------------------------------------------------------------
// /ripples/cascade/{id} (bounded cascade with max_depth + no persist)
// ---------------------------------------------------------------------------

export async function fetchCascadeWithDepth(rippleId: string, maxDepth: number): Promise<unknown> {
  return request(
    `/ripples/cascade/${encodeURIComponent(rippleId)}?max_depth=${encodeURIComponent(maxDepth)}&persist=false`,
  );
}