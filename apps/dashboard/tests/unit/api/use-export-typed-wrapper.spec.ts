/**
 * Phase 126 v16.2.5 Task T3.b URL contract regression test for export.ts
 * typed wrapper.
 *
 * Goal: lock the URL contract to `/creator/export/{epub,docx}` and
 * `/creator/publish/{,platforms,history}` (relative to BASE_URL='/api')
 * so the /api/api/ URL duplication bug cannot regress (v16.2.1 lesson).
 *
 * Scope: 5 wrapper functions covering the 5 actual export + publish endpoints.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as exportApi from '@/api/export';

describe('export typed wrapper (v16.2.5 Task T3)', () => {
  const originalFetch = globalThis.fetch;
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      json: async () => ({}),
      blob: async () => new Blob([new Uint8Array([1, 2, 3])]),
      text: async () => '',
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  // --- exports count: 5 wrappers (matches real endpoints) ---

  it('exports 5 wrapper functions', () => {
    const wrappers = Object.entries(exportApi).filter(([, fn]) => typeof fn === 'function');
    expect(wrappers.length).toBe(5);
  });

  // --- static: no /api/ prefix in any wrapper body (TYPE-level regression lock) ---

  it('no wrapper body hardcodes /api/ prefix', () => {
    const wrappers = Object.entries(exportApi).filter(([, fn]) => typeof fn === 'function');
    for (const [name, fn] of wrappers) {
      const src = fn.toString();
      expect(src, `${name} should not contain '/api/' prefix`).not.toMatch(/\/api\/creator/);
    }
  });

  // --- per-endpoint URL contract (runtime fetch capture) ---

  it('exportCreatorEpub POSTs /api/creator/export/epub with JSON body', async () => {
    await exportApi.exportCreatorEpub({ mode: 'full' });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/creator/export/epub');
    expect(init.method).toBe('POST');
    expect(init.headers['Content-Type']).toBe('application/json');
    expect(JSON.parse(init.body)).toEqual({ mode: 'full' });
  });

  it('exportCreatorDocx POSTs /api/creator/export/docx with JSON body', async () => {
    await exportApi.exportCreatorDocx({
      mode: 'range',
      start_chapter: 1,
      end_chapter: 10,
    });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/creator/export/docx');
    expect(init.method).toBe('POST');
    expect(JSON.parse(init.body)).toEqual({
      mode: 'range',
      start_chapter: 1,
      end_chapter: 10,
    });
  });

  it('submitCreatorPublish POSTs /api/creator/publish with JSON body', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        id: 'p1',
        platform: 'fanqie',
        include_outline: true,
        mode: 'submission',
        status: 'queued',
        message: 'OK',
        created_at: '2026-08-28',
      }),
    });
    await exportApi.submitCreatorPublish({ platform: 'fanqie', intro: 'test' });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/creator/publish');
    expect(init.method).toBe('POST');
    expect(JSON.parse(init.body)).toEqual({ platform: 'fanqie', intro: 'test' });
  });

  it('fetchCreatorPublishPlatforms GETs /api/creator/publish/platforms', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        slug: 'test',
        platforms: [
          { id: 'fanqie', label: '番茄小说', connection: 'stub', capabilities: {} },
        ],
      }),
    });
    await exportApi.fetchCreatorPublishPlatforms();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/publish/platforms');
  });

  it('fetchCreatorPublishHistory with limit adds ?limit=N', async () => {
    await exportApi.fetchCreatorPublishHistory(30);
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/publish/history?limit=30');
  });

  it('fetchCreatorPublishHistory without limit sends default ?limit=10', async () => {
    // Per v16.2.4 §5.1 lesson 4 (typed wrapper params forwarding fragility):
    // default limit=10 forwards ?limit=10 to API — preserves original publish.js behavior.
    await exportApi.fetchCreatorPublishHistory();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/publish/history?limit=10');
  });
});
