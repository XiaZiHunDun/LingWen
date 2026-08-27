/**
 * Phase 126 v16.2.1 Task 3.4 part 1 smoke test for volume.ts typed wrapper.
 *
 * Goal: lock the URL contract to `/creator/volume-plan*` (relative to BASE_URL='/api')
 * so the /api/api/ URL duplication bug cannot regress.
 *
 * NOTE: this test pre-dates the v16.2.7 typed-wrapper cleanup; if those
 * wrappers gain a /api prefix convention, this will need to be re-baselined.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  diffVolumePlan,
  fetchVolumePlan,
  mergeVolumePlan,
  saveVolumePlan,
  splitVolumePlan,
} from '@/api/volume';

describe('volume typed wrapper (v16.2.1 Task 3.4 part 1)', () => {
  const originalFetch = globalThis.fetch;
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      json: async () => ({
        slug: 'demo',
        global_outline_path: '/tmp/outline.md',
        state_path: '/tmp/state.json',
        revision: 'r1',
        volumes: [],
        locked_volume_count: 0,
        deviations: [],
        deviation_count: 0,
        alert_count: 0,
      }),
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('fetchVolumePlan GETs /api/creator/volume-plan (no /api/api duplication)', async () => {
    await fetchVolumePlan();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/volume-plan');
  });

  it('saveVolumePlan PUTs to /api/creator/volume-plan with object body', async () => {
    await saveVolumePlan({ volumes: [], expected_revision: 'rev-1' });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/creator/volume-plan');
    expect(init.method).toBe('PUT');
    expect(JSON.parse(init.body)).toEqual({ volumes: [], expected_revision: 'rev-1' });
  });

  it('diffVolumePlan POSTs /api/creator/volume-plan/diff', async () => {
    await diffVolumePlan({ volumes: [] });
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/volume-plan/diff');
  });

  it('mergeVolumePlan POSTs /api/creator/volume-plan/merge', async () => {
    await mergeVolumePlan({ volumes: [], start_index: 0, end_index: 1 });
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/volume-plan/merge');
  });

  it('splitVolumePlan POSTs /api/creator/volume-plan/split', async () => {
    await splitVolumePlan({ volumes: [], volume_index: 0, split_at_chapter: 2 });
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/volume-plan/split');
  });
});
