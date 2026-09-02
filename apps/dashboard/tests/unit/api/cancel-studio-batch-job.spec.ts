import { describe, expect, it, vi } from 'vitest';
import { cancelStudioBatchJob } from '@/api/studio';

interface CapturedCall { url: string; method: string; }

function mockFetch(returnBody: unknown, status = 200) {
  return vi.fn(async (url: string, init?: RequestInit): Promise<Response> => {
    const captured: CapturedCall = { url, method: init?.method ?? 'GET' };
    (globalThis as { __lastCall?: CapturedCall }).__lastCall = captured;
    return new Response(JSON.stringify(returnBody), {
      status,
      headers: { 'content-type': 'application/json' },
    });
  });
}

describe('cancelStudioBatchJob URL contract', () => {
  it('POSTs to /api/studio/batch/<job_id>/cancel', async () => {
    const fetchMock = mockFetch({ job_id: 'abc-123', status: 'cancelled' });
    vi.stubGlobal('fetch', fetchMock);

    await cancelStudioBatchJob('abc-123');

    const call = (globalThis as { __lastCall?: CapturedCall }).__lastCall;
    expect(call?.method).toBe('POST');
    expect(call?.url).toBe('/api/studio/batch/abc-123/cancel');
    vi.unstubAllGlobals();
  });

  it('returns parsed StudioBatchJobResponseDTO', async () => {
    const body = { job_id: 'xyz-789', status: 'cancelled', mode: 'pilot' };
    const fetchMock = mockFetch(body);
    vi.stubGlobal('fetch', fetchMock);

    const result = await cancelStudioBatchJob('xyz-789');
    expect(result.job_id).toBe('xyz-789');
    expect(result.status).toBe('cancelled');
    vi.unstubAllGlobals();
  });

  it('encodes special characters in job_id', async () => {
    const fetchMock = mockFetch({ status: 'cancelled' });
    vi.stubGlobal('fetch', fetchMock);

    await cancelStudioBatchJob('job with spaces / & special');

    const call = (globalThis as { __lastCall?: CapturedCall }).__lastCall;
    expect(call?.url).toContain('job%20with%20spaces');
    vi.unstubAllGlobals();
  });
});