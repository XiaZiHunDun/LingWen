// tests/unit/use-creator-volume-plan-templates.spec.ts — useCreatorVolumePlanTemplates

import { describe, test, expect, vi, beforeEach } from 'vitest';
import { computed, ref } from 'vue';
import { asEditableVolumes } from '../helpers/strict-test-types.js';

const templateMocks = vi.hoisted(() => ({
  listVolumeTemplates: vi.fn(),
  applyVolumeTemplate: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  listVolumeTemplates: (...args: unknown[]) => templateMocks.listVolumeTemplates(...args),
  applyVolumeTemplate: (...args: unknown[]) => templateMocks.applyVolumeTemplate(...args),
  saveCreatorVolumeTemplate: vi.fn(),
  deleteCreatorVolumeTemplate: vi.fn(),
  renameCreatorVolumeTemplate: vi.fn(),
  exportVolumeTemplates: vi.fn(),
  importVolumeTemplates: vi.fn(),
  fetchVolumeTemplateSyncSources: vi.fn(async () => ({ sources: [] })),
  syncVolumeTemplates: vi.fn(),
  publishFactoryVolumeTemplate: vi.fn(),
  pullFactoryVolumeTemplates: vi.fn(),
  deleteFactoryVolumeTemplate: vi.fn(),
  setCreatorVolumeTemplateVersion: vi.fn(),
  fetchCreatorVolumeTemplateChangelog: vi.fn(async () => ({ entries: [] })),
  rollbackCreatorVolumeTemplate: vi.fn(),
  fetchVolumeTemplateApprovals: vi.fn(async () => ({ approvals: [] })),
  submitCreatorTemplateVersionApproval: vi.fn(),
  approveVolumeTemplateApproval: vi.fn(),
  rejectVolumeTemplateApproval: vi.fn(),
  fetchVolumeTemplateApprovalChain: vi.fn(async () => ({ required_steps: 2, step_assignees: [] })),
  saveVolumeTemplateApprovalChain: vi.fn(),
  fetchVolumeTemplateApprovalHistory: vi.fn(async () => ({ approvals: [] })),
  exportCreatorTemplateApprovalAudit: vi.fn(),
  fetchVolumeTemplateApprovalSla: vi.fn(async () => ({ timeout_hours: 72 })),
  saveVolumeTemplateApprovalSla: vi.fn(),
  fetchVolumeTemplateApprovalsOverdue: vi.fn(async () => ({ approvals: [] })),
  transferVolumeTemplateApproval: vi.fn(),
  fetchVolumeTemplateApprovalSnapshotDiff: vi.fn(),
  fetchVolumeTemplateApprovalSnapshotDrift: vi.fn(async () => ({ drifted: false })),
  batchApproveVolumeTemplateApprovals: vi.fn(),
  batchRejectVolumeTemplateApprovals: vi.fn(),
}));

// v16.2.7 T6.B: also mock the typed wrapper module so useCreatorVolumePlanTemplates
// (which now imports from @/api/volume) resolves the same mocks. Per v16.2.5 §5.1 lesson 3.
vi.mock('../../src/api/volume', () => ({
  listVolumeTemplates: (...args: unknown[]) => templateMocks.listVolumeTemplates(...args),
  applyVolumeTemplate: (...args: unknown[]) => templateMocks.applyVolumeTemplate(...args),
  fetchVolumeTemplateSyncSources: vi.fn(async () => ({ sources: [] })),
  exportVolumeTemplates: vi.fn(),
  importVolumeTemplates: vi.fn(),
  syncVolumeTemplates: vi.fn(),
  publishFactoryVolumeTemplate: vi.fn(),
  pullFactoryVolumeTemplates: vi.fn(),
  deleteFactoryVolumeTemplate: vi.fn(),
  fetchVolumeTemplateApprovals: vi.fn(async () => ({ approvals: [] })),
  approveVolumeTemplateApproval: vi.fn(),
  rejectVolumeTemplateApproval: vi.fn(),
  transferVolumeTemplateApproval: vi.fn(),
  fetchVolumeTemplateApprovalChain: vi.fn(async () => ({ required_steps: 2, step_assignees: [] })),
  saveVolumeTemplateApprovalChain: vi.fn(),
  fetchVolumeTemplateApprovalHistory: vi.fn(async () => ({ approvals: [] })),
  fetchVolumeTemplateApprovalSla: vi.fn(async () => ({ timeout_hours: 72 })),
  saveVolumeTemplateApprovalSla: vi.fn(),
  fetchVolumeTemplateApprovalsOverdue: vi.fn(async () => ({ approvals: [] })),
  fetchVolumeTemplateApprovalSnapshotDiff: vi.fn(),
  fetchVolumeTemplateApprovalSnapshotDrift: vi.fn(async () => ({ drifted: false })),
  batchApproveVolumeTemplateApprovals: vi.fn(),
  batchRejectVolumeTemplateApprovals: vi.fn(),
}));

