/**
 * Quality API client — typed wrapper around /studio/quality* endpoints.
 *
 * Path convention: relative paths (no `/api/` prefix) — `core.js`'s `request()`
 * prepends `BASE_URL='/api'`.
 *
 * NOTE: This is a typed wrapper added in v16.1 (Phase 124 T4) and fixed in
 * v16.2.7 (Phase 126 cleanup) to drop the `/api/` prefix per v16.2.1 §5.1
 * lesson 4. Existing api/studio.js continues to handle backward-compatible
 * calls.
 */
import type { QualityScoreDTO, ProseJudgeDTO, ProseDiffDTO } from '@lingwen/dashboard-contracts/shared';
import { request } from './core.js';

export async function fetchQuality(): Promise<QualityScoreDTO> {
  const data = await request('/studio/quality');
  return data as QualityScoreDTO;
}

export async function fetchProseJudge(): Promise<ProseJudgeDTO> {
  const data = await request('/studio/prose-judge');
  return data as ProseJudgeDTO;
}

export async function fetchProseDiff(): Promise<ProseDiffDTO> {
  const data = await request('/studio/prose-diff');
  return data as ProseDiffDTO;
}
