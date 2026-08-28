/**
 * Content API client — typed wrapper around /creator/{overview,preferences,models,
 * logic-check,agent/plan,batch-history,chapters}* endpoints.
 *
 * Types come from @lingwen/dashboard-contracts/shared (which mirrors
 * packages/lingwen-shared Pydantic DTOs via codegen).
 *
 * Path convention: relative paths (no `/api/` prefix) — `core.js`'s `request()`
 * prepends `BASE_URL='/api'`.
 *
 * NOTE: This is a NEW typed wrapper added in v16.2.4 (Phase 126 T4).
 * Existing api/agent.js + api/mergePreset.js + api/publish.js + api/volumePlan.js
 * continue to handle backward-compatible calls. Future v16.2+ phases will switch
 * them over.
 *
 * Scope note: this wrapper covers 11 of 16 Content DTOs. The following 5 are
 * forward-compat stubs (no endpoint yet) and are NOT wrapped here:
 * - CreatorDashboardOverview (stubs/forward-compat, see shared/creator.py docstring)
 * - CreatorDashboardChapterPreview (stubs/forward-compat, same)
 * - CreatorUiProfileState (embedded as a field on CreatorOverviewResponse.ui_profile)
 * - CreatorUiProfileSaveRequest (no dedicated endpoint yet)
 *
 * Re-exports: all 16 are still re-exported from packages/dashboard-contracts so
 * callers can use them as types. Wrap when the endpoints land in a later phase.
 */
import type {
  CreatorAgentPlanRequest,
  CreatorAgentPlanResponse,
  CreatorBatchHistoryExportResponse,
  CreatorBatchHistoryResponse,
  CreatorBodySaveRequest,
  CreatorChapterPreview,
  CreatorLogicCheckResponse,
  CreatorModelsResponse,
  CreatorOutlineSaveRequest,
  CreatorOverviewResponse,
  CreatorPreferencesResponse,
  CreatorPreferencesSaveRequest,
} from '@lingwen/dashboard-contracts/shared';
import { request } from './core.js';

// ---------------------------------------------------------------------------
// /creator/overview
// ---------------------------------------------------------------------------

export async function fetchCreatorOverview(): Promise<CreatorOverviewResponse> {
  const data = await request('/creator/overview');
  return data as CreatorOverviewResponse;
}

// ---------------------------------------------------------------------------
// /creator/preferences (GET + PUT)
// ---------------------------------------------------------------------------

export async function fetchCreatorPreferences(): Promise<CreatorPreferencesResponse> {
  const data = await request('/creator/preferences');
  return data as CreatorPreferencesResponse;
}

export async function saveCreatorPreferences(
  req: CreatorPreferencesSaveRequest,
): Promise<CreatorPreferencesResponse> {
  const data = await request('/creator/preferences', {
    method: 'PUT',
    body: req,
  });
  return data as CreatorPreferencesResponse;
}

// ---------------------------------------------------------------------------
// /creator/models
// ---------------------------------------------------------------------------

export async function fetchCreatorModels(): Promise<CreatorModelsResponse> {
  const data = await request('/creator/models');
  return data as CreatorModelsResponse;
}

// ---------------------------------------------------------------------------
// /creator/logic-check (POST, optional ?chapter=N)
// ---------------------------------------------------------------------------

export async function runCreatorLogicCheck(
  chapter?: number,
): Promise<CreatorLogicCheckResponse> {
  const query = chapter != null ? `?chapter=${encodeURIComponent(String(chapter))}` : '';
  const data = await request(`/creator/logic-check${query}`, { method: 'POST' });
  return data as CreatorLogicCheckResponse;
}

// ---------------------------------------------------------------------------
// /creator/agent/plan (POST)
// ---------------------------------------------------------------------------

export async function runCreatorAgentPlan(
  req: CreatorAgentPlanRequest,
): Promise<CreatorAgentPlanResponse> {
  const data = await request('/creator/agent/plan', {
    method: 'POST',
    body: req,
  });
  return data as CreatorAgentPlanResponse;
}

// ---------------------------------------------------------------------------
// /creator/batch-history (GET + GET /export)
// ---------------------------------------------------------------------------

export async function fetchCreatorBatchHistory(): Promise<CreatorBatchHistoryResponse> {
  const data = await request('/creator/batch-history');
  return data as CreatorBatchHistoryResponse;
}

export async function exportCreatorBatchHistory(): Promise<CreatorBatchHistoryExportResponse> {
  const data = await request('/creator/batch-history/export');
  return data as CreatorBatchHistoryExportResponse;
}

// ---------------------------------------------------------------------------
// /creator/chapters/{n} (GET preview + PUT outline + PUT body)
// ---------------------------------------------------------------------------

export async function fetchCreatorChapterPreview(
  chapterNum: number,
  opts: { full?: boolean } = {},
): Promise<CreatorChapterPreview> {
  const query = opts.full ? '?full=1' : '';
  const data = await request(`/creator/chapters/${encodeURIComponent(String(chapterNum))}${query}`);
  return data as CreatorChapterPreview;
}

export async function saveCreatorChapterOutline(
  req: CreatorOutlineSaveRequest,
): Promise<CreatorChapterPreview> {
  const chapterNum = req.chapter_id;
  const data = await request(
    `/creator/chapters/${encodeURIComponent(String(chapterNum))}/outline`,
    { method: 'PUT', body: { outline: req.outline } },
  );
  return data as CreatorChapterPreview;
}

export async function saveCreatorChapterBody(
  req: CreatorBodySaveRequest,
): Promise<CreatorChapterPreview> {
  const chapterNum = req.chapter_id;
  const data = await request(
    `/creator/chapters/${encodeURIComponent(String(chapterNum))}`,
    { method: 'PUT', body: { body: req.body } },
  );
  return data as CreatorChapterPreview;
}
