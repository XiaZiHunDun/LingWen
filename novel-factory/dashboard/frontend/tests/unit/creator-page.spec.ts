// tests/unit/creator-page.spec.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';

const creatorMocks = vi.hoisted(() => ({
  fetchCreatorOverview: vi.fn(),
  runCreatorLogicCheck: vi.fn(),
  fetchCreatorVolumePlan: vi.fn(),
  saveCreatorVolumePlan: vi.fn(),
  mergeCreatorVolumePlan: vi.fn(),
  splitCreatorVolumePlan: vi.fn(),
  fetchCreatorVolumeTemplates: vi.fn(),
  applyCreatorVolumeTemplate: vi.fn(),
  saveCreatorVolumeTemplate: vi.fn(),
  deleteCreatorVolumeTemplate: vi.fn(),
  renameCreatorVolumeTemplate: vi.fn(),
  exportCreatorVolumeTemplates: vi.fn(),
  importCreatorVolumeTemplates: vi.fn(),
  fetchCreatorVolumeTemplateSyncSources: vi.fn(),
  syncCreatorVolumeTemplates: vi.fn(),
  publishCreatorVolumeTemplateToFactory: vi.fn(),
  pullCreatorFactoryVolumeTemplates: vi.fn(),
  deleteCreatorFactoryVolumeTemplate: vi.fn(),
  fetchCreatorOnboarding: vi.fn(),
  saveCreatorOnboardingProgress: vi.fn(),
  applyCreatorOnboardingShare: vi.fn(),
  saveCreatorOnboardingNotes: vi.fn(),
  setCreatorVolumeTemplateVersion: vi.fn(),
  fetchCreatorChapterPreview: vi.fn(),
  saveCreatorChapterBody: vi.fn(),
  generateCreatorVolumeSummary: vi.fn(),
  dismissCreatorWizardPanel: vi.fn(),
  fetchCreatorSettingsDocs: vi.fn(),
  saveCreatorSettingsDocs: vi.fn(),
  previewCreatorSettingsDocs: vi.fn(),
  previewCreatorSettingsThreeWay: vi.fn(),
  previewCreatorSettingsMerge: vi.fn(),
  fetchCreatorMergePreferences: vi.fn(),
  exportCreatorMergePreferences: vi.fn(),
  importCreatorMergePreferences: vi.fn(),
  fetchCreatorMergePresetPackages: vi.fn(),
  exportCreatorMergePresetPackages: vi.fn(),
  importCreatorMergePresetPackages: vi.fn(),
  fetchCreatorVolumeTemplateChangelog: vi.fn(),
  fetchCreatorOnboardingNotifications: vi.fn(),
  ackCreatorOnboardingNotifications: vi.fn(),
  fetchCreatorOnboardingWebhook: vi.fn(),
  saveCreatorOnboardingWebhook: vi.fn(),
  fetchCreatorOnboardingEmail: vi.fn(),
  saveCreatorOnboardingEmail: vi.fn(),
  rollbackCreatorVolumeTemplate: vi.fn(),
  fetchCreatorTemplateApprovals: vi.fn(),
  submitCreatorTemplateVersionApproval: vi.fn(),
  approveCreatorTemplateApproval: vi.fn(),
  rejectCreatorTemplateApproval: vi.fn(),
  fetchCreatorOnboardingNotificationDigest: vi.fn(),
  fetchCreatorOnboardingDigestSchedule: vi.fn(),
  saveCreatorOnboardingDigestSchedule: vi.fn(),
  dispatchCreatorOnboardingDigest: vi.fn(),
  fetchCreatorOnboardingDigestRetryQueue: vi.fn(),
  fetchCreatorOnboardingDigestStats: vi.fn(),
  processCreatorOnboardingDigestRetries: vi.fn(),
  fetchCreatorFactoryMergePresetPackages: vi.fn(),
  fetchCreatorMergePresetGraph: vi.fn(),
  fetchCreatorMergePresetConflicts: vi.fn(),
  fetchCreatorMergePresetConflictFixes: vi.fn(),
  applyCreatorMergePresetConflictFix: vi.fn(),
  applyAllCreatorMergePresetConflictFixes: vi.fn(),
  preflightCreatorMergePresetImport: vi.fn(),
  previewCreatorMergePresetImportDiff: vi.fn(),
  applyCreatorMergePresetToposort: vi.fn(),
  fetchCreatorTemplateApprovalChainConfig: vi.fn(),
  saveCreatorTemplateApprovalChainConfig: vi.fn(),
  fetchCreatorTemplateApprovalHistory: vi.fn(),
  exportCreatorTemplateApprovalAudit: vi.fn(),
  fetchCreatorTemplateApprovalSlaConfig: vi.fn(),
  saveCreatorTemplateApprovalSlaConfig: vi.fn(),
  fetchCreatorTemplateApprovalOverdue: vi.fn(),
  transferCreatorTemplateApproval: vi.fn(),
  fetchCreatorTemplateApprovalSnapshotDiff: vi.fn(),
  fetchCreatorTemplateApprovalSnapshotDrift: vi.fn(),
  batchApproveCreatorTemplateApprovals: vi.fn(),
  batchRejectCreatorTemplateApprovals: vi.fn(),
  fetchCreatorOnboardingDigestDeadLetter: vi.fn(),
  replayCreatorOnboardingDigestDeadLetter: vi.fn(),
  preflightCreatorFactoryMergePresetPull: vi.fn(),
  fetchCreatorMergePresetChangelog: vi.fn(),
  fetchCreatorMergePresetChangelogDiff: vi.fn(),
  fetchCreatorMergePresetToposort: vi.fn(),
  publishCreatorMergePresetToFactory: vi.fn(),
  pullCreatorFactoryMergePresetPackages: vi.fn(),
  fetchCreatorSettingsHistory: vi.fn(),
  restoreCreatorSettingsSnapshot: vi.fn(),
  studioProductionPreflight: vi.fn(),
  studioProductionRun: vi.fn(),
  fetchStudioActiveBatchJob: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorOverview: creatorMocks.fetchCreatorOverview,
  runCreatorLogicCheck: creatorMocks.runCreatorLogicCheck,
  fetchCreatorVolumePlan: creatorMocks.fetchCreatorVolumePlan,
  saveCreatorVolumePlan: creatorMocks.saveCreatorVolumePlan,
  mergeCreatorVolumePlan: creatorMocks.mergeCreatorVolumePlan,
  splitCreatorVolumePlan: creatorMocks.splitCreatorVolumePlan,
  fetchCreatorVolumeTemplates: creatorMocks.fetchCreatorVolumeTemplates,
  applyCreatorVolumeTemplate: creatorMocks.applyCreatorVolumeTemplate,
  saveCreatorVolumeTemplate: creatorMocks.saveCreatorVolumeTemplate,
  deleteCreatorVolumeTemplate: creatorMocks.deleteCreatorVolumeTemplate,
  renameCreatorVolumeTemplate: creatorMocks.renameCreatorVolumeTemplate,
  exportCreatorVolumeTemplates: creatorMocks.exportCreatorVolumeTemplates,
  importCreatorVolumeTemplates: creatorMocks.importCreatorVolumeTemplates,
  fetchCreatorVolumeTemplateSyncSources: creatorMocks.fetchCreatorVolumeTemplateSyncSources,
  syncCreatorVolumeTemplates: creatorMocks.syncCreatorVolumeTemplates,
  publishCreatorVolumeTemplateToFactory: creatorMocks.publishCreatorVolumeTemplateToFactory,
  pullCreatorFactoryVolumeTemplates: creatorMocks.pullCreatorFactoryVolumeTemplates,
  deleteCreatorFactoryVolumeTemplate: creatorMocks.deleteCreatorFactoryVolumeTemplate,
  fetchCreatorOnboarding: creatorMocks.fetchCreatorOnboarding,
  saveCreatorOnboardingProgress: creatorMocks.saveCreatorOnboardingProgress,
  applyCreatorOnboardingShare: creatorMocks.applyCreatorOnboardingShare,
  saveCreatorOnboardingNotes: creatorMocks.saveCreatorOnboardingNotes,
  setCreatorVolumeTemplateVersion: creatorMocks.setCreatorVolumeTemplateVersion,
  fetchCreatorChapterPreview: creatorMocks.fetchCreatorChapterPreview,
  saveCreatorChapterBody: creatorMocks.saveCreatorChapterBody,
  generateCreatorVolumeSummary: creatorMocks.generateCreatorVolumeSummary,
  dismissCreatorWizardPanel: creatorMocks.dismissCreatorWizardPanel,
  fetchCreatorSettingsDocs: creatorMocks.fetchCreatorSettingsDocs,
  saveCreatorSettingsDocs: creatorMocks.saveCreatorSettingsDocs,
  previewCreatorSettingsDocs: creatorMocks.previewCreatorSettingsDocs,
  previewCreatorSettingsThreeWay: creatorMocks.previewCreatorSettingsThreeWay,
  previewCreatorSettingsMerge: creatorMocks.previewCreatorSettingsMerge,
  fetchCreatorMergePreferences: creatorMocks.fetchCreatorMergePreferences,
  exportCreatorMergePreferences: creatorMocks.exportCreatorMergePreferences,
  importCreatorMergePreferences: creatorMocks.importCreatorMergePreferences,
  fetchCreatorMergePresetPackages: creatorMocks.fetchCreatorMergePresetPackages,
  exportCreatorMergePresetPackages: creatorMocks.exportCreatorMergePresetPackages,
  importCreatorMergePresetPackages: creatorMocks.importCreatorMergePresetPackages,
  fetchCreatorVolumeTemplateChangelog: creatorMocks.fetchCreatorVolumeTemplateChangelog,
  fetchCreatorOnboardingNotifications: creatorMocks.fetchCreatorOnboardingNotifications,
  ackCreatorOnboardingNotifications: creatorMocks.ackCreatorOnboardingNotifications,
  fetchCreatorOnboardingWebhook: creatorMocks.fetchCreatorOnboardingWebhook,
  saveCreatorOnboardingWebhook: creatorMocks.saveCreatorOnboardingWebhook,
  fetchCreatorOnboardingEmail: creatorMocks.fetchCreatorOnboardingEmail,
  saveCreatorOnboardingEmail: creatorMocks.saveCreatorOnboardingEmail,
  rollbackCreatorVolumeTemplate: creatorMocks.rollbackCreatorVolumeTemplate,
  fetchCreatorTemplateApprovals: creatorMocks.fetchCreatorTemplateApprovals,
  submitCreatorTemplateVersionApproval: creatorMocks.submitCreatorTemplateVersionApproval,
  approveCreatorTemplateApproval: creatorMocks.approveCreatorTemplateApproval,
  rejectCreatorTemplateApproval: creatorMocks.rejectCreatorTemplateApproval,
  fetchCreatorOnboardingNotificationDigest: creatorMocks.fetchCreatorOnboardingNotificationDigest,
  fetchCreatorOnboardingDigestSchedule: creatorMocks.fetchCreatorOnboardingDigestSchedule,
  saveCreatorOnboardingDigestSchedule: creatorMocks.saveCreatorOnboardingDigestSchedule,
  dispatchCreatorOnboardingDigest: creatorMocks.dispatchCreatorOnboardingDigest,
  fetchCreatorOnboardingDigestRetryQueue: creatorMocks.fetchCreatorOnboardingDigestRetryQueue,
  fetchCreatorOnboardingDigestStats: creatorMocks.fetchCreatorOnboardingDigestStats,
  processCreatorOnboardingDigestRetries: creatorMocks.processCreatorOnboardingDigestRetries,
  fetchCreatorFactoryMergePresetPackages: creatorMocks.fetchCreatorFactoryMergePresetPackages,
  fetchCreatorMergePresetGraph: creatorMocks.fetchCreatorMergePresetGraph,
  fetchCreatorMergePresetConflicts: creatorMocks.fetchCreatorMergePresetConflicts,
  fetchCreatorMergePresetConflictFixes: creatorMocks.fetchCreatorMergePresetConflictFixes,
  applyCreatorMergePresetConflictFix: creatorMocks.applyCreatorMergePresetConflictFix,
  applyAllCreatorMergePresetConflictFixes: creatorMocks.applyAllCreatorMergePresetConflictFixes,
  preflightCreatorMergePresetImport: creatorMocks.preflightCreatorMergePresetImport,
  previewCreatorMergePresetImportDiff: creatorMocks.previewCreatorMergePresetImportDiff,
  applyCreatorMergePresetToposort: creatorMocks.applyCreatorMergePresetToposort,
  fetchCreatorTemplateApprovalChainConfig: creatorMocks.fetchCreatorTemplateApprovalChainConfig,
  saveCreatorTemplateApprovalChainConfig: creatorMocks.saveCreatorTemplateApprovalChainConfig,
  fetchCreatorTemplateApprovalHistory: creatorMocks.fetchCreatorTemplateApprovalHistory,
  exportCreatorTemplateApprovalAudit: creatorMocks.exportCreatorTemplateApprovalAudit,
  fetchCreatorTemplateApprovalSlaConfig: creatorMocks.fetchCreatorTemplateApprovalSlaConfig,
  saveCreatorTemplateApprovalSlaConfig: creatorMocks.saveCreatorTemplateApprovalSlaConfig,
  fetchCreatorTemplateApprovalOverdue: creatorMocks.fetchCreatorTemplateApprovalOverdue,
  transferCreatorTemplateApproval: creatorMocks.transferCreatorTemplateApproval,
  fetchCreatorTemplateApprovalSnapshotDiff: creatorMocks.fetchCreatorTemplateApprovalSnapshotDiff,
  fetchCreatorTemplateApprovalSnapshotDrift: creatorMocks.fetchCreatorTemplateApprovalSnapshotDrift,
  batchApproveCreatorTemplateApprovals: creatorMocks.batchApproveCreatorTemplateApprovals,
  batchRejectCreatorTemplateApprovals: creatorMocks.batchRejectCreatorTemplateApprovals,
  fetchCreatorOnboardingDigestDeadLetter: creatorMocks.fetchCreatorOnboardingDigestDeadLetter,
  replayCreatorOnboardingDigestDeadLetter: creatorMocks.replayCreatorOnboardingDigestDeadLetter,
  preflightCreatorFactoryMergePresetPull: creatorMocks.preflightCreatorFactoryMergePresetPull,
  fetchCreatorMergePresetChangelog: creatorMocks.fetchCreatorMergePresetChangelog,
  fetchCreatorMergePresetChangelogDiff: creatorMocks.fetchCreatorMergePresetChangelogDiff,
  fetchCreatorMergePresetToposort: creatorMocks.fetchCreatorMergePresetToposort,
  publishCreatorMergePresetToFactory: creatorMocks.publishCreatorMergePresetToFactory,
  pullCreatorFactoryMergePresetPackages: creatorMocks.pullCreatorFactoryMergePresetPackages,
  fetchCreatorSettingsHistory: creatorMocks.fetchCreatorSettingsHistory,
  restoreCreatorSettingsSnapshot: creatorMocks.restoreCreatorSettingsSnapshot,
  studioProductionPreflight: creatorMocks.studioProductionPreflight,
  studioProductionRun: creatorMocks.studioProductionRun,
  fetchStudioActiveBatchJob: creatorMocks.fetchStudioActiveBatchJob,
}));

