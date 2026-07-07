// tests/unit/use-creator-volume-plan-diff.spec.ts — useCreatorVolumePlanDiff

import { describe, test, expect, vi, beforeEach } from 'vitest';
import { computed, ref } from 'vue';
import { asVolumePlanDiffPreviewRef } from '../helpers/strict-test-types.js';

const diffMocks = vi.hoisted(() => ({
  previewCreatorVolumePlanDiff: vi.fn(),
  downloadJsonExport: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  previewCreatorVolumePlanDiff: (...args: unknown[]) => diffMocks.previewCreatorVolumePlanDiff(...args),
  fetchCreatorDiffCollabNotes: vi.fn(async () => ({ notes: {} })),
  saveCreatorDiffCollabNotes: vi.fn(async (payload: unknown) => payload),
}));

vi.mock('../../src/composables/volumePlanDiffExportUtils.js', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../src/composables/volumePlanDiffExportUtils.js')>();
  return {
    ...actual,
    downloadJsonExport: (...args: unknown[]) => diffMocks.downloadJsonExport(...args),
  };
});

describe('useCreatorVolumePlanDiff', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    diffMocks.previewCreatorVolumePlanDiff.mockResolvedValue({
      has_changes: true,
      changes: [
        { type: 'modified', label: '第一卷', message: '范围变更' },
        { type: 'added', label: '第二卷', message: '新增卷' },
      ],
    });
  });

  async function mountDiff(overrides: Record<string, unknown> = {}) {
    const { useCreatorVolumePlanDiff } = await import('../../src/composables/useCreatorVolumePlanDiff.js');
    const editableVolumes = ref([
      { label: '第一卷', start_chapter: 1, end_chapter: 10, core_conflict: '', locked: false },
    ]);
    const uiProfile = computed(() => ({
      volume_plan_diff_preview: true,
      volume_plan_diff_auto_collapse: false,
      volume_plan_diff_type_filter: true,
      volume_plan_diff_volume_filter: true,
      volume_plan_diff_export: true,
      volume_plan_diff_export_outline: false,
      volume_plan_diff_export_highlight: false,
      ...overrides,
    }));
    return useCreatorVolumePlanDiff({
      uiProfile,
      saveMessage: ref(''),
      wizardEmailTo: ref(''),
      globalOutlineEditorRef: ref(null),
      editableVolumes,
      saving: ref(false),
    });
  }

  test('refreshVolumePlanDiffPreview loads preview from API', async () => {
    const hub = await mountDiff();
    await hub.refreshVolumePlanDiffPreview();
    expect(diffMocks.previewCreatorVolumePlanDiff).toHaveBeenCalledTimes(1);
    expect(asVolumePlanDiffPreviewRef(hub.volumePlanDiffPreview).value?.has_changes).toBe(true);
    expect(hub.volumePlanDiffChangeCount.value).toBe(2);
  });

  test('filteredVolumePlanDiffChanges respects type filter', async () => {
    const hub = await mountDiff();
    await hub.refreshVolumePlanDiffPreview();
    hub.volumePlanDiffTypeFilter.value = 'added';
    expect(hub.filteredVolumePlanDiffChanges.value).toHaveLength(1);
    expect(hub.filteredVolumePlanDiffChanges.value[0].label).toBe('第二卷');
  });

  test('exportVolumePlanDiff downloads JSON when changes exist', async () => {
    const hub = await mountDiff();
    await hub.refreshVolumePlanDiffPreview();
    hub.exportVolumePlanDiff();
    expect(diffMocks.downloadJsonExport).toHaveBeenCalledWith(
      'creator-volume-plan-diff.json',
      expect.objectContaining({ change_count: 2 }),
    );
  });

  test('refreshVolumePlanDiffPreview clears preview when disabled', async () => {
    const hub = await mountDiff({ volume_plan_diff_preview: false });
    await hub.refreshVolumePlanDiffPreview();
    expect(diffMocks.previewCreatorVolumePlanDiff).not.toHaveBeenCalled();
    expect(hub.volumePlanDiffPreview.value).toBeNull();
  });
});
