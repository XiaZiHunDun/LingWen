/**
 * useProductPublish 子模块独立测试
 *
 * Phase 33: 为 Phase 19.1 useProductPublish 子模块添加专门测试。
 * 重点测试：发布向导 4 步流程 + 平台加载 + 历史加载 + 设置导出模式。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref } from 'vue';

const pubMocks = vi.hoisted(() => ({
  fetchCreatorPublishHistory: vi.fn(),
  fetchCreatorPublishPlatforms: vi.fn(),
  submitCreatorPublish: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorPublishHistory: (...args: unknown[]) => pubMocks.fetchCreatorPublishHistory(...args),
  fetchCreatorPublishPlatforms: (...args: unknown[]) => pubMocks.fetchCreatorPublishPlatforms(...args),
  submitCreatorPublish: (...args: unknown[]) => pubMocks.submitCreatorPublish(...args),
}));

vi.mock('../../utils/displayProjectName.js', () => ({
  normalizeVolumePlanVolumes: (v: unknown) => v,
}));

import { useProductPublish } from '../../src/composables/useCreatorProductTools/useProductPublish';

function mountPublish(overrides: { buildExportMarkdown?: () => Promise<string>; resolveExportChapterNums?: () => Promise<number[]> } = {}) {
  const exportIntro = ref('export intro');
  const exportDescription = ref('export desc');
  const buildExportMarkdown = overrides.buildExportMarkdown || (async () => '# MD');
  const resolveExportChapterNums = overrides.resolveExportChapterNums || (async () => [1, 2, 3]);
  const setExportMode = vi.fn();
  const error = ref<string | null>(null);
  const saveMessage = ref('');
  return {
    ...useProductPublish({
      exportIntro, exportDescription, buildExportMarkdown, resolveExportChapterNums,
      setExportMode, error, saveMessage,
    }),
    saveMessage, exportIntro, exportDescription, error,
  };
}

describe('useProductPublish', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    pubMocks.fetchCreatorPublishHistory.mockResolvedValue({ entries: [] });
    pubMocks.fetchCreatorPublishPlatforms.mockResolvedValue({ platforms: [] });
  });

  it('initial state has closed modal and idle', () => {
    const p = mountPublish();
    expect(p.publishModalOpen.value).toBe(false);
    expect(p.publishStep.value).toBe(0);
    expect(p.publishStatus.value).toBe('idle');
  });

  it('initial platforms include CREATOR_PUBLISH_PLATFORMS fallback', () => {
    const p = mountPublish();
    expect(p.publishPlatforms.value.length).toBeGreaterThan(0);
    expect(p.publishPlatforms.value.some((pl: { id: string }) => pl.id === 'fanqie')).toBe(true);
  });

  it('activePublishPlatform returns matching platform', () => {
    const p = mountPublish();
    p.publishPlatform.value = 'fanqie';
    expect(p.activePublishPlatform.value.id).toBe('fanqie');
  });

  it('activePublishPlatform falls back to first', () => {
    const p = mountPublish();
    p.publishPlatform.value = 'unknown';
    expect(p.activePublishPlatform.value.id).toBeTruthy();
  });

  it('openPublishWizard sets loading and loads history + platforms', async () => {
    const p = mountPublish();
    await p.openPublishWizard();
    expect(p.publishModalOpen.value).toBe(true);
    expect(p.publishStep.value).toBe(0);
    expect(p.publishStatus.value).toBe('idle');
    expect(pubMocks.fetchCreatorPublishHistory).toHaveBeenCalled();
    expect(pubMocks.fetchCreatorPublishPlatforms).toHaveBeenCalled();
  });

  it('closePublishWizard closes modal and resets status', () => {
    const p = mountPublish();
    p.publishModalOpen.value = true;
    p.publishStatus.value = 'submitting';
    p.closePublishWizard();
    expect(p.publishModalOpen.value).toBe(false);
    expect(p.publishStatus.value).toBe('idle');
  });

  it('nextPublishStep advances from 0 to 1 and calls prefill', async () => {
    const p = mountPublish();
    p.publishModalOpen.value = true;
    p.nextPublishStep();
    // step 0 → 1 触发 prefillPublishFromSubmission
    expect(p.publishStep.value).toBe(1);
  });

  it('nextPublishStep caps at 3', () => {
    const p = mountPublish();
    p.publishStep.value = 3;
    p.nextPublishStep();
    expect(p.publishStep.value).toBe(3);
  });

  it('prevPublishStep decrements step but not below 0', () => {
    const p = mountPublish();
    p.publishStep.value = 2;
    p.prevPublishStep();
    expect(p.publishStep.value).toBe(1);
    p.prevPublishStep();
    p.prevPublishStep();
    expect(p.publishStep.value).toBe(0);
  });

  it('openPublishHistoryModal opens and loads history', async () => {
    const p = mountPublish();
    await p.openPublishHistoryModal();
    expect(p.publishHistoryModalOpen.value).toBe(true);
    expect(pubMocks.fetchCreatorPublishHistory).toHaveBeenCalledWith(30);
  });

  it('closePublishHistoryModal closes history modal', () => {
    const p = mountPublish();
    p.publishHistoryModalOpen.value = true;
    p.closePublishHistoryModal();
    expect(p.publishHistoryModalOpen.value).toBe(false);
  });

  it('submitPublish posts and updates status on success', async () => {
    pubMocks.submitCreatorPublish.mockResolvedValueOnce({ message: '已发布', status: 'success' });
    const p = mountPublish();
    p.publishPlatform.value = 'fanqie';
    await p.submitPublish();
    expect(pubMocks.submitCreatorPublish).toHaveBeenCalled();
    expect(p.publishStatus.value).toBe('success');
    expect(p.saveMessage.value).toContain('已发布');
  });

  it('submitPublish sets idle on failure', async () => {
    pubMocks.submitCreatorPublish.mockRejectedValueOnce(new Error('network'));
    const p = mountPublish();
    p.publishPlatform.value = 'fanqie';
    await p.submitPublish();
    expect(p.publishStatus.value).toBe('idle');
    expect(p.error.value).toBe('network');
  });

  it('prefillPublishFromSubmission sets intro from export', async () => {
    const p = mountPublish();
    p.exportIntro.value = 'shared intro';
    await p.openPublishWizard();
    p.publishStep.value = 0;
    p.nextPublishStep();
    // prefillPublishFromSubmission 是 async，需要等待微任务
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(p.publishIntro.value).toBe('shared intro');
  });
});