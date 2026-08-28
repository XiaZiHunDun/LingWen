/**
 * Phase 126 v16.2.4 Task T4 URL contract regression test for content.ts
 * typed wrapper.
 *
 * Goal: lock the URL contract to `/creator/{overview,preferences,models,
 * logic-check,agent/plan,batch-history,chapters}*` (relative to BASE_URL='/api')
 * so the /api/api/ URL duplication bug cannot regress (v16.2.1 lesson:
 * world.ts/workspace.ts/quality.ts carry this bug to v16.2.7; this wrapper is
 * being authored AFTER the fix so it must NOT regress).
 *
 * Scope: 11 wrapper functions covering the 11 actual content endpoints.
 * The 5 forward-compat Content DTOs (CreatorDashboardOverview,
 * CreatorDashboardChapterPreview, CreatorUiProfileState,
 * CreatorUiProfileSaveRequest) are NOT wrapped yet — see content.ts JSDoc.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as contentApi from '@/api/content';

describe('content typed wrapper (v16.2.4 Task T4)', () => {
  const originalFetch = globalThis.fetch;
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      json: async () => ({}),
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  // --- exports count: 12 wrappers (matches real endpoints) ---

  it('exports 13 wrapper functions', () => {  // v16.2.8 T2.5: added runCreatorAgentPlanStream (was 12)
    const wrappers = Object.entries(contentApi).filter(([, fn]) => typeof fn === 'function');
    expect(wrappers.length).toBe(13);
  });

  // --- static: no /api/ prefix in any wrapper body (TYPE-level regression lock) ---

  it('no wrapper body hardcodes /api/ prefix', () => {
    const wrappers = Object.entries(contentApi).filter(([, fn]) => typeof fn === 'function');
    for (const [name, fn] of wrappers) {
      const src = fn.toString();
      expect(src, `${name} should not contain '/api/' prefix`).not.toMatch(/\/api\/creator/);
      // v16.2.8 T2.5: runCreatorAgentPlanStream uses raw fetch() for SSE
      // streaming (cannot use request() which buffers the full response).
      if (name !== 'runCreatorAgentPlanStream') {
        expect(src, `${name} should not contain 'fetch(' direct`).not.toMatch(/\bfetch\(/);
      }
    }
  });

  // --- per-endpoint URL contract (runtime fetch capture) ---

  it('fetchCreatorOverview GETs /api/creator/overview (no /api/api duplication)', async () => {
    await contentApi.fetchCreatorOverview();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/overview');
  });

  it('fetchCreatorPreferences GETs /api/creator/preferences', async () => {
    await contentApi.fetchCreatorPreferences();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/preferences');
  });

  it('saveCreatorPreferences PUTs /api/creator/preferences', async () => {
    await contentApi.saveCreatorPreferences({ creation_mode: 'studio' });
    const url = fetchMock.mock.calls[0][0];
    const opts = fetchMock.mock.calls[0][1];
    expect(url).toBe('/api/creator/preferences');
    expect(opts.method).toBe('PUT');
  });

  it('fetchCreatorModels GETs /api/creator/models', async () => {
    await contentApi.fetchCreatorModels();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/models');
  });

  it('runCreatorLogicCheck POSTs /api/creator/logic-check (no chapter)', async () => {
    await contentApi.runCreatorLogicCheck();
    const url = fetchMock.mock.calls[0][0];
    const opts = fetchMock.mock.calls[0][1];
    expect(url).toBe('/api/creator/logic-check');
    expect(opts.method).toBe('POST');
  });

  it('runCreatorLogicCheck POSTs /api/creator/logic-check?chapter=N when given', async () => {
    await contentApi.runCreatorLogicCheck(42);
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/logic-check?chapter=42');
  });

  it('runCreatorAgentPlan POSTs /api/creator/agent/plan', async () => {
    await contentApi.runCreatorAgentPlan({ action_label: 'plan' });
    const url = fetchMock.mock.calls[0][0];
    const opts = fetchMock.mock.calls[0][1];
    expect(url).toBe('/api/creator/agent/plan');
    expect(opts.method).toBe('POST');
  });

  it('fetchCreatorBatchHistory GETs /api/creator/batch-history', async () => {
    await contentApi.fetchCreatorBatchHistory();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/batch-history');
  });

  it('exportCreatorBatchHistory GETs /api/creator/batch-history/export', async () => {
    await contentApi.exportCreatorBatchHistory();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/batch-history/export');
  });

  it('fetchCreatorChapterPreview GETs /api/creator/chapters/{n}', async () => {
    await contentApi.fetchCreatorChapterPreview(42);
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/chapters/42');
  });

  it('fetchCreatorChapterPreview appends ?full=1 when opts.full', async () => {
    await contentApi.fetchCreatorChapterPreview(42, { full: true });
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/chapters/42?full=1');
  });

  it('saveCreatorChapterOutline PUTs /api/creator/chapters/{n}/outline', async () => {
    await contentApi.saveCreatorChapterOutline({ chapter_id: 42, outline: 'text' });
    const url = fetchMock.mock.calls[0][0];
    const opts = fetchMock.mock.calls[0][1];
    expect(url).toBe('/api/creator/chapters/42/outline');
    expect(opts.method).toBe('PUT');
  });

  it('saveCreatorChapterBody PUTs /api/creator/chapters/{n}', async () => {
    await contentApi.saveCreatorChapterBody({ chapter_id: 42, body: 'text' });
    const url = fetchMock.mock.calls[0][0];
    const opts = fetchMock.mock.calls[0][1];
    expect(url).toBe('/api/creator/chapters/42');
    expect(opts.method).toBe('PUT');
  });
});
