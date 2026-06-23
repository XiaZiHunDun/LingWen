// tests/unit/creator-page.spec.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';

const creatorMocks = vi.hoisted(() => ({
  fetchCreatorOverview: vi.fn(),
  fetchCreatorVolumePlan: vi.fn(),
  saveCreatorVolumePlan: vi.fn(),
  mergeCreatorVolumePlan: vi.fn(),
  splitCreatorVolumePlan: vi.fn(),
  fetchCreatorVolumeTemplates: vi.fn(),
  applyCreatorVolumeTemplate: vi.fn(),
  saveCreatorVolumeTemplate: vi.fn(),
  deleteCreatorVolumeTemplate: vi.fn(),
  fetchCreatorOnboarding: vi.fn(),
  fetchCreatorChapterPreview: vi.fn(),
  fetchCreatorSettingsDocs: vi.fn(),
  saveCreatorSettingsDocs: vi.fn(),
  previewCreatorSettingsDocs: vi.fn(),
  previewCreatorSettingsThreeWay: vi.fn(),
  previewCreatorSettingsMerge: vi.fn(),
  fetchCreatorSettingsHistory: vi.fn(),
  restoreCreatorSettingsSnapshot: vi.fn(),
  studioProductionPreflight: vi.fn(),
  studioProductionRun: vi.fn(),
  fetchStudioActiveBatchJob: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorOverview: creatorMocks.fetchCreatorOverview,
  fetchCreatorVolumePlan: creatorMocks.fetchCreatorVolumePlan,
  saveCreatorVolumePlan: creatorMocks.saveCreatorVolumePlan,
  mergeCreatorVolumePlan: creatorMocks.mergeCreatorVolumePlan,
  splitCreatorVolumePlan: creatorMocks.splitCreatorVolumePlan,
  fetchCreatorVolumeTemplates: creatorMocks.fetchCreatorVolumeTemplates,
  applyCreatorVolumeTemplate: creatorMocks.applyCreatorVolumeTemplate,
  saveCreatorVolumeTemplate: creatorMocks.saveCreatorVolumeTemplate,
  deleteCreatorVolumeTemplate: creatorMocks.deleteCreatorVolumeTemplate,
  fetchCreatorOnboarding: creatorMocks.fetchCreatorOnboarding,
  fetchCreatorChapterPreview: creatorMocks.fetchCreatorChapterPreview,
  fetchCreatorSettingsDocs: creatorMocks.fetchCreatorSettingsDocs,
  saveCreatorSettingsDocs: creatorMocks.saveCreatorSettingsDocs,
  previewCreatorSettingsDocs: creatorMocks.previewCreatorSettingsDocs,
  previewCreatorSettingsThreeWay: creatorMocks.previewCreatorSettingsThreeWay,
  previewCreatorSettingsMerge: creatorMocks.previewCreatorSettingsMerge,
  fetchCreatorSettingsHistory: creatorMocks.fetchCreatorSettingsHistory,
  restoreCreatorSettingsSnapshot: creatorMocks.restoreCreatorSettingsSnapshot,
  studioProductionPreflight: creatorMocks.studioProductionPreflight,
  studioProductionRun: creatorMocks.studioProductionRun,
  fetchStudioActiveBatchJob: creatorMocks.fetchStudioActiveBatchJob,
}));

vi.mock('../../src/composables/useStudioProject.js', () => ({
  useStudioProject: () => ({
    projectRevision: { value: 0 },
  }),
}));

const navMocks = vi.hoisted(() => ({
  focusWizard: null,
  setWizardDeepLink: vi.fn(),
}));

vi.mock('../../src/composables/useDashboardNav.js', async () => {
  const { ref } = await import('vue');
  const focusWizard = ref(false);
  navMocks.focusWizard = focusWizard;
  navMocks.setWizardDeepLink.mockImplementation((open) => {
    focusWizard.value = Boolean(open);
  });
  return {
    useDashboardNav: () => ({
      focusWizard,
      setWizardDeepLink: navMocks.setWizardDeepLink,
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
  deviation_count: 2,
  alert_count: 1,
  deviations: [
    { type: 'missing_body', severity: 'warn', chapter: 2, volume_label: '一', message: '缺正文' },
    { type: 'outside_locked_plan', severity: 'alert', chapter: 8, volume_label: null, message: '越界' },
  ],
};

describe('CreatorPage', () => {
  beforeEach(() => {
    navMocks.focusWizard.value = false;
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
        { id: 'three_act', name: '三幕式', description: '建置对抗结局', builtin: true },
        { id: 'custom_test', name: '我的结构', description: '自定义', builtin: false },
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

    expect(creatorMocks.fetchCreatorChapterPreview).toHaveBeenCalledWith(1);
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
});
