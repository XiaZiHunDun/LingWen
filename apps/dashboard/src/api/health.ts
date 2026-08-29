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
 *
 * v16.5 #7: Promise<unknown> narrowed to concrete DTO types declared in
 * @lingwen/dashboard-contracts/shared/health.
 */
import type {
  ChaptersResponseDTO,
  HealthResponseDTO,
  OverviewResponseDTO,
  ProductionCostTrendResponseDTO,
  ProductionRecordsResponseDTO,
  ProductionRollupResponseDTO,
} from '@lingwen/dashboard-contracts/shared';
import { request } from './core.js';

// ---------------------------------------------------------------------------
// /overview (creator dashboard aggregate snapshot)
// ---------------------------------------------------------------------------

export async function fetchOverview(): Promise<OverviewResponseDTO> {
  const data = await request('/overview');
  return data as OverviewResponseDTO;
}

// ---------------------------------------------------------------------------
// /chapters (overview-scoped chapter list with optional range filter)
// ---------------------------------------------------------------------------

export async function fetchChapters(range?: string): Promise<ChaptersResponseDTO> {
  const query = range ? `?range=${encodeURIComponent(range)}` : '';
  const data = await request(`/chapters${query}`);
  return data as ChaptersResponseDTO;
}

// ---------------------------------------------------------------------------
// /production-records (per-chapter cost + LLM call log)
// ---------------------------------------------------------------------------

export interface ProductionRecordsOptions {
  chapterNum?: number;
  limit?: number;
}

export async function fetchProductionRecords(
  opts: ProductionRecordsOptions = {},
): Promise<ProductionRecordsResponseDTO> {
  const params = new URLSearchParams();
  if (opts.chapterNum != null) params.set('chapter_num', String(opts.chapterNum));
  if (opts.limit != null) params.set('limit', String(opts.limit));
  const q = params.toString();
  const data = await request(`/production-records${q ? `?${q}` : ''}`);
  return data as ProductionRecordsResponseDTO;
}

// ---------------------------------------------------------------------------
// /production-records/rollup (aggregate stats)
// ---------------------------------------------------------------------------

export async function fetchProductionRollup(
  opts: { limit?: number } = {},
): Promise<ProductionRollupResponseDTO> {
  const params = new URLSearchParams();
  if (opts.limit != null) params.set('limit', String(opts.limit));
  const q = params.toString();
  const data = await request(`/production-records/rollup${q ? `?${q}` : ''}`);
  return data as ProductionRollupResponseDTO;
}

// ---------------------------------------------------------------------------
// /production-records/trend (time-series cost trend)
// ---------------------------------------------------------------------------

export async function fetchProductionCostTrend(
  opts: { limit?: number } = {},
): Promise<ProductionCostTrendResponseDTO> {
  const params = new URLSearchParams();
  if (opts.limit != null) params.set('limit', String(opts.limit));
  const q = params.toString();
  const data = await request(`/production-records/trend${q ? `?${q}` : ''}`);
  return data as ProductionCostTrendResponseDTO;
}

// ---------------------------------------------------------------------------
// /health (service liveness)
// ---------------------------------------------------------------------------

export async function fetchHealth(): Promise<HealthResponseDTO> {
  const data = await request('/health');
  return data as HealthResponseDTO;
}
