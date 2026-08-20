/**
 * api/publish 独立测试（Phase 62.4）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  fetchCreatorChapterPreview,
  saveCreatorChapterBody,
  saveCreatorChapterOutline,
  submitCreatorPublish,
  fetchCreatorPublishHistory,
  fetchCreatorPublishPlatforms,
  exportCreatorEpub,
  exportCreatorDocx,
  generateCreatorVolumeSummary,
} from '../../src/api/publish.js';

const mocks = vi.hoisted(() => ({
  request: vi.fn(),
}));

vi.mock('../../src/api/core.js', () => ({
  request: (...args: unknown[]) => mocks.request(...args),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe('api/publish', () => {
  it('fetchCreatorChapterPreview GETs /creator/chapters/:n (no query by default)', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await fetchCreatorChapterPreview(5);
    expect(mocks.request).toHaveBeenCalledWith('/creator/chapters/5');
  });

  it('fetchCreatorChapterPreview with full=true adds ?full=1', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await fetchCreatorChapterPreview(5, { full: true });
    expect(mocks.request).toHaveBeenCalledWith('/creator/chapters/5?full=1');
  });

  it('saveCreatorChapterBody PUTs wrapped body', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await saveCreatorChapterBody(5, { text: 'foo' });
    expect(mocks.request).toHaveBeenCalledWith('/creator/chapters/5', {
      method: 'PUT',
      body: { body: { text: 'foo' } },
    });
  });

  it('saveCreatorChapterOutline PUTs wrapped outline', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await saveCreatorChapterOutline(5, { outline: 'foo' });
    expect(mocks.request).toHaveBeenCalledWith('/creator/chapters/5/outline', {
      method: 'PUT',
      body: { outline: { outline: 'foo' } },
    });
  });

  it('submitCreatorPublish POSTs body to /creator/publish', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await submitCreatorPublish({ platform: 'wechat' });
    expect(mocks.request).toHaveBeenCalledWith('/creator/publish', {
      method: 'POST',
      body: { platform: 'wechat' },
    });
  });

  it('fetchCreatorPublishHistory GETs with limit query', async () => {
    mocks.request.mockResolvedValueOnce({ history: [] });
    await fetchCreatorPublishHistory(20);
    expect(mocks.request).toHaveBeenCalledWith('/creator/publish/history?limit=20');
  });

  it('fetchCreatorPublishHistory default limit=10', async () => {
    mocks.request.mockResolvedValueOnce({ history: [] });
    await fetchCreatorPublishHistory();
    expect(mocks.request).toHaveBeenCalledWith('/creator/publish/history?limit=10');
  });

  it('fetchCreatorPublishPlatforms GETs /creator/publish/platforms', async () => {
    mocks.request.mockResolvedValueOnce({ platforms: [] });
    await fetchCreatorPublishPlatforms();
    expect(mocks.request).toHaveBeenCalledWith('/creator/publish/platforms');
  });

  it('generateCreatorVolumeSummary POSTs start/end_chapter to /creator/volume-summary/generate', async () => {
    mocks.request.mockResolvedValueOnce({ summary: 'foo' });
    await generateCreatorVolumeSummary({ startChapter: 1, endChapter: 30 });
    expect(mocks.request).toHaveBeenCalledWith('/creator/volume-summary/generate', {
      method: 'POST',
      body: { start_chapter: 1, end_chapter: 30 },
    });
  });

  it('exportCreatorEpub POSTs JSON via raw fetch and returns blob', async () => {
    const fakeBlob = new Blob(['fake']);
    const fetchSpy = vi.fn().mockResolvedValueOnce({ ok: true, blob: async () => fakeBlob });
    vi.stubGlobal('fetch', fetchSpy);
    try {
      const result = await exportCreatorEpub({ volume: 1 });
      expect(result).toBe(fakeBlob);
      const [url, init] = fetchSpy.mock.calls[0];
      expect(url).toMatch(/\/creator\/export\/epub$/);
      expect(init.method).toBe('POST');
      expect(init.headers).toEqual({ 'Content-Type': 'application/json' });
      expect(init.body).toBe(JSON.stringify({ volume: 1 }));
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it('exportCreatorEpub throws on non-ok response', async () => {
    const fetchSpy = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 500,
      text: async () => 'server error',
    });
    vi.stubGlobal('fetch', fetchSpy);
    try {
      await expect(exportCreatorEpub({ volume: 1 })).rejects.toThrow('API Error 500: server error');
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it('exportCreatorDocx POSTs JSON via raw fetch and returns blob', async () => {
    const fakeBlob = new Blob(['fake']);
    const fetchSpy = vi.fn().mockResolvedValueOnce({ ok: true, blob: async () => fakeBlob });
    vi.stubGlobal('fetch', fetchSpy);
    try {
      const result = await exportCreatorDocx({ volume: 1 });
      expect(result).toBe(fakeBlob);
      const [url, init] = fetchSpy.mock.calls[0];
      expect(url).toMatch(/\/creator\/export\/docx$/);
      expect(init.method).toBe('POST');
      expect(init.headers).toEqual({ 'Content-Type': 'application/json' });
      expect(init.body).toBe(JSON.stringify({ volume: 1 }));
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
