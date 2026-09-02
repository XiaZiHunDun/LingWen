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
  StudioBatchJobListResponseDTO,
  StudioBatchJobResponseDTO,
  StudioBatchTemplateCreateRequestDTO,
  StudioBatchTemplateDTO,
  StudioBatchTemplateListResponseDTO,
  StudioBatchTemplateUpdateRequestDTO,
  StudioPreflightResponseDTO,
  StudioProseDiffResponseDTO,
  StudioProseJudgeResponseDTO,
  StudioProjectsResponseDTO,
  StudioQualityReportResponseDTO,
  StudioQualityResponseDTO,
  StudioSummaryResponseDTO,
} from '@lingwen/dashboard-contracts/shared';
import { request } from './core.js';

// Re-export the Pilot batch DTOs so composables consume the app's contract
// boundary (@/api/studio) instead of reaching into the external contracts
// package directly (Phase 26+ P2-DTOMIGR).
export type {
  StudioBatchJobResponseDTO,
  StudioBatchJobSummaryDTO,
  StudioBatchTemplateDTO,
  StudioBatchTemplateCreateRequestDTO,
  StudioBatchTemplateListResponseDTO,
} from '@lingwen/dashboard-contracts/shared';

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
// /studio/batch/{id}/cancel (cancel a batch production job)
// ---------------------------------------------------------------------------

export async function cancelStudioBatchJob(
  jobId: string,
): Promise<StudioBatchJobResponseDTO> {
  const encoded = encodeURIComponent(jobId);
  const data = await request<StudioBatchJobResponseDTO>(
    `/studio/batch/${encoded}/cancel`,
    { method: 'POST' },
  );
  return data;
}

// ---------------------------------------------------------------------------
// /studio/batch/history?slug=X&limit=N (list recent batch jobs for a slug)
// ---------------------------------------------------------------------------

export async function listStudioBatchJobs(
  slug: string,
  limit: number = 20,
): Promise<StudioBatchJobListResponseDTO> {
  const params = new URLSearchParams({ slug, limit: String(limit) });
  const data = await request<StudioBatchJobListResponseDTO>(
    `/studio/batch/history?${params.toString()}`,
  );
  return data;
}

// ---------------------------------------------------------------------------
// /studio/batch/queue?slug=X (list queued, not-yet-started batch jobs)
// ---------------------------------------------------------------------------

export async function listStudioBatchQueue(
  slug: string,
): Promise<StudioBatchJobListResponseDTO> {
  const params = new URLSearchParams({ slug });
  const data = await request<StudioBatchJobListResponseDTO>(
    `/studio/batch/queue?${params.toString()}`,
  );
  return data;
}

// ---------------------------------------------------------------------------
// /studio/batch/templates (save / load reusable batch-run presets — Track B)
// ---------------------------------------------------------------------------

export async function listStudioBatchTemplates(
  slug?: string,
): Promise<StudioBatchTemplateListResponseDTO> {
  const params = new URLSearchParams();
  if (slug) params.set('slug', slug);
  const q = params.toString();
  const data = await request<StudioBatchTemplateListResponseDTO>(
    `/studio/batch/templates${q ? `?${q}` : ''}`,
  );
  return data;
}

export async function createStudioBatchTemplate(
  body: StudioBatchTemplateCreateRequestDTO,
): Promise<StudioBatchTemplateDTO> {
  const data = await request<StudioBatchTemplateDTO>('/studio/batch/templates', {
    method: 'POST',
    body,
  });
  return data;
}

export async function deleteStudioBatchTemplate(
  templateId: string,
): Promise<StudioBatchTemplateDTO> {
  const encoded = encodeURIComponent(templateId);
  const data = await request<StudioBatchTemplateDTO>(
    `/studio/batch/templates/${encoded}`,
    { method: 'DELETE' },
  );
  return data;
}
