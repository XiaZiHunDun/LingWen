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
 *
 * v16.5 #7: Promise<unknown> narrowed to concrete DTO types declared in
 * @lingwen/dashboard-contracts/shared/cvg.
 */
import type {
  CascadeCancelPayloadDTO,
  CascadePreviewResponseDTO,
  CascadeResponseDTO,
  CascadeRunResponseDTO,
  ReferenceGraphResponseDTO,
  RippleActionResponseDTO,
  RippleAuditEntryResponseDTO,
  RippleDetailResponseDTO,
  RippleListItemResponseDTO,
  RippleStatsResponseDTO,
} from '@lingwen/dashboard-contracts/shared';
import { request } from './core.js';

// ---------------------------------------------------------------------------
// /cvg/ripples (list ripples with optional filters)
// ---------------------------------------------------------------------------

export async function fetchRipples(
  params: URLSearchParams = new URLSearchParams(),
): Promise<RippleListItemResponseDTO[]> {
  const qs = params.toString();
  const data = await request(`/cvg/ripples${qs ? `?${qs}` : ''}`);
  return data as RippleListItemResponseDTO[];
}

// ---------------------------------------------------------------------------
// /cvg/ripples/{id} (single ripple detail)
// ---------------------------------------------------------------------------

export async function fetchRippleDetail(rippleId: string): Promise<RippleDetailResponseDTO> {
  const data = await request(`/cvg/ripples/${encodeURIComponent(rippleId)}`);
  return data as RippleDetailResponseDTO;
}

// ---------------------------------------------------------------------------
// /cvg/ripples/{id}/apply (apply a ripple to canon)
// ---------------------------------------------------------------------------

export async function applyRipple(rippleId: string): Promise<RippleActionResponseDTO> {
  const data = await request(`/cvg/ripples/${encodeURIComponent(rippleId)}/apply`, {
    method: 'POST',
  });
  return data as RippleActionResponseDTO;
}

// ---------------------------------------------------------------------------
// /cvg/ripples/{id}/reject (reject a ripple with optional reason)
// ---------------------------------------------------------------------------

export async function rejectRipple(rippleId: string, reason: string = ''): Promise<RippleActionResponseDTO> {
  const params = reason ? `?reason=${encodeURIComponent(reason)}` : '';
  const data = await request(
    `/cvg/ripples/${encodeURIComponent(rippleId)}/reject${params}`,
    { method: 'POST' },
  );
  return data as RippleActionResponseDTO;
}

// ---------------------------------------------------------------------------
// /cvg/ripples/stats (aggregate ripple statistics)
// ---------------------------------------------------------------------------

export async function fetchRippleStats(): Promise<RippleStatsResponseDTO> {
  const data = await request('/cvg/ripples/stats');
  return data as RippleStatsResponseDTO;
}

// ---------------------------------------------------------------------------
// /cvg/reference-graph (cross-volume reference graph)
// ---------------------------------------------------------------------------

export interface ReferenceGraphOptions {
  volume?: number;
  dimension?: string;
  limit?: number;
}

export async function fetchReferenceGraph(
  options: ReferenceGraphOptions = {},
): Promise<ReferenceGraphResponseDTO> {
  const params = new URLSearchParams();
  if (options.volume != null) params.set('volume', String(options.volume));
  if (options.dimension) params.set('dimension', options.dimension);
  if (options.limit != null) params.set('limit', String(options.limit));
  const qs = params.toString();
  const data = await request(`/cvg/reference-graph${qs ? `?${qs}` : ''}`);
  return data as ReferenceGraphResponseDTO;
}

// ---------------------------------------------------------------------------
// /cvg/ripples/{id}/audit (audit trail for a single ripple)
// ---------------------------------------------------------------------------

export async function fetchRippleAudit(rippleId: string): Promise<RippleAuditEntryResponseDTO[]> {
  const data = await request(`/cvg/ripples/${encodeURIComponent(rippleId)}/audit`);
  return data as RippleAuditEntryResponseDTO[];
}

// ---------------------------------------------------------------------------
// /cvg/ripples/{id}/rollback (revert a previously-applied ripple)
// ---------------------------------------------------------------------------

export async function rollbackRipple(
  rippleId: string,
  reason: string,
): Promise<RippleActionResponseDTO> {
  const data = await request(`/cvg/ripples/${encodeURIComponent(rippleId)}/rollback`, {
    method: 'POST',
    body: { reason },
  });
  return data as RippleActionResponseDTO;
}

// ---------------------------------------------------------------------------
// /cvg/ripples/{id}/cascade (full cascade tree)
// ---------------------------------------------------------------------------

export async function fetchRippleCascade(rippleId: string): Promise<CascadeResponseDTO> {
  const data = await request(`/cvg/ripples/${encodeURIComponent(rippleId)}/cascade`);
  return data as CascadeResponseDTO;
}

// ---------------------------------------------------------------------------
// /cvg/ripples/{id}/cascade/preview (cascade preview without applying)
// ---------------------------------------------------------------------------

export async function fetchRipplePreview(rippleId: string): Promise<CascadePreviewResponseDTO> {
  const data = await request(`/cvg/ripples/${encodeURIComponent(rippleId)}/cascade/preview`);
  return data as CascadePreviewResponseDTO;
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
): Promise<CascadeRunResponseDTO[]> {
  const params = new URLSearchParams();
  if (options.limit) params.set('limit', String(options.limit));
  if (options.offset) params.set('offset', String(options.offset));
  if (options.status) params.set('status', options.status);
  if (options.minDepth) params.set('min_depth', String(options.minDepth));
  if (options.maxDepth) params.set('max_depth', String(options.maxDepth));
  if (options.algorithm) params.set('algorithm', options.algorithm);
  const qs = params.toString();
  const data = await request(`/ripples/cascade/${encodeURIComponent(rippleId)}/runs${qs ? '?' + qs : ''}`);
  return data as CascadeRunResponseDTO[];
}

// ---------------------------------------------------------------------------
// /cascade/runs (project-wide cascade run history)
// ---------------------------------------------------------------------------

export interface AllCascadeRunsOptions extends CascadeRunsOptions {
  rippleId?: string;
  sinceDays?: number;
}

export async function fetchAllCascadeRuns(
  options: AllCascadeRunsOptions = {},
): Promise<CascadeRunResponseDTO[]> {
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
  const data = await request(`/cascade/runs${qs ? '?' + qs : ''}`);
  return data as CascadeRunResponseDTO[];
}

// ---------------------------------------------------------------------------
// /ripples/cascade/{id}/runs/{runId}/cancel (cancel an in-flight cascade run)
// ---------------------------------------------------------------------------

export async function cancelCascadeRun(
  rippleId: string,
  runId: string,
  reason: string = '',
): Promise<CascadeCancelPayloadDTO> {
  const data = await request(
    `/ripples/cascade/${encodeURIComponent(rippleId)}/runs/${runId}/cancel`,
    { method: 'POST', body: JSON.stringify({ reason }) },
  );
  return data as CascadeCancelPayloadDTO;
}

// ---------------------------------------------------------------------------
// /ripples/cascade/{id} (bounded cascade with max_depth + no persist)
// ---------------------------------------------------------------------------

export async function fetchCascadeWithDepth(
  rippleId: string,
  maxDepth: number,
): Promise<CascadeResponseDTO> {
  const data = await request(
    `/ripples/cascade/${encodeURIComponent(rippleId)}?max_depth=${encodeURIComponent(String(maxDepth))}&persist=false`,
  );
  return data as CascadeResponseDTO;
}
