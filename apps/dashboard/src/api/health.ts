/**
 * Health API client — typed wrapper around /overview, /chapters,
 * /production-records*, /health endpoints.
 *
 * Path convention: relative paths (no `/api/` prefix) — `core.js`'s `request()`
 * prepends `BASE_URL='/api'`.
 *
 * NOTE: This is a NEW typed wrapper added in v16.2.8 (Phase 126 cleanup).
 * Existing api/health.js continues to handle backward-compatible calls.
 * v16.2.8 T5 deletes api/health.js after consumers migrate.
 */
import { request } from './core.js';

// ---------------------------------------------------------------------------
// /overview (creator dashboard aggregate snapshot)
// ---------------------------------------------------------------------------

export async function fetchOverview(): Promise<unknown> {
  return request('/overview');
}

// ---------------------------------------------------------------------------
// /chapters (overview-scoped chapter list with optional range filter)
// ---------------------------------------------------------------------------

export async function fetchChapters(range?: string): Promise<unknown> {
  const query = range ? `?range=${encodeURIComponent(range)}` : '';
  return request(`/chapters${query}`);
}

// ---------------------------------------------------------------------------
// /production-records (per-chapter cost + LLM call log)
// ---------------------------------------------------------------------------

export interface ProductionRecordsOptions {
  chapterNum?: number;
  limit?: number;
}

export async function fetchProductionRecords(opts: ProductionRecordsOptions = {}): Promise<unknown> {
  const params = new URLSearchParams();
  if (opts.chapterNum != null) params.set('chapter_num', String(opts.chapterNum));
  if (opts.limit != null) params.set('limit', String(opts.limit));
  const q = params.toString();
  return request(`/production-records${q ? `?${q}` : ''}`);
}

// ---------------------------------------------------------------------------
// /production-records/rollup (aggregate stats)
// ---------------------------------------------------------------------------

export async function fetchProductionRollup(opts: { limit?: number } = {}): Promise<unknown> {
  const params = new URLSearchParams();
  if (opts.limit != null) params.set('limit', String(opts.limit));
  const q = params.toString();
  return request(`/production-records/rollup${q ? `?${q}` : ''}`);
}

// ---------------------------------------------------------------------------
// /production-records/trend (time-series cost trend)
// ---------------------------------------------------------------------------

export async function fetchProductionCostTrend(opts: { limit?: number } = {}): Promise<unknown> {
  const params = new URLSearchParams();
  if (opts.limit != null) params.set('limit', String(opts.limit));
  const q = params.toString();
  return request(`/production-records/trend${q ? `?${q}` : ''}`);
}

// ---------------------------------------------------------------------------
// /health (service liveness)
// ---------------------------------------------------------------------------

export async function fetchHealth(): Promise<unknown> {
  return request('/health');
}