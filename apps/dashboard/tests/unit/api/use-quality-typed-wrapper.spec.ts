/**
 * Phase 126 v16.2.7 T1 URL contract regression test for quality.ts typed wrapper.
 *
 * Goal: lock the URL contract to `/studio/quality*` (relative to BASE_URL='/api')
 * so the /api/api/ URL duplication bug cannot regress (v16.2.1 §5.1 lesson 4).
 *
 * Scope: 4 wrapper functions covering the 3 studio quality endpoints plus the
 * `/quality/run` writing-space quality bridge (kept as a typed wrapper even
 * though the endpoint is not yet registered — see api/quality.ts).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as qualityApi from '@/api/quality';

describe('quality typed wrapper (v16.2.7 T1)', () => {
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

  // --- exports count: 4 wrappers (3 studio quality + 1 quality bridge) ---

  it('exports 4 wrapper functions', () => {
    const wrappers = Object.entries(qualityApi).filter(([, fn]) => typeof fn === 'function');
    expect(wrappers.length).toBe(4);
  });

  // --- static: no /api/ prefix in any wrapper body (TYPE-level regression lock) ---

  it('no wrapper body hardcodes /api/ prefix', () => {
    const wrappers = Object.entries(qualityApi).filter(([, fn]) => typeof fn === 'function');
    for (const [name, fn] of wrappers) {
      const src = fn.toString();
      expect(src, `${name} should not contain '/api/' prefix`).not.toMatch(/\/api\/studio/);
    }
  });

  // --- per-endpoint URL contract (runtime fetch capture) ---

  it('fetchQuality GETs /api/studio/quality', async () => {
    await qualityApi.fetchQuality();
    const [url] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/studio/quality');
  });

  it('fetchProseJudge GETs /api/studio/prose-judge', async () => {
    await qualityApi.fetchProseJudge();
    const [url] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/studio/prose-judge');
  });

  it('fetchProseDiff GETs /api/studio/prose-diff', async () => {
    await qualityApi.fetchProseDiff();
    const [url] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/studio/prose-diff');
  });

  it('runQualityCheck POSTs /api/quality/run', async () => {
    await qualityApi.runQualityCheck({ chapter_id: 1, body: '' });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/quality/run');
    expect(init.method).toBe('POST');
  });
});
