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
  approveVolumeTemplateApproval,
  deleteFactoryVolumeTemplate,
  deleteVolumeTemplate,
  diffVolumePlan,
  fetchVolumePlan,
  fetchVolumeTemplateApprovalHistory,
  fetchVolumeTemplateApprovalSnapshotDiff,
  fetchVolumeTemplateApprovalSnapshotDrift,
  fetchVolumeTemplateChangelog,
  mergeVolumePlan,
  rejectVolumeTemplateApproval,
  renameVolumeTemplate,
  rollbackVolumeTemplate,
  saveVolumePlan,
  setVolumeTemplateVersion,
  splitVolumePlan,
  submitVolumeTemplateApproval,
  transferVolumeTemplateApproval,
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

  // --- regression: 11 paths that previously still had /api/ prefix (Phase 126 follow-up) ---

  it('setVolumeTemplateVersion constructs URL without /api/api/ duplication', async () => {
    await setVolumeTemplateVersion('abc', { version_label: 'v1' });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/creator/volume-plan/templates/abc/version');
    expect(init.method).toBe('PUT');
  });

  it('fetchVolumeTemplateChangelog constructs URL without /api/api/ duplication', async () => {
    await fetchVolumeTemplateChangelog('abc');
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/volume-plan/templates/abc/version-changelog');
  });

  it('rollbackVolumeTemplate constructs URL without /api/api/ duplication', async () => {
    await rollbackVolumeTemplate('abc', { version_label: 'v1' });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/creator/volume-plan/templates/abc/version-rollback');
    expect(init.method).toBe('POST');
  });

  it('fetchVolumeTemplateApprovalHistory constructs URL without /api/api/ duplication', async () => {
    await fetchVolumeTemplateApprovalHistory(50);
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/volume-plan/templates/approvals/history?limit=50');
  });

  it('submitVolumeTemplateApproval constructs URL without /api/api/ duplication', async () => {
    await submitVolumeTemplateApproval('abc', { submit_note: 'r' });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/creator/volume-plan/templates/abc/version-approval');
    expect(init.method).toBe('POST');
  });

  it('approveVolumeTemplateApproval constructs URL without /api/api/ duplication', async () => {
    await approveVolumeTemplateApproval('ap-1', { resolve_note: 'ok' });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/creator/volume-plan/templates/approvals/ap-1/approve');
    expect(init.method).toBe('POST');
  });

  it('rejectVolumeTemplateApproval constructs URL without /api/api/ duplication', async () => {
    await rejectVolumeTemplateApproval('ap-1', { reason: 'nope' });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/creator/volume-plan/templates/approvals/ap-1/reject');
    expect(init.method).toBe('POST');
  });

  it('transferVolumeTemplateApproval constructs URL without /api/api/ duplication', async () => {
    await transferVolumeTemplateApproval('ap-1', { to_assignee: 'u2' });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/creator/volume-plan/templates/approvals/ap-1/transfer');
    expect(init.method).toBe('POST');
  });

  it('fetchVolumeTemplateApprovalSnapshotDiff constructs URL without /api/api/ duplication', async () => {
    await fetchVolumeTemplateApprovalSnapshotDiff('ap-1');
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/volume-plan/templates/approvals/ap-1/snapshot-diff');
  });

  it('fetchVolumeTemplateApprovalSnapshotDrift constructs URL without /api/api/ duplication', async () => {
    await fetchVolumeTemplateApprovalSnapshotDrift('ap-1');
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('/api/creator/volume-plan/templates/approvals/ap-1/snapshot-drift');
  });

  it('deleteFactoryVolumeTemplate constructs URL without /api/api/ duplication', async () => {
    await deleteFactoryVolumeTemplate('tpl-1');
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/creator/volume-plan/templates/factory/tpl-1');
    expect(init.method).toBe('DELETE');
  });

  // --- additional sanity: existing single-prefix paths still use /api/ correctly ---

  it('deleteVolumeTemplate DELETEs with single /api/ prefix', async () => {
    await deleteVolumeTemplate('abc');
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/creator/volume-plan/templates/abc');
    expect(init.method).toBe('DELETE');
  });

  it('renameVolumeTemplate PATCHes with single /api/ prefix', async () => {
    await renameVolumeTemplate('abc', { name: 'renamed' });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/creator/volume-plan/templates/abc');
    expect(init.method).toBe('PATCH');
  });
});