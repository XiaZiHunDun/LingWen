// tests/unit/creator-page.spec.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';

const creatorMocks = vi.hoisted(() => ({
  fetchCreatorOverview: vi.fn(),
  fetchCreatorVolumePlan: vi.fn(),
  saveCreatorVolumePlan: vi.fn(),
  mergeCreatorVolumePlan: vi.fn(),
  fetchCreatorChapterPreview: vi.fn(),
  fetchCreatorSettingsDocs: vi.fn(),
  saveCreatorSettingsDocs: vi.fn(),
  previewCreatorSettingsDocs: vi.fn(),
  studioProductionPreflight: vi.fn(),
  studioProductionRun: vi.fn(),
  fetchStudioActiveBatchJob: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorOverview: creatorMocks.fetchCreatorOverview,
  fetchCreatorVolumePlan: creatorMocks.fetchCreatorVolumePlan,
  saveCreatorVolumePlan: creatorMocks.saveCreatorVolumePlan,
  mergeCreatorVolumePlan: creatorMocks.mergeCreatorVolumePlan,
  fetchCreatorChapterPreview: creatorMocks.fetchCreatorChapterPreview,
  fetchCreatorSettingsDocs: creatorMocks.fetchCreatorSettingsDocs,
  saveCreatorSettingsDocs: creatorMocks.saveCreatorSettingsDocs,
  previewCreatorSettingsDocs: creatorMocks.previewCreatorSettingsDocs,
  studioProductionPreflight: creatorMocks.studioProductionPreflight,
  studioProductionRun: creatorMocks.studioProductionRun,
  fetchStudioActiveBatchJob: creatorMocks.fetchStudioActiveBatchJob,
}));

vi.mock('../../src/composables/useStudioProject.js', () => ({
  useStudioProject: () => ({
    projectRevision: { value: 0 },
  }),
}));

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
    creatorMocks.saveCreatorSettingsDocs.mockResolvedValue({});
    creatorMocks.previewCreatorSettingsDocs.mockResolvedValue({
      has_changes: true,
      pillars: { changed: true, lines_added: 1, lines_removed: 0, snippet: ['+新行'] },
      global_outline: { changed: false, lines_added: 0, lines_removed: 0, snippet: [] },
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

    expect(creatorMocks.previewCreatorSettingsDocs).toHaveBeenCalled();
    expect(wrapper.find('[data-testid="settings-diff-panel"]').exists()).toBe(true);

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
});
