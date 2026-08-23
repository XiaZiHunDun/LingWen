/**
 * Studio API
 * (12 funcs)
 */

import { request } from './core.js';

export async function fetchStudioProjects() {
  return request('/studio/projects');
}

export async function fetchStudioActive() {
  return request('/studio/active');
}

export async function setStudioActive(slug) {
  return request('/studio/active', { method: 'PUT', body: { slug } });
}

export async function fetchStudioSummary() {
  return request('/studio/summary');
}

export async function fetchStudioQuality() {
  return request('/studio/quality');
}

export async function fetchStudioQualityReport() {
  return request('/studio/quality-report');
}

export async function fetchStudioProseDiff() {
  return request('/studio/prose-diff');
}

export async function fetchStudioProseJudge() {
  return request('/studio/prose-judge');
}

export async function studioProductionPreflight(req) {
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

export async function studioProductionRun(req) {
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

export async function fetchStudioActiveBatchJob() {
  return request('/studio/production/jobs/active');
}

export async function fetchStudioBatchJob(jobId) {
  return request(`/studio/production/jobs/${encodeURIComponent(jobId)}`);
}
