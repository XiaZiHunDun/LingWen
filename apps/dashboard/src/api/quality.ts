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

// ---------------------------------------------------------------------------
// /quality/run (POST) — 写作空间质量桥（章节正文行内 P0/P1 标注）
// 注意：该端点目前在后端 `/api/quality/run` 尚未注册（计划 Task 23 未交付）。
// 保留 typed wrapper 以维持调用约定一致；后端端点落地前调用会 404。
// ---------------------------------------------------------------------------

export interface QualityCheckAnnotation {
  sceneId: string;
  offset: number;
  severity: 'P0' | 'P1' | 'P2';
  rule: string;
  msg: string;
}

export interface QualityCheckResult {
  annotations: QualityCheckAnnotation[];
}

export async function runQualityCheck(req: { chapter_id: number; body: string }): Promise<QualityCheckResult> {
  const data = await request('/quality/run', { method: 'POST', body: req });
  return data as QualityCheckResult;
}
