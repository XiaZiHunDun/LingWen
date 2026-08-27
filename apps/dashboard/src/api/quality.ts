/**
 * Quality API client — typed wrapper around /api/studio/quality* endpoints.
 *
 * NOTE: This is a NEW typed wrapper added in v16.1 (Phase 124 T4).
 * Existing api/studio.js continues to handle backward-compatible calls.
 */
import type { QualityScoreDTO, ProseJudgeDTO, ProseDiffDTO } from '@lingwen/dashboard-contracts/shared';
import { request } from './core.js';

export async function fetchQuality(): Promise<QualityScoreDTO> {
  const data = await request('/api/studio/quality');
  return data as QualityScoreDTO;
}

export async function fetchProseJudge(): Promise<ProseJudgeDTO> {
  const data = await request('/api/studio/prose-judge');
  return data as ProseJudgeDTO;
}

export async function fetchProseDiff(): Promise<ProseDiffDTO> {
  const data = await request('/api/studio/prose-diff');
  return data as ProseDiffDTO;
}