vi.mock('../../src/composables/useStudioProject.js', async () => {
  const { ref } = await import('vue');
  return {
    useStudioProject: () => ({
      projectRevision: ref(0),
    }),
  };
});

const navMocks = vi.hoisted(() => ({
  focusWizard: null,
  focusWizardStep: null,
  focusWizardDone: null,
  focusWizardNotes: null,
  setWizardDeepLink: vi.fn(),
  buildWizardShareUrl: vi.fn(() => 'http://localhost/?nav=creator&wizard=1&done=init'),
}));

vi.mock('../../src/composables/useDashboardNav.js', async () => {
  const { ref } = await import('vue');
  const focusWizard = ref(false);
  const focusWizardStep = ref(null);
  const focusWizardDone = ref([]);
  const focusWizardNotes = ref({});
  navMocks.focusWizard = focusWizard;
  navMocks.focusWizardStep = focusWizardStep;
  navMocks.focusWizardDone = focusWizardDone;
  navMocks.focusWizardNotes = focusWizardNotes;
  navMocks.setWizardDeepLink.mockImplementation((open, step) => {
    focusWizard.value = Boolean(open);
    if (step !== undefined) focusWizardStep.value = step;
  });
  return {
    useDashboardNav: () => ({
      focusWizard,
      focusWizardStep,
      focusWizardDone,
      focusWizardNotes,
      setWizardDeepLink: navMocks.setWizardDeepLink,
      buildWizardShareUrl: navMocks.buildWizardShareUrl,
    }),
  };
});

import CreatorPage from '../../src/pages/CreatorPage.vue';

const overviewFixture = {
  slug: 'demo-book',
  name: '演示书',
  creation_mode: 'advance',
  quality_profile: 'creator_relaxed',
  max_chapter: 12,
  chapters_written: 3,
  coverage_pct: 25,
  chapters: [
    { chapter: 1, has_body: true, has_outline: true, word_count: 2000, excerpt: '第一章' },
    { chapter: 2, has_body: false, has_outline: true, word_count: 0, excerpt: null },
    { chapter: 8, has_body: true, has_outline: true, word_count: 500, excerpt: '越界' },
  ],
  volume_summaries: [],
  pillars_excerpt: '支柱',
  pillars_path: '/docs/novel-pillars.md',
  global_outline_excerpt: '大纲',
  global_outline_path: '/全局大纲.md',
  p0_count: 0,
  quality_report_available: true,
  companion_check_cmd: 'bash scripts/run-companion-check.sh',
  advance_batch_hint: 'bash scripts/run-advance-volume.sh 1 10 10 0.30',
  notify_per_chapter: false,
  advance_volume_summary: true,
  locked_volume_count: 1,
  deviation_count: 1,
  deviation_total_count: 2,
  alert_count: 1,
  deviations: [
    { type: 'missing_body', severity: 'warn', chapter: 2, volume_label: '一', message: '缺正文' },
    { type: 'outside_locked_plan', severity: 'alert', chapter: 8, volume_label: null, message: '越界' },
  ],
  ui_profile: {
    creation_mode: 'advance',
    quality_profile: 'creator_relaxed',
    primary_action: 'volume_pulse',
    show_studio_workflow: true,
    show_digest_ops: true,
    show_factory_presets: true,
    show_template_version_ops: true,
    show_merge_preset_advanced: true,
    simplified_notifications: false,
    volume_pulse_enabled: true,
        wizard_default_collapsed: false,
        wizard_expand_if_incomplete: false,
        chapter_inline_edit: false,
        chapter_full_preview: true,
        logic_check_inline_issues: false,
        deviation_min_severity: 'alert',
  },
  volume_pulse: {
    volume_count: 1,
    alert_count: 0,
    warn_count: 1,
    overall_status: 'warn',
    alerts_only: true,
    volumes: [
      {
        label: '一',
        start_chapter: 1,
        end_chapter: 5,
        written: 1,
        total_chapters: 5,
        progress_pct: 20,
        locked: true,
        status: 'warn',
        deviation_count: 1,
        headline: '已写 1/5 章 · 卷纲已锁定',
      },
    ],
    latest_summary: null,
  },
};

