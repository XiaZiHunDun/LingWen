// tests/unit/use-creator-volume-plan-merge-split.spec.ts — useCreatorVolumePlanMergeSplit

import { describe, test, expect, vi, beforeEach } from 'vitest';
import { ref } from 'vue';
import { asMergePreviewRef, asSplitPreviewRef } from '../helpers/strict-test-types.js';

const mergeSplitMocks = vi.hoisted(() => ({
  mergeCreatorVolumePlan: vi.fn(),
  splitCreatorVolumePlan: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  mergeCreatorVolumePlan: (...args: unknown[]) => mergeSplitMocks.mergeCreatorVolumePlan(...args),
  splitCreatorVolumePlan: (...args: unknown[]) => mergeSplitMocks.splitCreatorVolumePlan(...args),
}));

describe('useCreatorVolumePlanMergeSplit', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mergeSplitMocks.mergeCreatorVolumePlan.mockResolvedValue({
      volumes: [{ label: '合并卷', start_chapter: 1, end_chapter: 20, core_conflict: '', locked: false }],
      merged_label: '合并卷',
      merged_range: '1-20',
    });
    mergeSplitMocks.splitCreatorVolumePlan.mockResolvedValue({
      volumes: [
        { label: '卷A', start_chapter: 1, end_chapter: 5, core_conflict: '', locked: false },
        { label: '卷B', start_chapter: 6, end_chapter: 10, core_conflict: '', locked: false },
      ],
      first_label: '卷A',
      second_label: '卷B',
      first_range: '1-5',
      second_range: '6-10',
    });
  });

  async function mountMergeSplit() {
    const { useCreatorVolumePlanMergeSplit } = await import('../../src/composables/useCreatorVolumePlanMergeSplit.js');
    const editableVolumes = ref([
      { label: '第一卷', start_chapter: 1, end_chapter: 10, core_conflict: '', locked: false },
      { label: '第二卷', start_chapter: 11, end_chapter: 20, core_conflict: '', locked: false },
    ]);
    const saveMessage = ref('');
    const hub = useCreatorVolumePlanMergeSplit({
      error: ref(null),
      saveMessage,
      editableVolumes,
      handleSaveError: vi.fn(),
    });
    return { hub, editableVolumes, saveMessage };
  }

  test('syncSplitChapterFromVolume picks midpoint chapter', async () => {
    const { hub } = await mountMergeSplit();
    hub.splitVolumeIdx.value = 0;
    hub.syncSplitChapterFromVolume();
    expect(hub.splitAtChapter.value).toBe(5);
  });

  test('applyVolumeMerge replaces volumes and sets preview', async () => {
    const { hub, editableVolumes, saveMessage } = await mountMergeSplit();
    hub.mergeStartIdx.value = 0;
    hub.mergeEndIdx.value = 1;
    await hub.applyVolumeMerge();
    expect(mergeSplitMocks.mergeCreatorVolumePlan).toHaveBeenCalled();
    expect(editableVolumes.value).toHaveLength(1);
    expect(asMergePreviewRef(hub.mergePreview).value?.merged_label).toBe('合并卷');
    expect(saveMessage.value).toContain('合并卷');
  });

  test('applyVolumeSplit clears merge preview and sets split preview', async () => {
    const { hub, editableVolumes } = await mountMergeSplit();
    asMergePreviewRef(hub.mergePreview).value = { merged_label: 'x', merged_range: '1-2' };
    hub.splitVolumeIdx.value = 0;
    hub.splitAtChapter.value = 6;
    await hub.applyVolumeSplit();
    expect(mergeSplitMocks.splitCreatorVolumePlan).toHaveBeenCalled();
    expect(editableVolumes.value).toHaveLength(2);
    expect(hub.mergePreview.value).toBeNull();
    expect(asSplitPreviewRef(hub.splitPreview).value?.first_label).toBe('卷A');
  });

  test('resetAfterLoad resets indices and previews', async () => {
    const { hub } = await mountMergeSplit();
    asMergePreviewRef(hub.mergePreview).value = { merged_label: 'x', merged_range: '1-2' };
    asSplitPreviewRef(hub.splitPreview).value = { first_label: 'a', second_label: 'b', first_range: '1', second_range: '2' };
    hub.resetAfterLoad(3);
    expect(hub.mergeStartIdx.value).toBe(0);
    expect(hub.mergeEndIdx.value).toBe(1);
    expect(hub.mergePreview.value).toBeNull();
    expect(hub.splitPreview.value).toBeNull();
  });
});
