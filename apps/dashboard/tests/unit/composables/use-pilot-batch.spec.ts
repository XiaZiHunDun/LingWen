import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h } from 'vue';
import { mount } from '@vue/test-utils';

const mockStartBatch = vi.fn();
const mockActive = vi.fn();
const mockGetJob = vi.fn();
const mockList = vi.fn();
const mockCancel = vi.fn();

vi.mock('@/api/studio', () => ({
  studioProductionRun: (...args: unknown[]) => mockStartBatch(...args),
  fetchStudioActiveBatchJob: () => mockActive(),
  fetchStudioBatchJob: (...args: unknown[]) => mockGetJob(...args),
  listStudioBatchJobs: (...args: unknown[]) => mockList(...args),
  cancelStudioBatchJob: (...args: unknown[]) => mockCancel(...args),
}));

import { usePilotBatch } from '@/composables/usePilotBatch';

function withComposable<T>(cb: (api: ReturnType<typeof usePilotBatch>) => Promise<T>) {
  let captured!: ReturnType<typeof usePilotBatch>;
  const Host = defineComponent({
    setup() {
      captured = usePilotBatch();
      return () => h('div');
    },
  });
  const wrapper = mount(Host);
  return cb(captured).finally(() => wrapper.unmount());
}

beforeEach(() => {
  vi.useFakeTimers();
  mockStartBatch.mockReset();
  mockActive.mockReset();
  mockGetJob.mockReset();
  mockList.mockReset();
  mockCancel.mockReset();
});

afterEach(() => {
  vi.useRealTimers();
});

describe('usePilotBatch', () => {
  it('exposes initial empty state', async () => {
    await withComposable(async (api) => {
      expect(api.activeJob.value).toBeNull();
      expect(api.history.value).toEqual([]);
    });
  });

  it('refreshActive populates activeJob', async () => {
    const fakeJob = { job_id: 'j1', status: 'running', log_path: '/tmp/x' };
    mockActive.mockResolvedValue(fakeJob);
    await withComposable(async (api) => {
      await api.refreshActive();
      expect(api.activeJob.value).toEqual(fakeJob);
    });
  });

  it('startBatch calls fetchStudioStartBatchJob and refreshes active', async () => {
    const started = { job_id: 'new-j', status: 'running', log_path: '/tmp/y' };
    mockStartBatch.mockResolvedValue(started);
    mockActive.mockResolvedValue(started);
    await withComposable(async (api) => {
      await api.startBatch({ slug: 's1', start_chapter: 1, end_chapter: 10, budget_usd: 5, mode: 'pilot' });
      expect(mockStartBatch).toHaveBeenCalledOnce();
      expect(api.activeJob.value?.job_id).toBe('new-j');
    });
  });

  it('cancelBatch calls cancelStudioBatchJob', async () => {
    mockCancel.mockResolvedValue({ job_id: 'j1', status: 'cancelled' });
    await withComposable(async (api) => {
      await api.cancelBatch('j1');
      expect(mockCancel).toHaveBeenCalledWith('j1');
    });
  });

  it('refreshHistory populates history list', async () => {
    mockList.mockResolvedValue({ jobs: [{ job_id: 'h1', status: 'completed' }] });
    await withComposable(async (api) => {
      await api.refreshHistory('s1', 20);
      expect(api.history.value).toHaveLength(1);
      expect(api.history.value[0].job_id).toBe('h1');
    });
  });
});