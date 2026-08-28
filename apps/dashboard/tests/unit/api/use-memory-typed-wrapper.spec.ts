/**
 * Phase 126 v16.2.6 Task T3.b URL contract regression test for memory.ts
 * typed wrapper.
 *
 * Goal: lock the URL contract to `/creator/memory-assets*` and
 * `/creator/memory/query` (relative to BASE_URL='/api') so the /api/api/ URL
 * duplication bug cannot regress (v16.2.1 lesson 5).
 *
 * Scope: 3 wrapper functions covering the 3 actual memory endpoints.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as memoryApi from '@/api/memory';

describe('memory typed wrapper (v16.2.6 Task T3)', () => {
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
    const wrappers = Object.entries(memoryApi).filter(([, fn]) => typeof fn === 'function');
    expect(wrappers.length).toBe(3);
  });

  // --- static: no /api/ prefix, no raw fetch (regression lock) ---

  it('no wrapper body hardcodes /api/ prefix or raw fetch', () => {
    const wrappers = Object.entries(memoryApi).filter(([, fn]) => typeof fn === 'function');
    for (const [name, fn] of wrappers) {
      const src = fn.toString();
      expect(src, `${name} should not contain '/api/' prefix`).not.toMatch(/\/api\/creator/);
      expect(src, `${name} should not contain 'fetch(' direct`).not.toMatch(/\bfetch\(/);
    }
  });

  // --- per-endpoint URL contract (runtime fetch capture) ---

  it('fetchCreatorMemoryAssets GETs /api/creator/memory-assets', async () => {
    await memoryApi.fetchCreatorMemoryAssets();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/memory-assets');
  });

  it('saveCreatorMemoryAnnotation PUTs /api/creator/memory-assets/{id}/annotation', async () => {
    await memoryApi.saveCreatorMemoryAnnotation('memory-ch-1', { pinned: true });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/creator/memory-assets/memory-ch-1/annotation');
    expect(init.method).toBe('PUT');
    expect(JSON.parse(init.body)).toEqual({ pinned: true });
  });

  it('saveCreatorMemoryAnnotation percent-encodes the asset id', async () => {
    await memoryApi.saveCreatorMemoryAnnotation('memory-char-李逍遥/x', { note: 'n' });
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe(
      `/api/creator/memory-assets/${encodeURIComponent('memory-char-李逍遥/x')}/annotation`,
    );
    expect(url).not.toContain('/x/annotation');
  });

  it('queryCreatorMemory POSTs /api/creator/memory/query with JSON body', async () => {
    await memoryApi.queryCreatorMemory({ query: '李逍遥', scope: 'character', top_k: 5 });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/creator/memory/query');
    expect(init.method).toBe('POST');
    expect(JSON.parse(init.body)).toEqual({ query: '李逍遥', scope: 'character', top_k: 5 });
  });
});
