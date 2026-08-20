/**
 * api/volumePlan 独立测试（Phase 62.3）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  fetchCreatorVolumePlan,
  saveCreatorVolumePlan,
  previewCreatorVolumePlanDiff,
  mergeCreatorVolumePlan,
  splitCreatorVolumePlan,
  fetchCreatorBatchHistory,
  exportCreatorBatchHistory,
} from '../../src/api/volumePlan.js';

const mocks = vi.hoisted(() => ({
  request: vi.fn(),
}));

vi.mock('../../src/api/core.js', () => ({
  request: (...args: unknown[]) => mocks.request(...args),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe('api/volumePlan', () => {
  it('fetchCreatorVolumePlan GETs /creator/volume-plan', async () => {
    mocks.request.mockResolvedValueOnce({ volumes: [] });
    await fetchCreatorVolumePlan();
    expect(mocks.request).toHaveBeenCalledWith('/creator/volume-plan');
  });

  it('saveCreatorVolumePlan PUTs volumes + expected_revision when provided', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await saveCreatorVolumePlan([{ id: 1 }], 5);
    expect(mocks.request).toHaveBeenCalledWith('/creator/volume-plan', {
      method: 'PUT',
      body: { volumes: [{ id: 1 }], expected_revision: 5 },
    });
  });

  it('saveCreatorVolumePlan omits expected_revision when falsy', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await saveCreatorVolumePlan([{ id: 1 }], undefined);
    expect(mocks.request).toHaveBeenCalledWith('/creator/volume-plan', {
      method: 'PUT',
      body: { volumes: [{ id: 1 }] },
    });
  });

  it('previewCreatorVolumePlanDiff POSTs volumes', async () => {
    mocks.request.mockResolvedValueOnce({ diff: {} });
    await previewCreatorVolumePlanDiff([{ id: 1 }]);
    expect(mocks.request).toHaveBeenCalledWith('/creator/volume-plan/diff', {
      method: 'POST',
      body: { volumes: [{ id: 1 }] },
    });
  });

  it('mergeCreatorVolumePlan POSTs body', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await mergeCreatorVolumePlan({ foo: 1 });
    expect(mocks.request).toHaveBeenCalledWith('/creator/volume-plan/merge', {
      method: 'POST',
      body: { foo: 1 },
    });
  });

  it('splitCreatorVolumePlan POSTs body', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await splitCreatorVolumePlan({ bar: 2 });
    expect(mocks.request).toHaveBeenCalledWith('/creator/volume-plan/split', {
      method: 'POST',
      body: { bar: 2 },
    });
  });

  it('fetchCreatorBatchHistory GETs /creator/batch-history', async () => {
    mocks.request.mockResolvedValueOnce({ history: [] });
    await fetchCreatorBatchHistory();
    expect(mocks.request).toHaveBeenCalledWith('/creator/batch-history');
  });

  it('exportCreatorBatchHistory GETs /creator/batch-history/export (no POST)', async () => {
    mocks.request.mockResolvedValueOnce({ ok: true });
    await exportCreatorBatchHistory();
    expect(mocks.request).toHaveBeenCalledWith('/creator/batch-history/export');
  });
});
