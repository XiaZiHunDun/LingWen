/**
 * Phase 23 Task 6 URL contract regression test for listStudioBatchJobs
 * typed wrapper.
 *
 * Goal: lock the URL contract to `/studio/batch/history?slug=X&limit=N` (relative
 * to BASE_URL='/api') so the /api/api/ URL duplication bug cannot regress
 * (Phase 126 v16.2.1 §5 lesson 4) and percent-encoding for special-character
 * slugs is enforced.
 *
 * Mocking strategy: mock global fetch and assert the URL passed to fetch is
 * `/api/studio/batch/history?slug=<encoded>&limit=<n>` (matches established
 * pattern from cancel-studio-batch-job.spec.ts).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { listStudioBatchJobs } from '@/api/studio';

describe('listStudioBatchJobs URL contract', () => {
  const originalFetch = globalThis.fetch;
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      json: async () => ({ jobs: [] }),
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('GETs /api/studio/batch/history?slug=<slug>&limit=<limit>', async () => {
    await listStudioBatchJobs('my-project', 20);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain('/api/studio/batch/history');
    expect(url).toContain('slug=my-project');
    expect(url).toContain('limit=20');
    expect(init.method).toBe('GET');
  });

  it('returns parsed jobs array', async () => {
    const body = {
      jobs: [
        {
          job_id: 'j1',
          slug: 'my-project',
          start_chapter: 1,
          end_chapter: 10,
          budget_usd: 0.15,
          mode: 'canon',
          status: 'completed',
          started_at: '2026-09-01T00:00:00Z',
          finished_at: '2026-09-01T00:10:00Z',
          exit_code: 0,
          error: null,
        },
        {
          job_id: 'j2',
          slug: 'my-project',
          start_chapter: 11,
          end_chapter: 20,
          budget_usd: 0.2,
          mode: 'pilot',
          status: 'failed',
          started_at: '2026-09-02T00:00:00Z',
          finished_at: null,
          exit_code: null,
          error: 'oops',
        },
      ],
    };
    fetchMock.mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      json: async () => body,
    });

    const result = await listStudioBatchJobs('my-project', 10);
    expect(result.jobs).toHaveLength(2);
    expect(result.jobs[0].job_id).toBe('j1');
    expect(result.jobs[0].status).toBe('completed');
    expect(result.jobs[1].status).toBe('failed');
  });

  it('percent-encodes slug with spaces + non-ASCII characters', async () => {
    await listStudioBatchJobs('项目 with spaces', 5);
    const [url] = fetchMock.mock.calls[0];
    // URLSearchParams encodes spaces as '+' (form-encoding); non-ASCII chars
    // get percent-encoded. The unencoded slug must NOT appear in the URL.
    expect(url).not.toContain('slug=项目 with spaces');
    expect(url).toContain('slug=%E9%A1%B9%E7%9B%AE');
    expect(url).toContain('+with+spaces');
  });

  it('uses default limit=20 when omitted', async () => {
    await listStudioBatchJobs('slug-only');
    const [url] = fetchMock.mock.calls[0];
    expect(url).toContain('limit=20');
  });
});