// tests/unit/studio-page.spec.ts — Phase 10.04

import { describe, test, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { byTestid } from '../helpers/by-testid';

const studioMocks = vi.hoisted(() => ({
  fetchStudioProjects: vi.fn(),
  fetchStudioSummary: vi.fn(),
  fetchStudioQuality: vi.fn(),
  fetchStudioQualityReport: vi.fn(),
  fetchStudioProseDiff: vi.fn(),
  fetchStudioProseJudge: vi.fn(),
  studioProductionPreflight: vi.fn(),
  studioProductionRun: vi.fn(),
  fetchStudioBatchJob: vi.fn(),
  fetchStudioActiveBatchJob: vi.fn(),
}));

vi.mock('../../src/api/index.js', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...(actual as object),
    fetchStudioProjects: studioMocks.fetchStudioProjects,
    fetchStudioSummary: studioMocks.fetchStudioSummary,
  fetchStudioQuality: studioMocks.fetchStudioQuality,
  fetchStudioQualityReport: studioMocks.fetchStudioQualityReport,
  fetchStudioProseDiff: studioMocks.fetchStudioProseDiff,
  fetchStudioProseJudge: studioMocks.fetchStudioProseJudge,
  studioProductionPreflight: studioMocks.studioProductionPreflight,
    studioProductionRun: studioMocks.studioProductionRun,
    fetchStudioBatchJob: studioMocks.fetchStudioBatchJob,
    fetchStudioActiveBatchJob: studioMocks.fetchStudioActiveBatchJob,
  };
});

import StudioPage from '../../src/pages/StudioPage.vue';

describe('StudioPage (Phase 10.04)', () => {
  beforeEach(() => {
    studioMocks.fetchStudioProjects.mockResolvedValue({
      projects: [{ slug: 'anye-xinbiao', name: '暗夜信标', role: 'production' }],
      active_slug: 'anye-xinbiao',
    });
    studioMocks.fetchStudioSummary.mockResolvedValue({
      name: '暗夜信标',
      role: 'production',
      chapter_count: 10,
      latest_chapter: 10,
      max_chapter: 10,
      root: '/tmp/anye-xinbiao',
    });
    studioMocks.fetchStudioQuality.mockResolvedValue({
      pillars_ok: true,
      pillars_path: '/tmp/pillars.md',
      coverage_pct: 100,
      chapters_written: 10,
      max_chapter: 10,
      outlines_present: 10,
      missing_outlines: [],
      missing_bodies: [],
      golden_set_status: 'ready',
      golden_regression_cmd: './scripts/run-golden-set-check.sh anye-xinbiao',
    });
    studioMocks.fetchStudioQualityReport.mockResolvedValue({
      slug: 'anye-xinbiao',
      available: true,
      path: '/tmp/full-check-report.md',
      total: 5,
      p0: 0,
      p1: 3,
      p2: 1,
      p3: 1,
      generated_at: '2026-06-18',
      prose_heatmap: {
        chapters: [{ chapter: 1, issue_count: 2, prose_p1: 1, prose_total: 1, structural_total: 1, heat: 0.5 }],
        total_prose_p1: 1,
        total_prose_issues: 1,
      },
      chapters: [
        { chapter: 1, word_count: 1800, issue_count: 2, issues: [
          { severity: 'P1', issue_type: 'sentence_diversity_low', chapter: 1, description: 'test' },
        ]},
      ],
    });
    studioMocks.fetchStudioProseDiff.mockResolvedValue({
      slug: 'anye-xinbiao',
      available: true,
      before_captured_at: '2026-06-19',
      after_captured_at: '2026-06-20',
      total_delta: { prose_p1: -1, prose_total: -1, total: -2, p0: 0, p1: 0 },
      chapters: [
        {
          chapter: 1,
          before_prose_p1: 2,
          after_prose_p1: 1,
          delta_prose_p1: -1,
          before_prose_total: 2,
          after_prose_total: 1,
          delta_prose_total: -1,
        },
      ],
      improved_count: 1,
      regressed_count: 0,
      has_regression: false,
      net_prose_p1_delta: -1,
    });
    studioMocks.fetchStudioProseJudge.mockResolvedValue({
      slug: 'anye-xinbiao',
      available: true,
      source: 'offline',
      judged_at: '2026-06-20',
      golden_chapters: [1, 5, 10],
      weighted_avg: 3.83,
      chapters: [
        {
          chapter: 1,
          avg_score: 3.83,
          ratings: [
            { dimension: 'vitality', score: 3, evidence: 'test', action: 'trim' },
          ],
        },
      ],
      high_priority_count: 0,
      false_positive_candidate_count: 1,
      review_needed_count: 0,
      generate_command: 'bash scripts/run-prose-judge.sh anye-xinbiao --llm',
    });
    studioMocks.studioProductionPreflight.mockResolvedValue({
      all_ok: true,
      chapters: [{ chapter: 1, ok: true, message: 'ok' }],
      batch_command: './scripts/run-project-batch.sh 1 1',
    });
    studioMocks.fetchStudioActiveBatchJob.mockResolvedValue(null);
  });

  test('page-title 渲染', async () => {
    const wrapper = mount(StudioPage);
    await flushPromises();
    expect(wrapper.find(byTestid('page-title')).text()).toBe('灵文工作室');
  });

  test('summary 与 quality 面板渲染', async () => {
    const wrapper = mount(StudioPage);
    await flushPromises();
    expect(wrapper.find(byTestid('project-summary')).exists()).toBe(true);
    expect(wrapper.find(byTestid('quality-panel')).exists()).toBe(true);
    expect(wrapper.find(byTestid('quality-report-panel')).exists()).toBe(true);
    expect(wrapper.find(byTestid('prose-diff-panel')).exists()).toBe(true);
    expect(wrapper.find(byTestid('prose-diff-status')).text()).toContain('无 prose 回归');
    expect(wrapper.find(byTestid('prose-judge-panel')).exists()).toBe(true);
    expect(wrapper.find(byTestid('prose-judge-signals')).text()).toContain('误报候选');
  });

  test('无基线时 prose diff 空态', async () => {
    studioMocks.fetchStudioProseDiff.mockResolvedValue({
      slug: 'huangsha-dangan',
      available: false,
      reason: 'no_baseline',
      save_command: 'bash scripts/run-prose-diff.sh huangsha-dangan --save',
    });
    const wrapper = mount(StudioPage);
    await flushPromises();
    const panel = wrapper.find(byTestid('prose-diff-panel'));
    expect(panel.text()).toContain('尚无 prose 基线快照');
    expect(panel.text()).toContain('--save');
  });

  test('preflight 按钮触发 API', async () => {
    const wrapper = mount(StudioPage);
    await flushPromises();
    await wrapper.find('[data-testid="production-console"] form').trigger('submit');
    await flushPromises();
    expect(studioMocks.studioProductionPreflight).toHaveBeenCalled();
    expect(wrapper.find(byTestid('batch-command')).exists()).toBe(true);
  });

  test('后台启动 Batch 按钮', async () => {
    studioMocks.studioProductionRun.mockResolvedValue({
      job_id: 'abc123',
      status: 'running',
      start_chapter: 1,
      end_chapter: 1,
      budget_usd: 0.15,
      log_tail: 'started',
    });
    const wrapper = mount(StudioPage);
    await flushPromises();
    await wrapper.find('[data-testid="production-console"] form').trigger('submit');
    await flushPromises();
    await wrapper.find(byTestid('run-batch-btn')).trigger('click');
    await flushPromises();
    expect(studioMocks.studioProductionRun).toHaveBeenCalled();
  });
});
