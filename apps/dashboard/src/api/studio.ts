/**
 * Studio API client — typed wrapper around /studio/* endpoints.
 *
 * Path convention: relative paths (no `/api/` prefix) — `core.js`'s `request()`
 * prepends `BASE_URL='/api'`.
 *
 * NOTE: This is a NEW typed wrapper added in v16.2.8 (Phase 126 cleanup).
 * Existing api/studio.js continues to handle backward-compatible calls.
 * v16.2.8 T5 deletes api/studio.js after consumers migrate.
 *
 * v16.5 #7: Promise<unknown> narrowed to concrete DTO types declared in
 * @lingwen/dashboard-contracts/shared/studio.
 */
import type {
  StudioActiveResponseDTO,
  StudioBatchJobResponseDTO,
  StudioPreflightResponseDTO,
  StudioProseDiffResponseDTO,
  StudioProseJudgeResponseDTO,
  StudioProjectsResponseDTO,
  StudioQualityReportResponseDTO,
  StudioQualityResponseDTO,
  StudioSummaryResponseDTO,
} from '@lingwen/dashboard-contracts/shared';
import { request } from './core.js';

// ---------------------------------------------------------------------------
// /studio/active (set the active studio project by slug)
// ---------------------------------------------------------------------------

export async function setStudioActive(slug: string): Promise<StudioActiveResponseDTO> {
  const data = await request('/studio/active', { method: 'PUT', body: { slug } });
  return data as StudioActiveResponseDTO;
}

// ---------------------------------------------------------------------------
// /studio/summary (current project studio summary)
// ---------------------------------------------------------------------------

export async function fetchStudioSummary(): Promise<StudioSummaryResponseDTO> {
  const data = await request('/studio/summary');
  return data as StudioSummaryResponseDTO;
}

// ---------------------------------------------------------------------------
// /studio/quality (current quality scores)
// ---------------------------------------------------------------------------

export async function fetchStudioQuality(): Promise<StudioQualityResponseDTO> {
  const data = await request('/studio/quality');
  return data as StudioQualityResponseDTO;
}

// ---------------------------------------------------------------------------
// /studio/quality-report (detailed quality report by severity)
// ---------------------------------------------------------------------------

export async function fetchStudioQualityReport(): Promise<StudioQualityReportResponseDTO> {
  const data = await request('/studio/quality-report');
  return data as StudioQualityReportResponseDTO;
}

// ---------------------------------------------------------------------------
// /studio/prose-diff (prose-diff snapshot)
// ---------------------------------------------------------------------------

export async function fetchStudioProseDiff(): Promise<StudioProseDiffResponseDTO> {
  const data = await request('/studio/prose-diff');
  return data as StudioProseDiffResponseDTO;
}

// ---------------------------------------------------------------------------
// /studio/prose-judge (prose judge scorecard)
// ---------------------------------------------------------------------------

export async function fetchStudioProseJudge(): Promise<StudioProseJudgeResponseDTO> {
  const data = await request('/studio/prose-judge');
  return data as StudioProseJudgeResponseDTO;
}

// ---------------------------------------------------------------------------
// /studio/production/preflight (dry-run batch preflight check)
// ---------------------------------------------------------------------------

export interface StudioProductionPreflightRequest {
  start_chapter: number;
  end_chapter: number;
  budget_usd?: number;
  mode?: string;
}

export async function studioProductionPreflight(
  req: StudioProductionPreflightRequest,
): Promise<StudioPreflightResponseDTO> {
  const params = new URLSearchParams();
  if (req.budget_usd != null) params.set('budget_usd', String(req.budget_usd));
  const q = params.toString();
  const data = await request(`/studio/production/preflight${q ? `?${q}` : ''}`, {
    method: 'POST',
    body: {
      start_chapter: req.start_chapter,
      end_chapter: req.end_chapter,
      mode: req.mode || 'canon',
    },
  });
  return data as StudioPreflightResponseDTO;
}

// ---------------------------------------------------------------------------
// /studio/production/run (start a batch production run)
// ---------------------------------------------------------------------------

export interface StudioProductionRunRequest {
  start_chapter: number;
  end_chapter: number;
  budget_usd?: number;
  mode?: string;
  skip_preflight?: boolean;
}

export async function studioProductionRun(
  req: StudioProductionRunRequest,
): Promise<StudioBatchJobResponseDTO> {
  const data = await request('/studio/production/run', {
    method: 'POST',
    body: {
      start_chapter: req.start_chapter,
      end_chapter: req.end_chapter,
      mode: req.mode || 'canon',
      budget_usd: req.budget_usd ?? 0.15,
      skip_preflight: Boolean(req.skip_preflight),
    },
  });
  return data as StudioBatchJobResponseDTO;
}

// ---------------------------------------------------------------------------
// /studio/production/jobs/active (current in-flight batch job)
// ---------------------------------------------------------------------------

export async function fetchStudioActiveBatchJob(): Promise<StudioBatchJobResponseDTO | null> {
  const data = await request('/studio/production/jobs/active');
  return data as StudioBatchJobResponseDTO | null;
}

// ---------------------------------------------------------------------------
// /studio/production/jobs/{id} (single batch job status)
// ---------------------------------------------------------------------------

export async function fetchStudioBatchJob(jobId: string): Promise<StudioBatchJobResponseDTO> {
  const data = await request(`/studio/production/jobs/${encodeURIComponent(jobId)}`);
  return data as StudioBatchJobResponseDTO;
}

// ---------------------------------------------------------------------------
// /studio/batch/{id}/cancel (cancel a batch production job)
// ---------------------------------------------------------------------------

export async function cancelStudioBatchJob(
  jobId: string,
): Promise<StudioBatchJobResponseDTO> {
  const encoded = encodeURIComponent(jobId);
  const res = await fetch(`/api/studio/batch/${encoded}/cancel`, { method: 'POST' });
  const data = await res.json();
  return data as StudioBatchJobResponseDTO;
}
