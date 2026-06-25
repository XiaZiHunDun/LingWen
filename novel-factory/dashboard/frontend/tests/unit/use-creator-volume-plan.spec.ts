// tests/unit/use-creator-volume-plan.spec.ts — useCreatorVolumePlan 编排集成

import { describe, test, expect, vi, beforeEach } from 'vitest';
import { computed, ref } from 'vue';

const planMocks = vi.hoisted(() => ({
  fetchCreatorVolumePlan: vi.fn(),
  saveCreatorVolumePlan: vi.fn(),
  previewCreatorVolumePlanDiff: vi.fn(),
  applyCreatorVolumeTemplate: vi.fn(),
  mergeCreatorVolumePlan: vi.fn(),
}));

vi.mock('../../src/composables/volumePlanDiffExportUtils.js', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../src/composables/volumePlanDiffExportUtils.js')>();
  return { ...actual, downloadJsonExport: vi.fn() };
});

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorVolumePlan: (...args: unknown[]) => planMocks.fetchCreatorVolumePlan(...args),
  saveCreatorVolumePlan: (...args: unknown[]) => planMocks.saveCreatorVolumePlan(...args),
  previewCreatorVolumePlanDiff: (...args: unknown[]) => planMocks.previewCreatorVolumePlanDiff(...args),
  applyCreatorVolumeTemplate: (...args: unknown[]) => planMocks.applyCreatorVolumeTemplate(...args),
  mergeCreatorVolumePlan: (...args: unknown[]) => planMocks.mergeCreatorVolumePlan(...args),
  splitCreatorVolumePlan: vi.fn(),
  fetchCreatorDiffCollabNotes: vi.fn(async () => ({ notes: {} })),
  saveCreatorDiffCollabNotes: vi.fn(async (payload: unknown) => payload),
  fetchCreatorVolumeTemplates: vi.fn(async () => ({ templates: [] })),
  fetchCreatorVolumeTemplateSyncSources: vi.fn(async () => ({ sources: [] })),
  fetchCreatorTemplateApprovals: vi.fn(async () => ({ approvals: [] })),
  fetchCreatorTemplateApprovalHistory: vi.fn(async () => ({ approvals: [] })),
  fetchCreatorTemplateApprovalChainConfig: vi.fn(async () => ({ required_steps: 2, step_assignees: [] })),
  fetchCreatorTemplateApprovalSlaConfig: vi.fn(async () => ({ timeout_hours: 72 })),
  fetchCreatorTemplateApprovalOverdue: vi.fn(async () => ({ approvals: [] })),
}));