describe('CreatorPage', () => {
  beforeEach(() => {
    navMocks.focusWizard.value = false;
    navMocks.focusWizardStep.value = null;
    navMocks.focusWizardDone.value = [];
    navMocks.focusWizardNotes.value = {};
    navMocks.setWizardDeepLink.mockClear();
    creatorMocks.fetchCreatorOverview.mockResolvedValue(overviewFixture);
    creatorMocks.fetchCreatorVolumePlan.mockResolvedValue({
      volumes: [
        {
          label: '一',
          start_chapter: 1,
          end_chapter: 5,
          core_conflict: '开篇',
          locked: true,
        },
        {
          label: '二',
          start_chapter: 6,
          end_chapter: 10,
          core_conflict: '发展',
          locked: false,
        },
      ],
      deviations: overviewFixture.deviations,
      revision: 'abc123',
    });
    creatorMocks.saveCreatorVolumePlan.mockResolvedValue({});
    creatorMocks.fetchCreatorChapterPreview.mockResolvedValue({
      chapter: 1,
      has_body: true,
      has_outline: true,
      word_count: 2000,
      body_preview: '第一章正文预览',
      outline_preview: '大纲预览',
      body_truncated: false,
      outline_truncated: false,
      body_text: '第一章正文预览',
    });
    creatorMocks.saveCreatorChapterBody.mockResolvedValue({
      chapter: 1,
      has_body: true,
      has_outline: true,
      word_count: 2000,
      body_preview: '第一章正文预览',
      outline_preview: '大纲预览',
      body_truncated: false,
      outline_truncated: false,
      body_text: '第一章正文预览',
    });
    creatorMocks.generateCreatorVolumeSummary.mockResolvedValue({
      path: 'docs/volume-summary-ch001-010.md',
      written: true,
    });
    creatorMocks.dismissCreatorWizardPanel.mockResolvedValue({
      mode_label: '陪伴',
      max_chapter: 12,
      steps: [{ id: 'init', title: '初始化' }],
      completed_step_ids: [],
      progress_pct: 0,
      wizard_panel_dismissed: true,
    });
    creatorMocks.fetchCreatorSettingsDocs.mockResolvedValue({
      pillars_text: '# 支柱',
      global_outline_text: '# 大纲',
      pillars_path: '/docs/novel-pillars.md',
      global_outline_path: '/全局大纲.md',
      pillars_revision: 'rev-p',
      global_outline_revision: 'rev-o',
    });
    creatorMocks.mergeCreatorVolumePlan.mockResolvedValue({
      volumes: [
        {
          label: '合并',
          start_chapter: 1,
          end_chapter: 10,
          core_conflict: '开篇 / 发展',
          locked: true,
        },
      ],
      merged_label: '合并',
      merged_range: 'ch001–ch010',
    });
    creatorMocks.splitCreatorVolumePlan.mockResolvedValue({
      volumes: [
        { label: '一上', start_chapter: 1, end_chapter: 5, core_conflict: '开篇', locked: true },
        { label: '一下', start_chapter: 6, end_chapter: 10, core_conflict: '发展', locked: false },
      ],
      first_label: '一上',
      second_label: '一下',
      first_range: 'ch001–ch005',
      second_range: 'ch006–ch010',
    });
    creatorMocks.fetchCreatorVolumeTemplates.mockResolvedValue({
      templates: [
        { id: 'three_act', name: '三幕式', description: '建置对抗结局', builtin: true, scope: 'builtin' },
        { id: 'factory_shared', name: '工厂模板', description: '共享', builtin: false, scope: 'factory' },
        { id: 'custom_test', name: '我的结构', description: '自定义', builtin: false, scope: 'project', version_label: 'v1.0.0', version_semver_valid: true, version_changelog: [{ version_label: 'v1.0.0', previous_label: null, changed_at: '2026-06-22T12:00:00+00:00', diff_summary: { changed: false, lines_added: 0, lines_removed: 0, snippet: [] } }] },
      ],
    });
    creatorMocks.applyCreatorVolumeTemplate.mockResolvedValue({
      template_id: 'three_act',
      template_name: '三幕式',
      volumes: [
        { label: '第一幕', start_chapter: 1, end_chapter: 3, core_conflict: '建置', locked: false },
        { label: '第二幕', start_chapter: 4, end_chapter: 9, core_conflict: '对抗', locked: false },
        { label: '第三幕', start_chapter: 10, end_chapter: 12, core_conflict: '结局', locked: false },
      ],
    });
    creatorMocks.saveCreatorVolumeTemplate.mockResolvedValue({
      id: 'custom_test',
      name: '我的结构',
      description: '',
    });
    creatorMocks.fetchCreatorOnboarding.mockResolvedValue({
      slug: 'demo-book',
      creation_mode: 'advance',
      mode_label: '推进',
      max_chapter: 12,
      steps: [
        { id: 'init', title: '新建', detail: 'init-project' },
        { id: 'pillars', title: '支柱', detail: '编辑设定' },
        { id: 'volume', title: '卷纲', detail: '锁定卷纲' },
      ],
      checklist_doc: 'docs/advance-walkthrough-checklist.md',
      smoke_command: 'bash scripts/verify-advance-walkthrough.sh',
      onboarding_doc: 'docs/creator-onboarding-wizard.md',
      completed_step_ids: ['init'],
      auto_completed_step_ids: ['init', 'dashboard'],
      step_notes: { volume: '先锁卷纲' },
      step_mentions: { volume: ['batch'] },
      unread_mention_count: 1,
      progress_pct: 33,
    });
    creatorMocks.saveCreatorOnboardingNotes.mockResolvedValue({
      step_notes: { volume: '先锁卷纲' },
      completed_step_ids: ['init'],
      progress_pct: 33,
    });
    creatorMocks.setCreatorVolumeTemplateVersion.mockResolvedValue({
      id: 'custom_test',
      version_label: 'v2.0.0',
    });
    creatorMocks.exportCreatorMergePreferences.mockResolvedValue({
      schema_version: '1',
      project: { pillars_merge_source: 'disk' },
      global: { pillars_merge_source: 'disk' },
    });
    creatorMocks.importCreatorMergePreferences.mockResolvedValue({
      scope: 'both',
    });
    creatorMocks.fetchCreatorMergePresetPackages.mockResolvedValue({
      packages: [
        { id: 'all_disk', name: '全选磁盘', builtin: true, pillars_merge_source: 'disk', global_outline_merge_source: 'disk' },
        { id: 'pillars_disk_outline_editor', name: '支柱磁盘·大纲编辑器', builtin: true, scope: 'builtin', depends_on: ['all_disk', 'all_editor'], pillars_merge_source: 'disk', global_outline_merge_source: 'editor' },
        { id: 'my_combo', name: '我的组合', builtin: false, scope: 'project', version_label: 'v1.0.0', version_semver_valid: true, pillars_merge_source: 'disk', global_outline_merge_source: 'editor' },
      ],
    });
    creatorMocks.fetchCreatorFactoryMergePresetPackages.mockResolvedValue({
      packages: [{ id: 'factory_preset_team', name: '工厂组合', builtin: false, scope: 'factory', pillars_merge_source: 'disk', global_outline_merge_source: 'editor' }],
    });
    creatorMocks.fetchCreatorMergePresetGraph.mockResolvedValue({
      node_count: 3,
      edge_count: 2,
      nodes: [
        { id: 'all_disk', name: '全选磁盘', scope: 'builtin' },
        { id: 'pillars_disk_outline_editor', name: '支柱磁盘·大纲编辑器', scope: 'builtin' },
      ],
      edges: [
        { from_pkg: 'pillars_disk_outline_editor', to: 'all_disk', relation: 'depends_on' },
        { from_pkg: 'pillars_disk_outline_editor', to: 'all_editor', relation: 'depends_on' },
      ],
    });
    creatorMocks.fetchCreatorMergePresetConflicts.mockResolvedValue({
      conflict_count: 1,
      conflicts: [{ type: 'missing_dependency', package_id: 'my_combo', dependency_id: 'ghost', message: 'my_combo depends on unknown package ghost' }],
    });
    creatorMocks.fetchCreatorMergePresetConflictFixes.mockResolvedValue({
      fix_count: 1,
      fixes: [{
        id: 'fix_0',
        conflict_type: 'missing_dependency',
        package_id: 'my_combo',
        action: 'remove_dependency',
        dependency_id: 'ghost',
        label: '从 my_combo 移除依赖 ghost',
        applicable: true,
      }],
    });
    creatorMocks.exportCreatorTemplateApprovalAudit.mockResolvedValue({
      schema_version: '1',
      count: 1,
      approvals: [{ id: 'aprv_done', status: 'approved', chain_log: [] }],
    });
    creatorMocks.applyAllCreatorMergePresetConflictFixes.mockResolvedValue({ applied: 2, conflict_count: 0 });
    creatorMocks.applyCreatorMergePresetConflictFix.mockResolvedValue({
      package_id: 'my_combo',
      action: 'remove_dependency',
      conflict_count: 0,
      package: { id: 'my_combo', name: '我的组合' },
    });
    creatorMocks.preflightCreatorMergePresetImport.mockResolvedValue({
      would_import: 1,
      conflict_count: 1,
      blocked: true,
      conflicts: [{ type: 'missing_dependency', package_id: 'x', message: 'bad' }],
    });
    creatorMocks.previewCreatorMergePresetImportDiff.mockResolvedValue({
      added: ['pkg_new'],
      updated: [],
      removed: [],
      unchanged_count: 0,
      replace: false,
    });
    creatorMocks.applyCreatorMergePresetToposort.mockResolvedValue({ reordered: 2, order: ['a', 'b'] });
    creatorMocks.fetchCreatorMergePresetToposort.mockResolvedValue({
      order: ['a', 'b'],
      edges: [{ from: 'a', to: 'b', relation: 'depends_on' }],
      edge_count: 1,
    });
    creatorMocks.fetchCreatorMergePresetChangelog.mockResolvedValue({
      package_id: 'my_combo',
      entry_count: 1,
      entries: [{ action: 'update', changed_fields: ['name'] }],
    });
    creatorMocks.fetchCreatorOnboardingDigestDeadLetter.mockResolvedValue({
      item_count: 1,
      items: [{ channel: 'webhook', error: 'timeout', attempts: 5 }],
    });
    creatorMocks.preflightCreatorFactoryMergePresetPull.mockResolvedValue({
      would_import: 1,
      conflict_count: 0,
      blocked: false,
      conflicts: [],
    });
    creatorMocks.fetchCreatorTemplateApprovalSnapshotDiff.mockResolvedValue({
      approval_id: 'aprv_test',
      template_id: 'custom_test',
      diff_summary: { changed: true, lines_added: 1, lines_removed: 0 },
      visual_diff: { before: '', after: 'x', lines: [] },
    });
    creatorMocks.transferCreatorTemplateApproval.mockResolvedValue({
      id: 'aprv_test',
      current_assignee: 'carol',
      status: 'pending',
    });
    creatorMocks.fetchCreatorTemplateApprovalSnapshotDrift.mockResolvedValue({
      approval_id: 'aprv_test',
      template_id: 'custom_test',
      drifted: false,
      diff_summary: { changed: false },
    });
    creatorMocks.batchApproveCreatorTemplateApprovals.mockResolvedValue({
      approved: 2,
      rejected: 0,
      total: 2,
      results: [],
    });
    creatorMocks.replayCreatorOnboardingDigestDeadLetter.mockResolvedValue({
      replayed: true,
      index: 0,
      channel: 'webhook',
      retry_queue_size: 1,
      dead_letter_count: 0,
    });
    creatorMocks.fetchCreatorMergePresetChangelogDiff.mockResolvedValue({
      package_id: 'my_combo',
      entry_index: 0,
      change_count: 1,
      changes: [{ field: 'name', before: 'A', after: 'B' }],
    });
    creatorMocks.fetchCreatorTemplateApprovals.mockResolvedValue({
      approvals: [
        {
          id: 'aprv_test',
          template_id: 'custom_test',
          status: 'pending',
          version_label: 'v2.0.0',
          previous_label: 'v1.0.0',
          has_volumes_snapshot: true,
          chain_step: 1,
          chain_total: 2,
          chain_progress: '1/2',
          or_signing: true,
          current_assignees: ['alice', 'bob'],
        },
        {
          id: 'aprv_test2',
          template_id: 'custom_test2',
          status: 'pending',
          version_label: 'v3.0.0',
          previous_label: 'v2.0.0',
          chain_step: 1,
          chain_total: 1,
          chain_progress: '1/1',
        },
      ],
    });
    creatorMocks.fetchCreatorTemplateApprovalChainConfig.mockResolvedValue({ required_steps: 2, step_assignees: ['alice'] });
    creatorMocks.saveCreatorTemplateApprovalChainConfig.mockResolvedValue({ required_steps: 3 });
    creatorMocks.fetchCreatorTemplateApprovalHistory.mockResolvedValue({
      approvals: [{
        id: 'aprv_done',
        template_id: 'custom_test',
        status: 'approved',
        version_label: 'v2.0.0',
        previous_label: 'v1.0.0',
        chain_log: [{ step: 1, approved_at: '2026-06-22T12:00:00+00:00' }],
      }],
    });
    creatorMocks.fetchCreatorTemplateApprovalSlaConfig.mockResolvedValue({
      timeout_hours: 72,
      email_on_submit: true,
      email_on_reject: true,
      email_on_overdue: true,
    });
    creatorMocks.saveCreatorTemplateApprovalSlaConfig.mockResolvedValue({
      timeout_hours: 48,
      email_on_submit: true,
      email_on_reject: false,
      email_on_overdue: true,
    });
    creatorMocks.fetchCreatorTemplateApprovalOverdue.mockResolvedValue({
      overdue_count: 1,
      approvals: [{ id: 'aprv_old', template_id: 'custom_test', status: 'pending', hours_pending: 80 }],
    });
    creatorMocks.submitCreatorTemplateVersionApproval.mockResolvedValue({
      id: 'aprv_new',
      template_id: 'custom_test',
      status: 'pending',
      version_label: 'v2.0.0',
    });
    creatorMocks.approveCreatorTemplateApproval.mockResolvedValue({
      id: 'aprv_test',
      template_id: 'custom_test',
      status: 'approved',
      version_label: 'v2.0.0',
    });
    creatorMocks.fetchCreatorOnboardingNotificationDigest.mockResolvedValue({
      unread: 1,
      group_count: 1,
      groups: [{ handle: 'batch', count: 1, steps: [{ step_id: 'volume', count: 1 }], excerpts: ['先锁卷纲'] }],
    });
    creatorMocks.fetchCreatorOnboardingDigestSchedule.mockResolvedValue({
      enabled: false,
      interval_hours: 24,
      last_sent_at: null,
      channels: ['webhook'],
      handle_channels: {},
      quiet_hours_start: null,
      quiet_hours_end: null,
    });
    creatorMocks.fetchCreatorOnboardingDigestStats.mockResolvedValue({
      sent_total: 2,
      failed_total: 1,
      last_sent_at: '2026-06-22T12:00:00+00:00',
      last_failure_at: null,
    });
    creatorMocks.fetchCreatorOnboardingDigestRetryQueue.mockResolvedValue({
      item_count: 1,
      items: [{ channel: 'webhook', error: 'timeout', attempts: 1 }],
    });
    creatorMocks.processCreatorOnboardingDigestRetries.mockResolvedValue({ retried: 1, remaining: 0 });
    creatorMocks.saveCreatorOnboardingDigestSchedule.mockResolvedValue({
      enabled: true,
      interval_hours: 12,
      last_sent_at: null,
      channels: ['webhook', 'email'],
    });
    creatorMocks.dispatchCreatorOnboardingDigest.mockResolvedValue({ sent: true });
    creatorMocks.publishCreatorMergePresetToFactory.mockResolvedValue({ id: 'factory_preset_my_combo', name: '我的组合', scope: 'factory' });
    creatorMocks.pullCreatorFactoryMergePresetPackages.mockResolvedValue({ imported: 1, total: 1, package_ids: ['factory_preset_team'] });
    creatorMocks.fetchCreatorOnboardingWebhook.mockResolvedValue({
      enabled: false,
      url: '',
      mention_handles: [],
      signing_secret: '',
    });
    creatorMocks.saveCreatorOnboardingWebhook.mockResolvedValue({
      enabled: true,
      url: 'https://example.com/hook',
      mention_handles: ['batch'],
      signing_secret: 'secret',
    });
    creatorMocks.fetchCreatorVolumeTemplateChangelog.mockResolvedValue({
      template_id: 'custom_test',
      entries: [{
        version_label: 'v1.0.0',
        previous_label: null,
        changed_at: '2026-06-22T12:00:00+00:00',
        diff_summary: { changed: true, lines_added: 1, lines_removed: 0, snippet: ['+一: ch1-12'] },
        visual_diff: { before: '', after: '一: ch1-12 x', lines: [{ type: 'add', text: '一: ch1-12 x' }] },
        can_rollback: true,
      }],
    });
    creatorMocks.rollbackCreatorVolumeTemplate.mockResolvedValue({
      id: 'custom_test',
      version_label: 'v1.0.0',
      rolled_back_to: 'v1.0.0',
    });
    creatorMocks.fetchCreatorOnboardingEmail.mockResolvedValue({
      enabled: false,
      to_addresses: [],
      mention_handles: [],
      smtp_host: '',
      smtp_port: 587,
      smtp_user: '',
      smtp_use_tls: true,
      from_address: '',
    });
    creatorMocks.saveCreatorOnboardingEmail.mockResolvedValue({
      enabled: true,
      to_addresses: ['writer@example.com'],
      mention_handles: ['batch'],
      smtp_host: 'smtp.example.com',
      smtp_port: 587,
      smtp_user: '',
      smtp_use_tls: true,
      from_address: 'writer@example.com',
    });
    creatorMocks.fetchCreatorOnboardingNotifications.mockResolvedValue({
      unread: 1,
      handles: ['batch'],
      notifications: [
        { id: 'n1', step_id: 'volume', handle: 'batch', note_excerpt: '先锁卷纲', created_at: '2026-06-22T12:00:00+00:00', read: false },
      ],
    });
    creatorMocks.exportCreatorMergePresetPackages.mockResolvedValue({
      schema_version: '1',
      count: 1,
      packages: [{ id: 'my_combo', name: '我的组合', pillars_merge_source: 'disk', global_outline_merge_source: 'editor' }],
    });
    creatorMocks.importCreatorMergePresetPackages.mockResolvedValue({
      imported: 1,
      total: 1,
      replaced: false,
      packages: [],
    });
    creatorMocks.ackCreatorOnboardingNotifications.mockResolvedValue({ acked: 1, unread: 0 });
    creatorMocks.saveCreatorOnboardingProgress.mockResolvedValue({
      completed_step_ids: ['init', 'pillars'],
      auto_completed_step_ids: ['init', 'dashboard'],
      progress_pct: 67,
    });
    creatorMocks.fetchCreatorMergePreferences.mockResolvedValue({
      pillars_merge_source: 'disk',
      global_outline_merge_source: 'history',
      merge_snapshot_id: 'snap1',
      pillars_merge_snapshot_id: 'snap1',
      global_outline_merge_snapshot_id: 'snap2',
      uses_global_default: true,
    });
    creatorMocks.applyCreatorOnboardingShare.mockResolvedValue({
      completed_step_ids: ['init', 'pillars', 'volume'],
      auto_completed_step_ids: ['init'],
      progress_pct: 100,
    });
    creatorMocks.publishCreatorVolumeTemplateToFactory.mockResolvedValue({
      id: 'factory_new',
      name: '我的结构',
      description: '工厂共享',
    });
    creatorMocks.pullCreatorFactoryVolumeTemplates.mockResolvedValue({
      imported: 1,
      total: 2,
      template_ids: ['factory_shared'],
    });
    creatorMocks.fetchCreatorVolumeTemplateSyncSources.mockResolvedValue({
      sources: [{ slug: 'other-book', name: '其他书', template_count: 2 }],
    });
    creatorMocks.syncCreatorVolumeTemplates.mockResolvedValue({
      imported: 2,
      total: 3,
      sources: ['other-book'],
    });
    creatorMocks.exportCreatorVolumeTemplates.mockResolvedValue({
      schema_version: '1',
      count: 1,
      templates: [{ id: 'custom_x', name: '导出', volumes: [] }],
    });
    creatorMocks.importCreatorVolumeTemplates.mockResolvedValue({
      imported: 1,
      total: 2,
      replaced: false,
    });
    creatorMocks.fetchCreatorSettingsHistory.mockResolvedValue({
      snapshots: [
        {
          id: 'snap1',
          saved_at: '2026-06-22T12:00:00+00:00',
          label: 'before-save',
          pillars_excerpt: '# 旧',
          global_outline_excerpt: '# 大纲',
          pillars_lines: 1,
          global_outline_lines: 1,
        },
      ],
      count: 1,
    });
    creatorMocks.restoreCreatorSettingsSnapshot.mockResolvedValue({
      pillars_text: '# 恢复',
      global_outline_text: '# 大纲',
      pillars_revision: 'r1',
      global_outline_revision: 'r2',
    });
    creatorMocks.saveCreatorSettingsDocs.mockResolvedValue({});
    creatorMocks.previewCreatorSettingsDocs.mockResolvedValue({
      has_changes: true,
      pillars: { changed: true, lines_added: 1, lines_removed: 0, snippet: ['+新行'] },
      global_outline: { changed: false, lines_added: 0, lines_removed: 0, snippet: [] },
    });
    creatorMocks.previewCreatorSettingsMerge.mockResolvedValue({
      pillars: {
        source: 'disk',
        vs_disk: { changed: false, lines_added: 0, lines_removed: 0, snippet: [] },
        vs_editor: { changed: true, lines_added: 1, lines_removed: 1, snippet: ['-旧', '+磁盘'] },
      },
      global_outline: {
        source: 'editor',
        vs_disk: { changed: false, lines_added: 0, lines_removed: 0, snippet: [] },
        vs_editor: { changed: false, lines_added: 0, lines_removed: 0, snippet: [] },
      },
    });
    creatorMocks.deleteCreatorVolumeTemplate.mockResolvedValue({ id: 'custom_test', deleted: true });
    creatorMocks.renameCreatorVolumeTemplate.mockResolvedValue({
      id: 'custom_test',
      name: '新结构',
      description: '',
    });
    creatorMocks.previewCreatorSettingsThreeWay.mockResolvedValue({
      has_changes: true,
      pillars: { changed: true, lines_added: 1, lines_removed: 0, snippet: ['+新行'] },
      global_outline: { changed: false, lines_added: 0, lines_removed: 0, snippet: [] },
      has_history: true,
      history_snapshot_id: 'snap1',
      disk_vs_history: {
        pillars: { changed: true, lines_added: 1, lines_removed: 1, snippet: [] },
        global_outline: { changed: false, lines_added: 0, lines_removed: 0, snippet: [] },
      },
      editor_vs_history: {
        pillars: { changed: true, lines_added: 2, lines_removed: 1, snippet: [] },
        global_outline: { changed: false, lines_added: 0, lines_removed: 0, snippet: [] },
      },
    });
    creatorMocks.studioProductionPreflight.mockResolvedValue({
      all_ok: true,
      batch_command: 'bash scripts/run-advance-volume.sh 1 5 5 0.3',
    });
    creatorMocks.studioProductionRun.mockResolvedValue({ job_id: 'abc', status: 'running' });
    creatorMocks.fetchStudioActiveBatchJob.mockResolvedValue(null);
  });

  it('renders three columns, volume plan, and deviation badge', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    expect(wrapper.find('[data-testid="creator-grid"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="volume-plan-panel"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="deviation-badge"]').text()).toContain('偏离');
    expect(wrapper.find('[data-testid="deviation-list"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="creation-mode-badge"]').text()).toContain('推进');
  });

  it('saves volume plan on button click', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    await wrapper.find('[data-testid="save-volume-plan-btn"]').trigger('click');
    await flushPromises();

    expect(creatorMocks.saveCreatorVolumePlan).toHaveBeenCalled();
  });

  it('shows chapter preview when row clicked', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    await wrapper.find('[data-testid="chapter-row-1"]').trigger('click');
    await flushPromises();

    expect(creatorMocks.fetchCreatorChapterPreview).toHaveBeenCalledWith(1, { full: true });
    expect(wrapper.find('[data-testid="chapter-preview-panel"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('第一章正文预览');
  });

  it('shows advance batch panel and settings editor', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    expect(wrapper.find('[data-testid="advance-batch-panel"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="pillars-textarea"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="save-settings-btn"]').exists()).toBe(true);
  });

  it('reorders volume rows with move down', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    await wrapper.find('[data-testid="volume-move-down-0"]').trigger('click');
    await flushPromises();

    const rows = wrapper.findAll('[data-testid^="volume-row-"]');
    expect(rows[0].find('.vol-label').element.value).toBe('二');
    expect(rows[1].find('.vol-label').element.value).toBe('一');
  });

  it('shows settings diff preview before confirm save', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    await wrapper.find('[data-testid="pillars-textarea"]').setValue('# 支柱\n新内容');
    await wrapper.find('[data-testid="save-settings-btn"]').trigger('click');
    await flushPromises();

    expect(creatorMocks.previewCreatorSettingsThreeWay).toHaveBeenCalled();
    expect(wrapper.find('[data-testid="settings-diff-panel"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="three-way-history-label"]').exists()).toBe(true);

    await wrapper.find('[data-testid="confirm-settings-btn"]').trigger('click');
    await flushPromises();

    expect(creatorMocks.saveCreatorSettingsDocs).toHaveBeenCalled();
  });

  it('shows volume merge panel and applies merge', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    expect(wrapper.find('[data-testid="volume-merge-panel"]').exists()).toBe(true);
    await wrapper.find('[data-testid="apply-merge-btn"]').trigger('click');
    await flushPromises();

    expect(creatorMocks.mergeCreatorVolumePlan).toHaveBeenCalled();
    expect(wrapper.find('[data-testid="merge-preview-line"]').text()).toContain('合并');
  });

  it('shows conflict banner on 409 save error', async () => {
    creatorMocks.saveCreatorVolumePlan.mockRejectedValueOnce(
      new Error('API Error 409: Conflict. Details: {"detail":"卷纲已在别处修改"}'),
    );
    const wrapper = mount(CreatorPage);
    await flushPromises();

    await wrapper.find('[data-testid="save-volume-plan-btn"]').trigger('click');
    await flushPromises();

    expect(wrapper.find('[data-testid="conflict-banner"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="conflict-reload-btn"]').exists()).toBe(true);
  });

  it('shows split panel and applies split', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    expect(wrapper.find('[data-testid="volume-split-panel"]').exists()).toBe(true);
    await wrapper.find('[data-testid="apply-split-btn"]').trigger('click');
    await flushPromises();

    expect(creatorMocks.splitCreatorVolumePlan).toHaveBeenCalled();
    expect(wrapper.find('[data-testid="split-preview-line"]').text()).toContain('一上');
  });

  it('shows settings history panel', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    expect(wrapper.find('[data-testid="settings-history-panel"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="history-row-snap1"]').exists()).toBe(true);
  });

  it('applies volume template from template library', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    expect(wrapper.find('[data-testid="volume-template-panel"]').exists()).toBe(true);
    await wrapper.find('[data-testid="apply-template-btn"]').trigger('click');
    await flushPromises();

    expect(creatorMocks.applyCreatorVolumeTemplate).toHaveBeenCalled();
    expect(wrapper.text()).toContain('三幕式');
  });

  it('shows onboarding wizard panel', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    expect(creatorMocks.fetchCreatorOnboarding).toHaveBeenCalled();
    expect(wrapper.find('[data-testid="onboarding-wizard-panel"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('入门向导');
    expect(wrapper.text()).toContain('advance-walkthrough-checklist');
  });

  it('opens onboarding wizard when wizard deep-link is active', async () => {
    navMocks.focusWizard.value = true;
    const wrapper = mount(CreatorPage);
    await flushPromises();

    const panel = wrapper.find('[data-testid="onboarding-wizard-panel"]');
    expect(panel.exists()).toBe(true);
    expect(panel.element.open).toBe(true);
  });

  it('highlights wizard step from step deep-link', async () => {
    navMocks.focusWizard.value = true;
    navMocks.focusWizardStep.value = 'volume';
    const wrapper = mount(CreatorPage);
    await flushPromises();

    expect(wrapper.find('.wizard-step--focused').exists()).toBe(true);
  });

  it('saves custom volume template', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    await wrapper.find('[data-testid="save-template-name-input"]').setValue('我的结构');
    await wrapper.find('[data-testid="save-template-btn"]').trigger('click');
    await flushPromises();

    expect(creatorMocks.saveCreatorVolumeTemplate).toHaveBeenCalled();
  });

  it('shows merge strategy when three-way conflict', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    await wrapper.find('[data-testid="pillars-textarea"]').setValue('# 支柱\n新内容');
    await wrapper.find('[data-testid="save-settings-btn"]').trigger('click');
    await flushPromises();

    expect(wrapper.find('[data-testid="merge-strategy-panel"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="merge-preview-visual"]').exists()).toBe(true);
    expect(creatorMocks.previewCreatorSettingsMerge).toHaveBeenCalled();
    await wrapper.find('[data-testid="pillars-merge-source"]').setValue('disk');
    await wrapper.find('[data-testid="confirm-settings-btn"]').trigger('click');
    await flushPromises();

    const call = creatorMocks.saveCreatorSettingsDocs.mock.calls.at(-1)?.[0];
    expect(call?.pillars_merge_source).toBe('disk');
  });

  it('deletes custom volume template', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    const select = wrapper.find('[data-testid="volume-template-select"]');
    await select.setValue('custom_test');
    await flushPromises();

    expect(wrapper.find('[data-testid="delete-template-btn"]').exists()).toBe(true);
    await wrapper.find('[data-testid="delete-template-btn"]').trigger('click');
    await flushPromises();

    expect(creatorMocks.deleteCreatorVolumeTemplate).toHaveBeenCalledWith('custom_test');
  });

  it('renames custom volume template', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    const select = wrapper.find('[data-testid="volume-template-select"]');
    await select.setValue('custom_test');
    await flushPromises();

    await wrapper.find('[data-testid="rename-template-name-input"]').setValue('新结构');
    await wrapper.find('[data-testid="rename-template-btn"]').trigger('click');
    await flushPromises();

    expect(creatorMocks.renameCreatorVolumeTemplate).toHaveBeenCalledWith('custom_test', {
      name: '新结构',
    });
  });

  it('applies merge preset to disk', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    await wrapper.find('[data-testid="pillars-textarea"]').setValue('# 支柱\n新内容');
    await wrapper.find('[data-testid="save-settings-btn"]').trigger('click');
    await flushPromises();

    await wrapper.find('[data-testid="merge-preset-disk"]').trigger('click');
    await flushPromises();

    expect(creatorMocks.previewCreatorSettingsMerge).toHaveBeenCalled();
    const mergeCall = creatorMocks.previewCreatorSettingsMerge.mock.calls.at(-1)?.[0];
    expect(mergeCall?.pillars_merge_source).toBe('disk');
    expect(mergeCall?.global_outline_merge_source).toBe('disk');
  });

  it('toggles wizard step completion', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    expect(wrapper.find('[data-testid="wizard-progress-label"]').text()).toContain('33%');
    const checkbox = wrapper.find('[data-testid="wizard-step-pillars"]');
    await checkbox.setValue(true);
    await flushPromises();

    expect(creatorMocks.saveCreatorOnboardingProgress).toHaveBeenCalled();
    expect(wrapper.find('[data-testid="wizard-progress-label"]').text()).toContain('67%');
  });

  it('loads merge preferences on mount', async () => {
    mount(CreatorPage);
    await flushPromises();
    expect(creatorMocks.fetchCreatorMergePreferences).toHaveBeenCalled();
  });

  it('exports custom templates', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    await wrapper.find('[data-testid="export-templates-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.exportCreatorVolumeTemplates).toHaveBeenCalled();
  });

  it('imports custom templates from json', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    await wrapper.find('[data-testid="toggle-import-templates-btn"]').trigger('click');
    await wrapper.find('[data-testid="import-templates-json"]').setValue(
      JSON.stringify({ templates: [{ name: '导入', source_max_chapter: 10, volumes: [{ label: '一', start_chapter: 1, end_chapter: 10, core_conflict: 'x' }] }] }),
    );
    await wrapper.find('[data-testid="import-templates-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.importCreatorVolumeTemplates).toHaveBeenCalled();
  });

  it('syncs templates from other projects', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    await wrapper.find('[data-testid="sync-templates-btn"]').trigger('click');
    await flushPromises();

    expect(creatorMocks.syncCreatorVolumeTemplates).toHaveBeenCalled();
  });

  it('restores merge snapshot from preferences', async () => {
    mount(CreatorPage);
    await flushPromises();

    expect(creatorMocks.fetchCreatorMergePreferences).toHaveBeenCalled();
  });

  it('copies wizard share link', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });

    const wrapper = mount(CreatorPage);
    await flushPromises();

    await wrapper.find('[data-testid="wizard-share-link-btn"]').trigger('click');
    await flushPromises();

    expect(navMocks.buildWizardShareUrl).toHaveBeenCalled();
    expect(wrapper.find('[data-testid="wizard-share-message"]').text()).toContain('已复制');
  });

  it('applies wizard share done from url', async () => {
    navMocks.focusWizardDone.value = ['volume'];
    mount(CreatorPage);
    await flushPromises();

    expect(creatorMocks.applyCreatorOnboardingShare).toHaveBeenCalledWith({
      completed_step_ids: ['volume'],
      step_notes: {},
    });
  });

  it('publishes project template to factory library', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    await wrapper.find('[data-testid="volume-template-select"]').setValue('custom_test');
    await flushPromises();
    await wrapper.find('[data-testid="publish-factory-template-btn"]').trigger('click');
    await flushPromises();

    expect(creatorMocks.publishCreatorVolumeTemplateToFactory).toHaveBeenCalledWith({
      template_id: 'custom_test',
    });
  });

  it('pulls templates from factory library', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    await wrapper.find('[data-testid="pull-factory-templates-btn"]').trigger('click');
    await flushPromises();

    expect(creatorMocks.pullCreatorFactoryVolumeTemplates).toHaveBeenCalled();
  });

  it('shows template version label in select', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    expect(wrapper.find('[data-testid="volume-template-select"]').text()).toContain('[v1.0.0]');
  });

  it('shows semver warning for invalid template version', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    await wrapper.find('[data-testid="volume-template-select"]').setValue('custom_test');
    await flushPromises();
    await wrapper.find('[data-testid="template-version-input"]').setValue('latest');
    await flushPromises();
    expect(wrapper.find('[data-testid="template-version-semver-warn"]').exists()).toBe(true);
  });

  it('shows wizard mention badges', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    expect(wrapper.find('[data-testid="wizard-mention-badge"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('@batch');
  });

  it('exports merge preferences', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    await wrapper.find('[data-testid="pillars-textarea"]').setValue('# 支柱\n新内容');
    await wrapper.find('[data-testid="save-settings-btn"]').trigger('click');
    await flushPromises();
    await wrapper.find('[data-testid="export-merge-prefs-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.exportCreatorMergePreferences).toHaveBeenCalled();
  });

  it('shows wizard notification badge', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    expect(wrapper.find('[data-testid="wizard-notification-badge"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="wizard-notifications-panel"]').exists()).toBe(true);
  });

  it('shows template version changelog', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    await wrapper.find('[data-testid="volume-template-select"]').setValue('custom_test');
    await flushPromises();
    expect(wrapper.find('[data-testid="template-version-changelog"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="template-changelog-diff"]').exists()).toBe(true);
  });

  it('filters wizard notifications by handle', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    expect(wrapper.find('[data-testid="wizard-notification-handle-filter"]').exists()).toBe(true);
    await wrapper.find('[data-testid="wizard-notification-handle-filter"]').setValue('batch');
    await flushPromises();
    expect(creatorMocks.fetchCreatorOnboardingNotifications).toHaveBeenCalled();
  });

  it('exports merge preset packages', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    await wrapper.find('[data-testid="pillars-textarea"]').setValue('# 支柱\n新内容');
    await wrapper.find('[data-testid="save-settings-btn"]').trigger('click');
    await flushPromises();
    await wrapper.find('[data-testid="export-merge-preset-packages-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.exportCreatorMergePresetPackages).toHaveBeenCalled();
  });

  it('shows changelog visual diff', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    await wrapper.find('[data-testid="volume-template-select"]').setValue('custom_test');
    await flushPromises();
    await wrapper.find('[data-testid="template-changelog-visual-btn"]').trigger('click');
    await flushPromises();
    expect(wrapper.find('[data-testid="template-changelog-visual-diff"]').exists()).toBe(true);
  });

  it('shows wizard webhook panel', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    expect(wrapper.find('[data-testid="wizard-webhook-panel"]').exists()).toBe(true);
    await wrapper.find('[data-testid="wizard-webhook-url"]').setValue('https://example.com/hook');
    await wrapper.find('[data-testid="save-wizard-webhook-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.saveCreatorOnboardingWebhook).toHaveBeenCalled();
  });

  it('publishes merge preset to factory', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    await wrapper.find('[data-testid="pillars-textarea"]').setValue('# 支柱\n新内容');
    await wrapper.find('[data-testid="save-settings-btn"]').trigger('click');
    await flushPromises();
    const select = wrapper.find('[data-testid="merge-preset-package-select"]');
    await select.setValue('my_combo');
    await flushPromises();
    const publishBtn = wrapper.find('[data-testid="publish-merge-preset-factory-btn"]');
    expect(publishBtn.element.disabled).toBe(false);
    await publishBtn.trigger('click');
    await flushPromises();
    expect(creatorMocks.publishCreatorMergePresetToFactory).toHaveBeenCalledWith({ package_id: 'my_combo' });
  });

  it('applies merge preset package', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    await wrapper.find('[data-testid="pillars-textarea"]').setValue('# 支柱\n新内容');
    await wrapper.find('[data-testid="save-settings-btn"]').trigger('click');
    await flushPromises();
    const select = wrapper.find('[data-testid="merge-preset-package-select"]');
    await select.setValue('pillars_disk_outline_editor');
    await flushPromises();
    expect(creatorMocks.previewCreatorSettingsMerge).toHaveBeenCalled();
    const matching = creatorMocks.previewCreatorSettingsMerge.mock.calls.find(
      (call) => call[0]?.pillars_merge_source === 'disk' && call[0]?.global_outline_merge_source === 'editor',
    );
    expect(matching).toBeTruthy();
  });

  it('saves wizard step note on blur', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    const note = wrapper.find('[data-testid="wizard-note-volume"]');
    await note.setValue('协作备注');
    await note.trigger('blur');
    await flushPromises();
    expect(creatorMocks.saveCreatorOnboardingNotes).toHaveBeenCalled();
  });

  it('sets template version label', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    await wrapper.find('[data-testid="volume-template-select"]').setValue('custom_test');
    await wrapper.find('[data-testid="template-version-input"]').setValue('v2.0.0');
    await wrapper.find('[data-testid="set-template-version-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.setCreatorVolumeTemplateVersion).toHaveBeenCalledWith('custom_test', {
      version_label: 'v2.0.0',
    });
  });

  it('rolls back template version from changelog', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    await wrapper.find('[data-testid="volume-template-select"]').setValue('custom_test');
    await flushPromises();
    const rollbackBtn = wrapper.find('[data-testid="template-changelog-rollback-btn"]');
    expect(rollbackBtn.exists()).toBe(true);
    await rollbackBtn.trigger('click');
    await flushPromises();
    expect(creatorMocks.rollbackCreatorVolumeTemplate).toHaveBeenCalled();
  });

  it('shows wizard email panel', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    expect(wrapper.find('[data-testid="wizard-email-panel"]').exists()).toBe(true);
    await wrapper.find('[data-testid="wizard-email-to"]').setValue('writer@example.com');
    await wrapper.find('[data-testid="wizard-email-smtp-host"]').setValue('smtp.example.com');
    await wrapper.find('[data-testid="save-wizard-email-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.saveCreatorOnboardingEmail).toHaveBeenCalled();
  });

  it('shows merge preset semver in select', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    await wrapper.find('[data-testid="pillars-textarea"]').setValue('# 支柱\n新内容');
    await wrapper.find('[data-testid="save-settings-btn"]').trigger('click');
    await flushPromises();
    const option = wrapper.find('[data-testid="merge-preset-package-select"] option[value="my_combo"]');
    expect(option.text()).toContain('[v1.0.0]');
  });

  it('shows wizard notification digest', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    expect(wrapper.find('[data-testid="wizard-notification-digest"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="wizard-digest-row"]').exists()).toBe(true);
  });

  it('submits template version approval', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    await wrapper.find('[data-testid="volume-template-select"]').setValue('custom_test');
    await wrapper.find('[data-testid="template-version-input"]').setValue('v2.0.0');
    await wrapper.find('[data-testid="submit-template-version-approval-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.submitCreatorTemplateVersionApproval).toHaveBeenCalled();
  });

  it('shows merge preset dependency graph', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    await wrapper.find('[data-testid="pillars-textarea"]').setValue('# 支柱\n新内容');
    await wrapper.find('[data-testid="save-settings-btn"]').trigger('click');
    await flushPromises();
    expect(wrapper.find('[data-testid="merge-preset-graph-panel"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="merge-preset-graph-edge"]').exists()).toBe(true);
  });

  it('shows wizard digest schedule panel', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    expect(wrapper.find('[data-testid="wizard-digest-schedule-panel"]').exists()).toBe(true);
    await wrapper.find('[data-testid="wizard-digest-schedule-enabled"]').setValue(true);
    await wrapper.find('[data-testid="save-wizard-digest-schedule-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.saveCreatorOnboardingDigestSchedule).toHaveBeenCalled();
    await wrapper.find('[data-testid="dispatch-wizard-digest-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.dispatchCreatorOnboardingDigest).toHaveBeenCalled();
  });

  it('shows template approval chain progress and config', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    expect(wrapper.find('[data-testid="template-approval-chain-config"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="template-approval-chain-progress"]').text()).toBe('1/2');
    await wrapper.find('[data-testid="template-approval-chain-steps"]').setValue(3);
    await wrapper.find('[data-testid="save-template-approval-chain-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.saveCreatorTemplateApprovalChainConfig).toHaveBeenCalled();
  });

  it('shows merge preset conflicts panel', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    await wrapper.find('[data-testid="pillars-textarea"]').setValue('# 支柱\n新内容');
    await wrapper.find('[data-testid="save-settings-btn"]').trigger('click');
    await flushPromises();
    expect(wrapper.find('[data-testid="merge-preset-conflicts-panel"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="merge-preset-conflict-row"]').exists()).toBe(true);
  });

  it('shows template approval history and export audit', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    expect(wrapper.find('[data-testid="template-approval-history-panel"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="template-approval-chain-log"]').exists()).toBe(true);
    await wrapper.find('[data-testid="export-template-approval-audit-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.exportCreatorTemplateApprovalAudit).toHaveBeenCalled();
  });

  it('shows merge preset conflict fix actions', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    await wrapper.find('[data-testid="pillars-textarea"]').setValue('# 支柱\n新内容');
    await wrapper.find('[data-testid="save-settings-btn"]').trigger('click');
    await flushPromises();
    expect(wrapper.find('[data-testid="merge-preset-conflict-fixes-panel"]').exists()).toBe(true);
    await wrapper.find('[data-testid="apply-merge-preset-fix-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.applyCreatorMergePresetConflictFix).toHaveBeenCalled();
  });

  it('shows digest background polling hint', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    expect(wrapper.find('[data-testid="wizard-digest-background-hint"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="wizard-digest-retry-panel"]').exists()).toBe(true);
    await wrapper.find('[data-testid="process-wizard-digest-retry-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.processCreatorOnboardingDigestRetries).toHaveBeenCalled();
  });

  it('shows template approval sla config', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    expect(wrapper.find('[data-testid="template-approval-sla-config"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="template-approval-overdue-panel"]').exists()).toBe(true);
    await wrapper.find('[data-testid="save-template-approval-sla-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.saveCreatorTemplateApprovalSlaConfig).toHaveBeenCalled();
  });

  it('preflights merge preset import and applies all fixes', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    await wrapper.find('[data-testid="pillars-textarea"]').setValue('# 支柱\n新内容');
    await wrapper.find('[data-testid="save-settings-btn"]').trigger('click');
    await flushPromises();
    await wrapper.find('[data-testid="toggle-import-merge-preset-packages-btn"]').trigger('click');
    await flushPromises();
    await wrapper.find('[data-testid="import-merge-preset-packages-json"]').setValue('{"packages":[]}');
    await wrapper.find('[data-testid="preflight-merge-preset-import-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.preflightCreatorMergePresetImport).toHaveBeenCalled();
    await wrapper.find('[data-testid="apply-all-merge-preset-fixes-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.applyAllCreatorMergePresetConflictFixes).toHaveBeenCalled();
  });

  it('shows v3.5 approval assignees digest stats and import diff', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    expect(wrapper.find('[data-testid="template-approval-step-assignees"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="template-approval-email-overdue"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="wizard-digest-stats"]').exists()).toBe(true);
    await wrapper.find('[data-testid="pillars-textarea"]').setValue('# 支柱\n新内容');
    await wrapper.find('[data-testid="save-settings-btn"]').trigger('click');
    await flushPromises();
    await wrapper.find('[data-testid="toggle-import-merge-preset-packages-btn"]').trigger('click');
    await flushPromises();
    await wrapper.find('[data-testid="import-merge-preset-packages-json"]').setValue('{"packages":[]}');
    await wrapper.find('[data-testid="preview-merge-preset-import-diff-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.previewCreatorMergePresetImportDiff).toHaveBeenCalled();
    await wrapper.find('[data-testid="toposort-merge-preset-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.applyCreatorMergePresetToposort).toHaveBeenCalled();
  });

  it('shows v3.6 or-signing dead-letter webhook secret and approval actions', async () => {
    const promptSpy = vi.spyOn(window, 'prompt').mockReturnValue('carol');
    const wrapper = mount(CreatorPage);
    await flushPromises();
    expect(wrapper.find('[data-testid="template-approval-or-groups"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="wizard-webhook-signing-secret"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="wizard-digest-handle-quiet-hours"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="wizard-digest-dead-letter-panel"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="template-approval-or-assignees"]').exists()).toBe(true);
    await wrapper.find('[data-testid="preview-approval-snapshot-diff-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.fetchCreatorTemplateApprovalSnapshotDiff).toHaveBeenCalled();
    await wrapper.find('[data-testid="transfer-template-approval-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.transferCreatorTemplateApproval).toHaveBeenCalled();
    promptSpy.mockRestore();
  });

  it('shows v3.7 drift guard batch approve dead-letter replay and changelog diff', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
    const wrapper = mount(CreatorPage);
    await flushPromises();
    expect(wrapper.find('[data-testid="batch-approve-template-versions-btn"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="replay-wizard-digest-dead-letter-btn"]').exists()).toBe(true);
    await wrapper.find('[data-testid="replay-wizard-digest-dead-letter-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.replayCreatorOnboardingDigestDeadLetter).toHaveBeenCalled();
    await wrapper.find('[data-testid="batch-approve-template-versions-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.batchApproveCreatorTemplateApprovals).toHaveBeenCalled();
    await wrapper.find('[data-testid="pillars-textarea"]').setValue('# 支柱\n新内容');
    await wrapper.find('[data-testid="save-settings-btn"]').trigger('click');
    await flushPromises();
    await wrapper.find('[data-testid="merge-preset-package-select"]').setValue('my_combo');
    await flushPromises();
    await wrapper.find('[data-testid="merge-preset-changelog-diff-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.fetchCreatorMergePresetChangelogDiff).toHaveBeenCalled();
    confirmSpy.mockRestore();
  });

  it('shows v3.8 volume pulse and companion logic check when ui_profile requests', async () => {
    creatorMocks.fetchCreatorOverview.mockResolvedValueOnce({
      ...overviewFixture,
      creation_mode: 'companion',
      ui_profile: {
        creation_mode: 'companion',
        quality_profile: 'creator_relaxed',
        primary_action: 'logic_check',
        show_studio_workflow: false,
        show_digest_ops: false,
        show_factory_presets: false,
        show_template_version_ops: true,
        show_merge_preset_advanced: false,
        simplified_notifications: true,
        volume_pulse_enabled: false,
      },
      volume_pulse: null,
    });
    creatorMocks.runCreatorLogicCheck.mockResolvedValue({
      passed: true,
      p0_count: 0,
      total_issues: 0,
      chapters_checked: 6,
    });
    const wrapper = mount(CreatorPage);
    await flushPromises();
    expect(wrapper.find('[data-testid="volume-pulse-panel"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="template-approval-chain-config"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="wizard-digest-schedule-panel"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="companion-logic-check-panel"]').exists()).toBe(true);
    await wrapper.find('[data-testid="run-companion-logic-check-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.runCreatorLogicCheck).toHaveBeenCalled();
  });

  it('v3.9 collapses wizard for companion and hides warn deviations for advance', async () => {
    navMocks.focusWizard.value = false;
    navMocks.focusWizardStep.value = null;
    creatorMocks.fetchCreatorOnboarding.mockResolvedValueOnce({
      mode_label: '陪伴',
      max_chapter: 12,
      steps: [{ id: 'init', title: '初始化' }],
      completed_step_ids: [],
      auto_completed_step_ids: [],
      step_notes: {},
      unread_mention_count: 0,
      progress_pct: 0,
    });
    creatorMocks.fetchCreatorOnboardingNotifications.mockResolvedValueOnce({
      unread: 0,
      handles: [],
      notifications: [],
    });
    creatorMocks.fetchCreatorOverview.mockResolvedValueOnce({
      ...overviewFixture,
      creation_mode: 'companion',
      deviation_count: 2,
      deviation_total_count: 2,
      ui_profile: {
        creation_mode: 'companion',
        quality_profile: 'creator_relaxed',
        primary_action: 'logic_check',
        show_studio_workflow: false,
        show_digest_ops: false,
        show_factory_presets: false,
        show_template_version_ops: true,
        show_merge_preset_advanced: false,
        simplified_notifications: true,
        volume_pulse_enabled: false,
        wizard_default_collapsed: true,
        wizard_expand_if_incomplete: false,
        chapter_inline_edit: true,
        deviation_min_severity: null,
      },
      volume_pulse: null,
    });
    const wrapper = mount(CreatorPage);
    await flushPromises();
    const wizard = wrapper.find('[data-testid="onboarding-wizard-panel"]');
    expect(wizard.element.open).toBe(false);
    expect(wrapper.find('[data-testid="wizard-webhook-panel"]').exists()).toBe(false);

    creatorMocks.fetchCreatorOverview.mockResolvedValueOnce({
      ...overviewFixture,
      deviations: [{ type: 'x', severity: 'alert', chapter: 8, message: '越界' }],
      deviation_count: 1,
      deviation_total_count: 2,
    });
    await wrapper.find('[data-testid="refresh-btn"]').trigger('click');
    await flushPromises();
    const items = wrapper.findAll('[data-testid="deviation-list"] .deviation-item');
    expect(items.length).toBe(1);
    expect(wrapper.find('[data-testid="deviation-badge"]').text()).toContain('1');
  });

  it('v4.0 companion inline chapter edit and wizard expand when incomplete', async () => {
    navMocks.focusWizard.value = false;
    navMocks.focusWizardStep.value = null;
    creatorMocks.fetchCreatorOnboarding.mockResolvedValueOnce({
      mode_label: '陪伴',
      max_chapter: 12,
      steps: [
        { id: 'init', title: '初始化' },
        { id: 'pillars', title: '支柱' },
      ],
      completed_step_ids: [],
      auto_completed_step_ids: [],
      step_notes: {},
      unread_mention_count: 0,
      progress_pct: 0,
      wizard_panel_dismissed: false,
    });
    creatorMocks.fetchCreatorOnboardingNotifications.mockResolvedValueOnce({
      unread: 0,
      handles: [],
      notifications: [],
    });
    creatorMocks.fetchCreatorOverview.mockResolvedValueOnce({
      ...overviewFixture,
      creation_mode: 'companion',
      ui_profile: {
        creation_mode: 'companion',
        quality_profile: 'creator_relaxed',
        primary_action: 'logic_check',
        show_studio_workflow: false,
        show_digest_ops: false,
        show_factory_presets: false,
        show_template_version_ops: true,
        show_merge_preset_advanced: false,
        simplified_notifications: true,
        volume_pulse_enabled: false,
        wizard_default_collapsed: true,
        wizard_expand_if_incomplete: true,
        chapter_inline_edit: true,
        deviation_min_severity: null,
      },
      volume_pulse: null,
    });
    const wrapper = mount(CreatorPage);
    await flushPromises();
    expect(wrapper.find('[data-testid="onboarding-wizard-panel"]').element.open).toBe(true);

    await wrapper.find('[data-testid="chapter-row-1"]').trigger('click');
    await flushPromises();
    expect(wrapper.find('[data-testid="chapter-inline-edit"]').exists()).toBe(true);
    expect(creatorMocks.fetchCreatorChapterPreview).toHaveBeenCalledWith(1, { full: true });
    await wrapper.find('[data-testid="chapter-body-textarea"]').setValue('新正文');
    await wrapper.find('[data-testid="save-chapter-body-btn"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.saveCreatorChapterBody).toHaveBeenCalledWith(1, '新正文');
  });

  it('v4.1 advance full read preview and pulse jump', async () => {
    creatorMocks.fetchCreatorChapterPreview.mockResolvedValueOnce({
      chapter: 1,
      has_body: true,
      has_outline: true,
      word_count: 2000,
      body_preview: '截断',
      body_text: '推进模式全文正文',
      outline_preview: '大纲',
      body_truncated: false,
      outline_truncated: false,
    });
    const wrapper = mount(CreatorPage);
    await flushPromises();
    await wrapper.find('[data-testid="volume-pulse-row-一"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.fetchCreatorChapterPreview).toHaveBeenCalledWith(1, { full: true });
    expect(wrapper.find('[data-testid="chapter-read-preview"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('推进模式全文正文');
  });

  it('v4.1 companion logic check inline issues jump to chapter', async () => {
    creatorMocks.fetchCreatorOverview.mockResolvedValue({
      ...overviewFixture,
      creation_mode: 'companion',
      ui_profile: {
        creation_mode: 'companion',
        quality_profile: 'creator_relaxed',
        primary_action: 'logic_check',
        show_studio_workflow: false,
        show_digest_ops: false,
        show_factory_presets: false,
        show_template_version_ops: true,
        show_merge_preset_advanced: false,
        simplified_notifications: true,
        volume_pulse_enabled: false,
        wizard_default_collapsed: true,
        wizard_expand_if_incomplete: false,
        chapter_inline_edit: true,
        chapter_full_preview: false,
        logic_check_inline_issues: true,
        deviation_min_severity: null,
      },
      volume_pulse: null,
    });
    creatorMocks.runCreatorLogicCheck.mockReset();
    creatorMocks.runCreatorLogicCheck.mockResolvedValue({
      passed: false,
      p0_count: 1,
      total_issues: 1,
      issues: [{ severity: 'P0', chapter: 2, title: '逻辑矛盾', message: '逻辑矛盾' }],
    });
    const wrapper = mount(CreatorPage);
    await flushPromises();
    await wrapper.find('[data-testid="run-companion-logic-check-btn"]').trigger('click');
    await flushPromises();
    expect(wrapper.find('[data-testid="logic-check-issues"]').exists()).toBe(true);
    await wrapper.find('[data-testid="logic-check-issue-0"]').trigger('click');
    await flushPromises();
    expect(creatorMocks.fetchCreatorChapterPreview).toHaveBeenCalledWith(2, { full: true });
  });
});
