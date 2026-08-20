/**
 * useCreatorPageRefresh 独立测试
 *
 * Phase 47: 为 useCreatorPageRefresh 工厂函数添加专门测试。
 * 重点测试：refresh 编排 + loaders 并行调用 + 错误处理。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref } from 'vue';
import { createCreatorPageRefresh } from '../../src/composables/useCreatorPageRefresh';

function mountRefresh() {
  const overview = ref<Record<string, unknown> | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const conflictMessage = ref('');
  const fetchOverview = vi.fn(async () => ({ chapters: 5 }));
  const loaders = {
    loadVolumePlan: vi.fn(async () => {}),
    loadSettingsDocs: vi.fn(async () => {}),
    loadSettingsHistory: vi.fn(async () => {}),
    loadVolumeTemplates: vi.fn(async () => {}),
    loadTemplateSyncSources: vi.fn(async () => {}),
    loadOnboardingWizard: vi.fn(async () => {}),
    pollBatchJob: vi.fn(async () => {}),
  };
  const afterOverview = vi.fn(async () => {});
  const refresh = createCreatorPageRefresh({
    overview, loading, error, conflictMessage, fetchOverview, loaders, afterOverview,
  });
  return {
    refresh, overview, loading, error, conflictMessage, fetchOverview, loaders, afterOverview,
  };
}

describe('createCreatorPageRefresh', () => {
  beforeEach(() => vi.clearAllMocks());

  it('initial state has loading false', () => {
    const r = mountRefresh();
    expect(r.loading.value).toBe(false);
    expect(r.error.value).toBeNull();
    expect(r.conflictMessage.value).toBe('');
  });

  it('refresh sets loading true then false', async () => {
    const r = mountRefresh();
    const promise = r.refresh();
    // Sync - loading should be true synchronously after refresh call
    expect(r.loading.value).toBe(true);
    await promise;
    expect(r.loading.value).toBe(false);
  });

  it('refresh calls fetchOverview and all loaders in parallel', async () => {
    const r = mountRefresh();
    await r.refresh();
    expect(r.fetchOverview).toHaveBeenCalledTimes(1);
    expect(r.loaders.loadVolumePlan).toHaveBeenCalledTimes(1);
    expect(r.loaders.loadSettingsDocs).toHaveBeenCalledTimes(1);
    expect(r.loaders.loadSettingsHistory).toHaveBeenCalledTimes(1);
    expect(r.loaders.loadVolumeTemplates).toHaveBeenCalledTimes(1);
    expect(r.loaders.loadTemplateSyncSources).toHaveBeenCalledTimes(1);
    expect(r.loaders.loadOnboardingWizard).toHaveBeenCalledTimes(1);
    expect(r.loaders.pollBatchJob).toHaveBeenCalledTimes(1);
  });

  it('refresh sets overview from fetchOverview result', async () => {
    const r = mountRefresh();
    r.fetchOverview.mockResolvedValueOnce({ chapters: 10 });
    await r.refresh();
    expect(r.overview.value).toEqual({ chapters: 10 });
  });

  it('refresh calls afterOverview with overview', async () => {
    const r = mountRefresh();
    await r.refresh();
    expect(r.afterOverview).toHaveBeenCalledWith({ chapters: 5 });
  });

  it('refresh clears conflictMessage before loading', async () => {
    const r = mountRefresh();
    r.conflictMessage.value = 'old conflict';
    await r.refresh();
    expect(r.conflictMessage.value).toBe('');
  });

  it('refresh handles fetchOverview failure', async () => {
    const r = mountRefresh();
    r.fetchOverview.mockRejectedValueOnce(new Error('network fail'));
    await r.refresh();
    expect(r.error.value).toBe('network fail');
    expect(r.loading.value).toBe(false);
  });

  it('refresh sets loading to false even on failure', async () => {
    const r = mountRefresh();
    r.loaders.loadVolumePlan.mockRejectedValueOnce(new Error('fail'));
    await r.refresh();
    expect(r.loading.value).toBe(false);
  });
});
