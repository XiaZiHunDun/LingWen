// tests/unit/use-creator-volume-plan-templates.spec.ts — useCreatorVolumePlanTemplates

import { describe, test, expect, vi, beforeEach } from 'vitest';
import { computed, ref } from 'vue';
import { asEditableVolumes } from '../helpers/strict-test-types.js';

const templateMocks = vi.hoisted(() => ({
  fetchCreatorVolumeTemplates: vi.fn(),
  applyCreatorVolumeTemplate: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorVolumeTemplates: (...args: unknown[]) => templateMocks.fetchCreatorVolumeTemplates(...args),
  applyCreatorVolumeTemplate: (...args: unknown[]) => templateMocks.applyCreatorVolumeTemplate(...args),
  saveCreatorVolumeTemplate: vi.fn(),
  deleteCreatorVolumeTemplate: vi.fn(),
  renameCreatorVolumeTemplate: vi.fn(),
  exportCreatorVolumeTemplates: vi.fn(),
  importCreatorVolumeTemplates: vi.fn(),
  fetchCreatorVolumeTemplateSyncSources: vi.fn(async () => ({ sources: [] })),
  syncCreatorVolumeTemplates: vi.fn(),
  publishCreatorVolumeTemplateToFactory: vi.fn(),
  pullCreatorFactoryVolumeTemplates: vi.fn(),
  deleteCreatorFactoryVolumeTemplate: vi.fn(),
  setCreatorVolumeTemplateVersion: vi.fn(),
  fetchCreatorVolumeTemplateChangelog: vi.fn(async () => ({ entries: [] })),
  rollbackCreatorVolumeTemplate: vi.fn(),
  fetchCreatorTemplateApprovals: vi.fn(async () => ({ approvals: [] })),
  submitCreatorTemplateVersionApproval: vi.fn(),
  approveCreatorTemplateApproval: vi.fn(),
  rejectCreatorTemplateApproval: vi.fn(),
  fetchCreatorTemplateApprovalChainConfig: vi.fn(async () => ({ required_steps: 2, step_assignees: [] })),
  saveCreatorTemplateApprovalChainConfig: vi.fn(),
  fetchCreatorTemplateApprovalHistory: vi.fn(async () => ({ approvals: [] })),
  exportCreatorTemplateApprovalAudit: vi.fn(),
  fetchCreatorTemplateApprovalSlaConfig: vi.fn(async () => ({ timeout_hours: 72 })),
  saveCreatorTemplateApprovalSlaConfig: vi.fn(),
  fetchCreatorTemplateApprovalOverdue: vi.fn(async () => ({ approvals: [] })),
  transferCreatorTemplateApproval: vi.fn(),
  fetchCreatorTemplateApprovalSnapshotDiff: vi.fn(),
  fetchCreatorTemplateApprovalSnapshotDrift: vi.fn(async () => ({ drifted: false })),
  batchApproveCreatorTemplateApprovals: vi.fn(),
  batchRejectCreatorTemplateApprovals: vi.fn(),
}));

describe('useCreatorVolumePlanTemplates', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    templateMocks.fetchCreatorVolumeTemplates.mockResolvedValue({
      templates: [
        { id: 'three_act', name: '三幕式', scope: 'builtin', version_label: 'v1.0.0', version_semver_valid: true },
        { id: 'custom_a', name: '自定义', scope: 'project' },
      ],
    });
    templateMocks.applyCreatorVolumeTemplate.mockResolvedValue({
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
    expect(templateMocks.applyCreatorVolumeTemplate).toHaveBeenCalledWith({
      template_id: 'three_act',
      max_chapter: 100,
    });
    expect(editableVolumes.value).toHaveLength(1);
    expect(asEditableVolumes(editableVolumes).value[0].end_chapter).toBe(20);
    expect(onAfterApplyTemplate).toHaveBeenCalledTimes(1);
  });
});
