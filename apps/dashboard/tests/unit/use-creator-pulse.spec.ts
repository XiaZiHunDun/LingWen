/**
 * useCreatorPulse 独立测试
 *
 * Phase 47: 为 useCreatorPulse hub 添加专门测试。
 * 重点测试：showPulseCompanionEmpty computed + jumpToVolume + openVolumeSummaryByName +
 *          setBatchSummaryPrompt + dismissBatchSummaryPrompt。
 */
import { describe, it, expect, vi } from 'vitest';
import { ref, computed, nextTick } from 'vue';
import { useCreatorPulse } from '../../src/composables/useCreatorPulse';

function mountPulse() {
  const uiProfile = computed(() => ({}));
  const overview = ref<Record<string, unknown> | null>(null);
  const error = ref<string | null>(null);
  const saveMessage = ref('');
  const workspaceTabsEnabled = ref(true);
  const isWorkspaceColumnVisible = vi.fn(() => true);
  const isDeskDrawerColumn = vi.fn(() => false);
  const closeDeskDrawer = vi.fn();
  const setWorkspaceTab = vi.fn();
  const editableVolumes = ref<Array<Record<string, unknown>>>([]);
  const visibleDeviations = ref<Array<Record<string, unknown>>>([]);
  const deviationHighlightEnabled = ref(false);
  const highlightedDeviationChapter = ref<number | null>(null);
  const handleDeviationClick = vi.fn();
  const jumpToChapter = vi.fn(async () => {});
  const onAfterVolumeSummarySave = vi.fn(async () => {});
  const batchJob = ref<Record<string, unknown> | null>(null);

  const ctx = useCreatorPulse({
    uiProfile, overview, error, saveMessage, workspaceTabsEnabled,
    isWorkspaceColumnVisible, isDeskDrawerColumn, closeDeskDrawer, setWorkspaceTab,
    editableVolumes, visibleDeviations, deviationHighlightEnabled,
    highlightedDeviationChapter, handleDeviationClick, jumpToChapter,
    onAfterVolumeSummarySave, batchJob,
  } as unknown as Parameters<typeof useCreatorPulse>[0]);
  return {
    ...ctx,
    overview, editableVolumes, visibleDeviations, workspaceTabsEnabled,
  };
}

describe('useCreatorPulse', () => {
  it('initial state has closed batch summary', () => {
    const p = mountPulse();
    expect(p.batchSummaryPrompt.value).toBeNull();
  });

  it('showPulseCompanionEmpty false in non-companion mode', () => {
    const p = mountPulse();
    p.overview.value = { creation_mode: 'studio' };
    expect(p.panelContext.showPulseCompanionEmpty.value).toBe(false);
  });

  it('showPulseCompanionEmpty false when workspace tabs disabled', () => {
    const p = mountPulse();
    p.overview.value = { creation_mode: 'companion' };
    p.workspaceTabsEnabled.value = false;
    expect(p.panelContext.showPulseCompanionEmpty.value).toBe(false);
  });

  it('showPulseCompanionEmpty false when editable volumes present', () => {
    const p = mountPulse();
    p.overview.value = { creation_mode: 'companion' };
    p.editableVolumes.value = [{ label: '第一卷' }];
    expect(p.panelContext.showPulseCompanionEmpty.value).toBe(false);
  });

  it('showPulseCompanionEmpty false when visible deviations present', () => {
    const p = mountPulse();
    p.overview.value = { creation_mode: 'companion' };
    p.visibleDeviations.value = [{ chapter: 1 }];
    expect(p.panelContext.showPulseCompanionEmpty.value).toBe(false);
  });

  it('showPulseCompanionEmpty false when volume_pulse has volumes', () => {
    const p = mountPulse();
    p.overview.value = {
      creation_mode: 'companion',
      volume_pulse: { volume_count: 3 },
    };
    expect(p.panelContext.showPulseCompanionEmpty.value).toBe(false);
  });

  it('showPulseCompanionEmpty true in companion mode with empty state', () => {
    const p = mountPulse();
    p.overview.value = { creation_mode: 'companion' };
    expect(p.panelContext.showPulseCompanionEmpty.value).toBe(true);
  });

  it('jumpToVolume no-op on null', async () => {
    const p = mountPulse();
    await p.panelContext.jumpToVolume(null);
    expect(p.panelContext.highlightedVolumeLabel.value).toBeNull();
  });

  it('jumpToVolume sets label', async () => {
    const p = mountPulse();
    await p.panelContext.jumpToVolume({ label: '第一卷', start_chapter: 1 });
    expect(p.panelContext.highlightedVolumeLabel.value).toBe('第一卷');
  });

  it('setBatchSummaryPrompt sets state', () => {
    const p = mountPulse();
    p.setBatchSummaryPrompt({ title: '批量总结' });
    expect(p.batchSummaryPrompt.value).toEqual({ title: '批量总结' });
  });

  it('dismissBatchSummaryPrompt clears state', () => {
    const p = mountPulse();
    p.setBatchSummaryPrompt({ title: 'test' });
    p.panelContext.dismissBatchSummaryPrompt();
    expect(p.panelContext.batchSummaryPrompt.value).toBeNull();
  });
});
