/**
 * Phase 126 v16.2.7 T1 URL contract regression test for workspace.ts typed wrapper.
 *
 * Goal: lock the URL contract to `/write/*` (relative to BASE_URL='/api')
 * so the /api/api/ URL duplication bug cannot regress (v16.2.1 §5.1 lesson 4).
 *
 * Scope: 3 wrapper functions covering the 3 actual workspace endpoints.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as workspaceApi from '@/api/workspace';

describe('workspace typed wrapper (v16.2.7 T1)', () => {
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

  // --- exports count: 3 wrappers (matches real endpoints) ---

  it('exports 3 wrapper functions', () => {
    const wrappers = Object.entries(workspaceApi).filter(([, fn]) => typeof fn === 'function');
    expect(wrappers.length).toBe(3);
  });

  // --- static: no /api/ prefix in any wrapper body (TYPE-level regression lock) ---

  it('no wrapper body hardcodes /api/ prefix', () => {
    const wrappers = Object.entries(workspaceApi).filter(([, fn]) => typeof fn === 'function');
    for (const [name, fn] of wrappers) {
      const src = fn.toString();
      expect(src, `${name} should not contain '/api/' prefix`).not.toMatch(/\/api\/write/);
    }
  });

  // --- per-endpoint URL contract (runtime fetch capture) ---

  it('getChapter GETs /api/write/{chapterId}', async () => {
    await workspaceApi.getChapter(7);
    const [url] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/write/7');
  });

  it('saveChapter PUTs /api/write/{chapterId} with body', async () => {
    await workspaceApi.saveChapter(7, 'new content', 3);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/write/7');
    expect(init.method).toBe('PUT');
    expect(JSON.parse(init.body)).toEqual({ content: 'new content', base_revision: 3 });
  });

  it('detectConflict GETs /api/write/{chapterId}/conflict', async () => {
    await workspaceApi.detectConflict(7);
    const [url] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/write/7/conflict');
  });
});
