/**
 * Phase 23 Task 5 URL contract regression test for cancelStudioBatchJob
 * typed wrapper.
 *
 * Goal: lock the URL contract to `/studio/batch/<id>/cancel` (relative to
 * BASE_URL='/api') so the /api/api/ URL duplication bug cannot regress
 * (Phase 126 v16.2.1 §5 lesson 4).
 *
 * Mocking strategy: mock global fetch and assert the URL passed to fetch is
 * `/api/studio/batch/<id>/cancel` (matches existing typed-wrapper tests in
 * use-{content,volume,quality,...}-typed-wrapper.spec.ts).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cancelStudioBatchJob } from '@/api/studio';

describe('cancelStudioBatchJob URL contract', () => {
  const originalFetch = globalThis.fetch;
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      json: async () => ({ job_id: 'abc-123', status: 'cancelled' }),
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('POSTs to /api/studio/batch/<job_id>/cancel (no /api/api duplication)', async () => {
    await cancelStudioBatchJob('abc-123');
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/studio/batch/abc-123/cancel');
    expect(init.method).toBe('POST');
  });

  it('returns parsed StudioBatchJobResponseDTO', async () => {
    const body = { job_id: 'xyz-789', status: 'cancelled', mode: 'pilot' };
    fetchMock.mockResolvedValue({
      ok: true,
      status: 200,
        statusText: 'OK',
      json: async () => body,
    });

    const result = await cancelStudioBatchJob('xyz-789');
    expect(result.job_id).toBe('xyz-789');
    expect(result.status).toBe('cancelled');
  });

  it('encodes special characters in job_id', async () => {
    await cancelStudioBatchJob('job with spaces / & special');
    const [url] = fetchMock.mock.calls[0];
    expect(url).toContain('job%20with%20spaces');
  });
});