describe('useCreatorVolumePlanTemplates', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    templateMocks.listVolumeTemplates.mockResolvedValue({
      templates: [
        { id: 'three_act', name: '三幕式', scope: 'builtin', version_label: 'v1.0.0', version_semver_valid: true },
        { id: 'custom_a', name: '自定义', scope: 'project' },
      ],
    });
    templateMocks.applyVolumeTemplate.mockResolvedValue({
      template_name: '三幕式',
      volumes: [{ label: '第一卷', start_chapter: 1, end_chapter: 20, core_conflict: 'x', locked: false }],
    });
  });

  async function mountTemplates(onAfterApplyTemplate = vi.fn()) {
    const { useCreatorVolumePlanTemplates } = await import('../../src/composables/useCreatorVolumePlanTemplates.js');
    const editableVolumes = ref([]);
    const hub = useCreatorVolumePlanTemplates({
      uiProfile: computed(() => ({})),
      overview: ref({ max_chapter: 100 }),
      error: ref(null),
      saveMessage: ref(''),
      editableVolumes,
      handleSaveError: vi.fn(),
      onAfterApplyTemplate,
    });
    return { hub, editableVolumes, onAfterApplyTemplate };
  }

  test('formatTemplateOption prefixes invalid semver with !', async () => {
    const { hub } = await mountTemplates();
    expect(hub.formatTemplateOption({ name: '模板', version_label: 'v1.0.0', version_semver_valid: true })).toBe('[v1.0.0] 模板');
    expect(hub.formatTemplateOption({ name: '模板', version_label: 'bad', version_semver_valid: false })).toBe('![bad] 模板');
    expect(hub.formatTemplateOption({ name: '无版本' })).toBe('无版本');
  });

  test('isSemverVersionLabel validates semver patterns', async () => {
    const { hub } = await mountTemplates();
    expect(hub.isSemverVersionLabel('v1.2.0')).toBe(true);
    expect(hub.isSemverVersionLabel('1.2')).toBe(true);
    expect(hub.isSemverVersionLabel('not-a-version')).toBe(false);
  });

  test('loadVolumeTemplates populates list and keeps valid selection', async () => {
    const { hub } = await mountTemplates();
    await hub.loadVolumeTemplates();
    expect(hub.volumeTemplates.value).toHaveLength(2);
    expect(hub.selectedTemplateId.value).toBe('three_act');
  });

  test('applyVolumeTemplate updates volumes and runs onAfterApplyTemplate', async () => {
    const onAfterApplyTemplate = vi.fn();
    const { hub, editableVolumes } = await mountTemplates(onAfterApplyTemplate);
    await hub.loadVolumeTemplates();
    await hub.applyVolumeTemplate();
    expect(templateMocks.applyVolumeTemplate).toHaveBeenCalledWith({
      template_id: 'three_act',
      max_chapter: 100,
    });
    expect(editableVolumes.value).toHaveLength(1);
    expect(asEditableVolumes(editableVolumes).value[0].end_chapter).toBe(20);
    expect(onAfterApplyTemplate).toHaveBeenCalledTimes(1);
  });
});