describe('useCreatorVolumePlan', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    planMocks.fetchCreatorVolumePlan.mockResolvedValue({
      revision: 'rev-1',
      volumes: [
        { label: '第一卷', start_chapter: 1, end_chapter: 10, core_conflict: 'a', locked: true },
        { label: '第二卷', start_chapter: 11, end_chapter: 20, core_conflict: 'b', locked: false },
      ],
    });
    planMocks.saveCreatorVolumePlan.mockResolvedValue({});
    planMocks.previewCreatorVolumePlanDiff.mockResolvedValue({
      has_changes: true,
      changes: [{ type: 'changed', label: '第一卷', message: '范围变更' }],
    });
    planMocks.applyCreatorVolumeTemplate.mockResolvedValue({
      template_name: '三幕式',
      volumes: [{ label: '套用卷', start_chapter: 1, end_chapter: 30, core_conflict: '', locked: false }],
    });
    planMocks.mergeCreatorVolumePlan.mockResolvedValue({
      volumes: [{ label: '合并卷', start_chapter: 1, end_chapter: 20, core_conflict: '', locked: false }],
      merged_label: '合并卷',
      merged_range: '1-20',
    });
  });

  async function mountVolumePlan(uiOverrides: Record<string, unknown> = {}) {
    const { useCreatorVolumePlan } = await import('../../src/composables/useCreatorVolumePlan.js');
    const saving = ref(false);
    const error = ref<string | null>(null);
    const saveMessage = ref('');
    const conflictMessage = ref('');
    const batchStart = ref(1);
    const batchEnd = ref(10);
    const onAfterVolumePlanSave = vi.fn(async () => undefined);
    const hub = useCreatorVolumePlan({
      uiProfile: computed(() => ({
        volume_plan_diff_preview: true,
        volume_plan_diff_save_confirm: true,
        volume_plan_diff_refresh_on_save: true,
        max_chapter: 100,
        ...uiOverrides,
      })),
      overview: ref({ max_chapter: 100 }),
      saving,
      error,
      saveMessage,
      conflictMessage,
      globalOutlineEditorRef: ref(null),
      globalOutlineText: ref(''),
      batchStart,
      batchEnd,
      wizardEmailTo: ref(''),
      handleSaveError: (err: unknown) => {
        error.value = err instanceof Error ? err.message : String(err);
      },
      onAfterVolumePlanSave,
    });
    return {
      hub,
      saving,
      error,
      saveMessage,
      batchStart,
      batchEnd,
      onAfterVolumePlanSave,
      panel: hub.panelContext,
    };
  }

  test('loadVolumePlan hydrates volumes and syncs batch range from locked volume', async () => {
    const { hub, batchStart, batchEnd } = await mountVolumePlan();
    await hub.loadVolumePlan();
    expect(hub.editableVolumes.value).toHaveLength(2);
    expect(batchStart.value).toBe(1);
    expect(batchEnd.value).toBe(10);
    expect(hub.panelContext.mergeStartIdx.value).toBe(0);
    expect(hub.panelContext.mergeEndIdx.value).toBe(1);
  });

  test('addVolume appends next chapter block', async () => {
    const { hub } = await mountVolumePlan();
    await hub.loadVolumePlan();
    hub.panelContext.addVolume();
    const last = hub.editableVolumes.value.at(-1);
    expect(last?.label).toBe('卷3');
    expect(last?.start_chapter).toBe(21);
    expect(last?.end_chapter).toBe(30);
  });

  test('moveVolume reorders editable volumes', async () => {
    const { hub } = await mountVolumePlan();
    await hub.loadVolumePlan();
    hub.panelContext.moveVolume(0, 1);
    expect(hub.editableVolumes.value[0].label).toBe('第二卷');
    expect(hub.editableVolumes.value[1].label).toBe('第一卷');
  });

  test('requestSaveVolumePlan opens confirm when diff has changes', async () => {
    const { hub, panel } = await mountVolumePlan();
    await hub.loadVolumePlan();
    await hub.refreshVolumePlanDiffPreview();
    panel.requestSaveVolumePlan();
    expect(panel.volumePlanSaveConfirmOpen.value).toBe(true);
    expect(planMocks.saveCreatorVolumePlan).not.toHaveBeenCalled();
  });

  test('saveVolumePlan persists volumes and refreshes diff', async () => {
    const { hub, panel, saveMessage, onAfterVolumePlanSave } = await mountVolumePlan();
    await hub.loadVolumePlan();
    await hub.refreshVolumePlanDiffPreview();
    planMocks.previewCreatorVolumePlanDiff.mockResolvedValueOnce({ has_changes: false, changes: [] });
    await panel.confirmSaveVolumePlan();
    expect(planMocks.saveCreatorVolumePlan).toHaveBeenCalledWith(
      hub.editableVolumes.value,
      'rev-1',
    );
    expect(planMocks.previewCreatorVolumePlanDiff).toHaveBeenCalledTimes(2);
    expect(saveMessage.value).toContain('卷纲已保存');
    expect(onAfterVolumePlanSave).toHaveBeenCalledTimes(1);
  });

  test('applyVolumeTemplate clears merge preview via orchestration callback', async () => {
    const { hub, panel } = await mountVolumePlan();
    await hub.loadVolumePlan();
    panel.mergePreview.value = { merged_label: 'x', merged_range: '1-2' };
    panel.splitPreview.value = { first_label: 'a', second_label: 'b', first_range: '1', second_range: '2' };
    await panel.applyVolumeTemplate();
    expect(planMocks.applyCreatorVolumeTemplate).toHaveBeenCalled();
    expect(hub.editableVolumes.value[0].label).toBe('套用卷');
    expect(panel.mergePreview.value).toBeNull();
    expect(panel.splitPreview.value).toBeNull();
  });

  test('panelContext wires merge/split actions to mergeSplit hub', async () => {
    const { hub, panel } = await mountVolumePlan();
    await hub.loadVolumePlan();
    panel.mergeStartIdx.value = 0;
    panel.mergeEndIdx.value = 1;
    await panel.applyVolumeMerge();
    expect(planMocks.mergeCreatorVolumePlan).toHaveBeenCalled();
    expect(hub.editableVolumes.value).toHaveLength(1);
    expect(hub.editableVolumes.value[0].label).toBe('合并卷');
  });
});
