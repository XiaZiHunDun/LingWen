/**
 * Studio API client — typed wrapper around /studio/* endpoints.
 *
 * Path convention: relative paths (no `/api/` prefix) — `core.js`'s `request()`
 * prepends `BASE_URL='/api'`.
 *
 * NOTE: This is a NEW typed wrapper added in v16.2.8 (Phase 126 cleanup).
 * Existing api/studio.js continues to handle backward-compatible calls.
 * v16.2.8 T5 deletes api/studio.js after consumers migrate.
 */
import { request } from './core.js';

// ---------------------------------------------------------------------------
// /studio/projects (list all projects in studio)
// ---------------------------------------------------------------------------

export async function listStudioProjects(): Promise<unknown> {
  return request('/studio/projects');
}

// ---------------------------------------------------------------------------
// /studio/active (set the active studio project by slug)
// ---------------------------------------------------------------------------

export async function setStudioActive(slug: string): Promise<unknown> {
  return request('/studio/active', { method: 'PUT', body: { slug } });
}

// ---------------------------------------------------------------------------
// /studio/summary (current project studio summary)
// ---------------------------------------------------------------------------

export async function fetchStudioSummary(): Promise<unknown> {
  return request('/studio/summary');
}

// ---------------------------------------------------------------------------
// /studio/quality (current quality scores)
// ---------------------------------------------------------------------------

export async function fetchStudioQuality(): Promise<unknown> {
  return request('/studio/quality');
}

// ---------------------------------------------------------------------------
// /studio/quality-report (detailed quality report by severity)
// ---------------------------------------------------------------------------

export async function fetchStudioQualityReport(): Promise<unknown> {
  return request('/studio/quality-report');
}

// ---------------------------------------------------------------------------
// /studio/prose-diff (prose-diff snapshot)
// ---------------------------------------------------------------------------

export async function fetchStudioProseDiff(): Promise<unknown> {
  return request('/studio/prose-diff');
}

// ---------------------------------------------------------------------------
// /studio/prose-judge (prose judge scorecard)
// ---------------------------------------------------------------------------

export async function fetchStudioProseJudge(): Promise<unknown> {
  return request('/studio/prose-judge');
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
): Promise<unknown> {
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

export async function studioProductionRun(req: StudioProductionRunRequest): Promise<unknown> {
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

// ---------------------------------------------------------------------------
// /studio/production/jobs/active (current in-flight batch job)
// ---------------------------------------------------------------------------

export async function fetchStudioActiveBatchJob(): Promise<unknown> {
  return request('/studio/production/jobs/active');
}

// ---------------------------------------------------------------------------
// /studio/production/jobs/{id} (single batch job status)
// ---------------------------------------------------------------------------

export async function fetchStudioBatchJob(jobId: string): Promise<unknown> {
  return request(`/studio/production/jobs/${encodeURIComponent(jobId)}`);
}