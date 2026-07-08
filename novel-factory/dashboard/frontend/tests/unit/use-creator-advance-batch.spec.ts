// tests/unit/use-creator-advance-batch.spec.ts — useCreatorAdvanceBatch 推进 batch

import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { computed, defineComponent, ref } from 'vue';
import { flushPromises, mount } from '@vue/test-utils';

const batchMocks = vi.hoisted(() => ({
  studioProductionPreflight: vi.fn(),
  studioProductionRun: vi.fn(),
  fetchStudioActiveBatchJob: vi.fn(),
  generateCreatorVolumeSummary: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  studioProductionPreflight: (...args: unknown[]) => batchMocks.studioProductionPreflight(...args),
  studioProductionRun: (...args: unknown[]) => batchMocks.studioProductionRun(...args),
  fetchStudioActiveBatchJob: (...args: unknown[]) => batchMocks.fetchStudioActiveBatchJob(...args),
  generateCreatorVolumeSummary: (...args: unknown[]) => batchMocks.generateCreatorVolumeSummary(...args),
}));

import { useCreatorAdvanceBatch } from '../../src/composables/useCreatorAdvanceBatch.js';

type BatchApi = ReturnType<typeof useCreatorAdvanceBatch>;

function mountBatch(overrides: Record<string, unknown> = {}) {
  const uiProfile = computed(() => ({
    advance_batch_panel_on_creator: true,
    ...(overrides.uiProfile as object | undefined),
  }));

  const overview = ref({
    creation_mode: 'advance',
    advance_volume_summary: true,
    ...(overrides.overview as object | undefined),
  });

  const error = ref<string | null>(null);
  const saveMessage = ref('');
  const navigateTo = vi.fn();
  const onAfterBatchRefresh = vi.fn(async () => undefined);
  const onBatchCompleted = vi.fn(async () => undefined);
  const loadBatchHistory = vi.fn(async () => undefined);
  const setBatchSummaryPrompt = vi.fn();

  const deps = {
    uiProfile,
    overview,
    saveMessage,
    error,
    navigateTo,
    onAfterBatchRefresh,
    onBatchCompleted,
    loadBatchHistory,
    setBatchSummaryPrompt,
  };

  let api!: BatchApi;
  const Comp = defineComponent({
    setup() {
      api = useCreatorAdvanceBatch(deps);
      return () => null;
    },
  });

  const wrapper = mount(Comp);
  return {
    wrapper,
    api,
    error,
    saveMessage,
    navigateTo,
    onAfterBatchRefresh,
    onBatchCompleted,
    loadBatchHistory,
    setBatchSummaryPrompt,
  };
}

describe('useCreatorAdvanceBatch', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    batchMocks.studioProductionPreflight.mockResolvedValue({
      all_ok: true,
      batch_command: 'lingwen batch 1 10',
    });
    batchMocks.studioProductionRun.mockResolvedValue({ status: 'running', id: 'job-1' });
    batchMocks.fetchStudioActiveBatchJob.mockResolvedValue({ status: 'running', id: 'job-1' });
    batchMocks.generateCreatorVolumeSummary.mockResolvedValue({});
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  test('showAdvanceBatch true for advance mode with volume summary', () => {
    const { api } = mountBatch();
    expect(api.panelContext.showAdvanceBatch.value).toBe(true);
    expect(api.panelContext.showAdvanceBatchOnCreator.value).toBe(true);
  });

  test('runAdvancePreflight sets command and preflightOk on success', async () => {
    const { api } = mountBatch();
    await api.panelContext.runAdvancePreflight();
    expect(batchMocks.studioProductionPreflight).toHaveBeenCalledWith({
      start_chapter: 1,
      end_chapter: 10,
      budget_usd: 0.3,
    });
    expect(api.panelContext.preflightOk.value).toBe(true);
    expect(api.panelContext.batchCommand.value).toContain('lingwen batch');
  });

  test('runAdvancePreflight surfaces failure message', async () => {
    batchMocks.studioProductionPreflight.mockResolvedValue({ all_ok: false, batch_command: '' });
    const { api } = mountBatch();
    await api.panelContext.runAdvancePreflight();
    expect(api.panelContext.preflightOk.value).toBe(false);
    expect(api.panelContext.batchError.value).toContain('Preflight');
  });

  test('runAdvancePreflight catches API errors', async () => {
    batchMocks.studioProductionPreflight.mockRejectedValue(new Error('网络错误'));
    const { api } = mountBatch();
    await api.panelContext.runAdvancePreflight();
    expect(api.panelContext.batchError.value).toBe('网络错误');
  });

  test('runAdvanceBatch starts job and polling when running', async () => {
    const { api } = mountBatch();
    await api.panelContext.runAdvanceBatch();
    expect(batchMocks.studioProductionRun).toHaveBeenCalled();
    expect(api.batchJob.value?.status).toBe('running');
    expect(api.batchRunning.value).toBe(false);
  });

  test('pollBatchJob updates running state from API', async () => {
    const { api } = mountBatch();
    await api.pollBatchJob();
    expect(api.batchJob.value?.id).toBe('job-1');
    expect(api.batchRunning.value).toBe(true);
  });

  test('polling completion triggers refresh and onBatchCompleted', async () => {
    batchMocks.fetchStudioActiveBatchJob.mockResolvedValue(null);
    const { api, saveMessage, onAfterBatchRefresh, onBatchCompleted, loadBatchHistory, setBatchSummaryPrompt } = mountBatch();
    api.batchJob.value = { status: 'running', id: 'job-1' };
    api.resumeBatchPollingIfNeeded();
    await vi.advanceTimersByTimeAsync(3000);
    await flushPromises();
    expect(setBatchSummaryPrompt).toHaveBeenCalled();
    expect(saveMessage.value).toContain('Batch 已完成');
    expect(onAfterBatchRefresh).toHaveBeenCalled();
    expect(onBatchCompleted).toHaveBeenCalledWith(1, 10);
    expect(loadBatchHistory).toHaveBeenCalled();
  });

  test('goProduceConsole navigates to produce studio tab', () => {
    const { api, navigateTo } = mountBatch();
    api.panelContext.goProduceConsole();
    expect(navigateTo).toHaveBeenCalledWith('produce', { tab: 'studio', clearFocus: true });
  });

  test('resumeBatchPollingIfNeeded restarts polling for running job', async () => {
    const { api } = mountBatch();
    api.batchJob.value = { status: 'running', id: 'job-1' };
    api.resumeBatchPollingIfNeeded();
    await vi.advanceTimersByTimeAsync(3000);
    await flushPromises();
    expect(batchMocks.fetchStudioActiveBatchJob).toHaveBeenCalled();
  });

  test('stopBatchPolling clears interval on unmount', async () => {
    const { api, wrapper } = mountBatch();
    await api.panelContext.runAdvanceBatch();
    wrapper.unmount();
    batchMocks.fetchStudioActiveBatchJob.mockClear();
    await vi.advanceTimersByTimeAsync(6000);
    expect(batchMocks.fetchStudioActiveBatchJob).not.toHaveBeenCalled();
  });
});
