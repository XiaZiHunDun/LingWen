// tests/unit/use-creator-batch-history.spec.ts — useCreatorBatchHistory 编排

import { describe, test, expect, vi, beforeEach } from 'vitest';
import { computed, ref } from 'vue';

const batchMocks = vi.hoisted(() => ({
  fetchCreatorBatchHistory: vi.fn(),
  exportCreatorBatchHistory: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorBatchHistory: (...args: unknown[]) => batchMocks.fetchCreatorBatchHistory(...args),
  exportCreatorBatchHistory: (...args: unknown[]) => batchMocks.exportCreatorBatchHistory(...args),
}));

const sampleJobs = [
  {
    job_id: 'j1',
    status: 'completed',
    started_at: '2026-06-01T10:00:00Z',
    finished_at: '2026-06-01T10:03:00Z',
    queued_at: '2026-06-01T09:58:00Z',
    start_chapter: 1,
    end_chapter: 3,
    budget_usd: 0.42,
    chapters_completed: 3,
    total_cost_usd: 0.1,
  },
  {
    job_id: 'j2',
    status: 'failed',
    started_at: '2026-06-02T10:00:00Z',
    finished_at: '2026-06-02T10:12:00Z',
    queued_at: '2026-06-02T09:55:00Z',
    start_chapter: 4,
    end_chapter: 5,
    failure_reason: 'timeout',
    chapters_completed: 0,
    total_cost_usd: 0.05,
  },
  {
    job_id: 'j3',
    status: 'running',
    started_at: '2026-06-03T10:00:00Z',
    start_chapter: 6,
    end_chapter: 8,
    chapters_completed: 1,
  },
];

const allFlagsProfile = {
  batch_history_panel: true,
  batch_history_success_rate: true,
  batch_history_success_rate_chart: true,
  batch_history_status_stack_chart: true,
  batch_history_duration_distribution: true,
  batch_history_concurrency_chart: true,
  batch_history_queue_depth_chart: true,
  batch_history_throughput_chart: true,
  batch_history_cost_efficiency_chart: true,
  batch_history_retry_rate_stack: true,
  batch_history_chapter_failure_heatmap: true,
  batch_history_avg_duration: true,
  batch_history_failure_trend: true,
  batch_history_weekly_summary: true,
  batch_history_monthly_summary: true,
  batch_history_export: true,
  batch_history_duration: true,
  batch_history_failure_reason_label: true,
  batch_history_budget_hint: true,
  batch_history_replay_range: true,
  batch_history_failed_retry: true,
  batch_history_status_color: true,
  batch_history_running_pulse: true,
  batch_history_status_filter: true,
  batch_history_date_group: true,
  batch_history_ops_summary: true,
};

describe('useCreatorBatchHistory', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    batchMocks.fetchCreatorBatchHistory.mockResolvedValue({ jobs: sampleJobs });
    batchMocks.exportCreatorBatchHistory.mockResolvedValue({
      schema_version: '1',
      jobs: sampleJobs,
    });
  });

  async function mountBatchHistory(profileOverrides: Record<string, unknown> = {}) {
    const { useCreatorBatchHistory } = await import('../../src/composables/useCreatorBatchHistory.js');
    const batchStart = ref(1);
    const batchEnd = ref(10);
    const batchBudget = ref(1);
    const saveMessage = ref('');
    const error = ref<string | null>(null);
    const hub = useCreatorBatchHistory({
      uiProfile: computed(() => ({ ...allFlagsProfile, ...profileOverrides })),
      batchStart,
      batchEnd,
      batchBudget,
      saveMessage,
      error,
    });
    return { hub, batchStart, batchEnd, batchBudget, saveMessage, error, panel: hub.panelContext };
  }

  test('loadBatchHistory populates jobs when panel enabled', async () => {
    const { hub, panel } = await mountBatchHistory();
    await hub.loadBatchHistory();
    expect(panel.batchHistory.value).toHaveLength(3);
  });

  test('loadBatchHistory clears jobs when panel disabled', async () => {
    const { hub, panel } = await mountBatchHistory({ batch_history_panel: false });
    await hub.loadBatchHistory();
    expect(panel.batchHistory.value).toEqual([]);
  });

  test('computed charts and summaries render for sample jobs', async () => {
    const { hub, panel } = await mountBatchHistory();
    await hub.loadBatchHistory();
    expect(panel.batchHistorySuccessRate.value?.pct).toBe(33);
    expect(panel.batchHistorySuccessRateChart.value?.polyline).toBeTruthy();
    expect(panel.batchHistoryStatusStackChart.value?.segments.length).toBeGreaterThan(0);
    expect(panel.batchHistoryDurationDistribution.value?.bars.length).toBeGreaterThan(0);
    expect(panel.batchHistoryConcurrencyChart.value?.peak).toBeGreaterThan(0);
    expect(panel.batchHistoryQueueDepthChart.value?.peak).toBeGreaterThan(0);
    expect(panel.batchHistoryThroughputChart.value?.bars.length).toBeGreaterThan(0);
    expect(panel.batchHistoryCostEfficiencyChart.value?.bars.length).toBeGreaterThan(0);
    expect(panel.batchHistoryRetryRateStack.value?.segments.length).toBeGreaterThan(0);
    expect(panel.batchHistoryChapterFailureHeatmap.value?.cells.length).toBeGreaterThan(0);
    expect(panel.batchHistoryAvgDuration.value).toBeTruthy();
    expect(panel.batchHistoryFailureTrend.value).toBeTruthy();
    expect(panel.batchHistoryWeeklySummary.value.length).toBeGreaterThan(0);
    expect(panel.batchHistoryMonthlySummary.value.length).toBeGreaterThan(0);
  });

  test('applyBatchHistoryRange and retryBatchHistoryJob mutate batch inputs', async () => {
    const { hub, panel, batchStart, batchEnd, batchBudget, saveMessage } = await mountBatchHistory();
    await hub.loadBatchHistory();
    panel.applyBatchHistoryRange(sampleJobs[0]);
    expect(batchStart.value).toBe(1);
    expect(batchEnd.value).toBe(3);
    expect(batchBudget.value).toBe(0.42);
    expect(saveMessage.value).toContain('batch 范围');
    panel.retryBatchHistoryJob(sampleJobs[1]);
    expect(batchStart.value).toBe(4);
    expect(panel.batchJobDurationLabel(sampleJobs[1])).toContain('分钟');
    expect(panel.batchHistoryFailureReasonLabel(sampleJobs[1])).toBe('timeout');
    panel.retryBatchHistoryJob(sampleJobs[0]);
    expect(batchStart.value).toBe(4);
  });

  test('filtered history respects status filter and date groups', async () => {
    const { hub, panel } = await mountBatchHistory();
    await hub.loadBatchHistory();
    panel.batchHistoryStatusFilter.value = 'failed';
    expect(panel.filteredBatchHistory.value).toHaveLength(1);
    expect(panel.batchHistoryDateGroups.value.length).toBeGreaterThan(0);
    const runningClasses = panel.batchHistoryStatusClass(sampleJobs[2]) as Record<string, boolean>;
    expect(runningClasses['batch-history-item--running-pulse']).toBe(true);
  });

  test('exportBatchHistory downloads JSON payload', async () => {
    const { hub, panel, saveMessage } = await mountBatchHistory();
    await hub.loadBatchHistory();
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    await panel.exportBatchHistory();
    expect(clickSpy).toHaveBeenCalled();
    expect(saveMessage.value).toContain('导出');
    clickSpy.mockRestore();
  });

  test('toggleBatchHistoryOpsSummary flips open state', async () => {
    const { panel } = await mountBatchHistory();
    expect(panel.batchHistoryOpsSummaryOpen.value).toBe(false);
    panel.toggleBatchHistoryOpsSummary();
    expect(panel.batchHistoryOpsSummaryOpen.value).toBe(true);
  });

  test('loadBatchHistory clears jobs on API failure', async () => {
    batchMocks.fetchCreatorBatchHistory.mockRejectedValueOnce(new Error('down'));
    const { hub, panel } = await mountBatchHistory();
    await hub.loadBatchHistory();
    expect(panel.batchHistory.value).toEqual([]);
  });

  test('exportBatchHistory surfaces API errors', async () => {
    batchMocks.exportCreatorBatchHistory.mockRejectedValueOnce(new Error('export fail'));
    const { hub, panel, error } = await mountBatchHistory();
    await hub.loadBatchHistory();
    await panel.exportBatchHistory();
    expect(error.value).toBe('export fail');
  });

  test('ops summary and duration edge labels', async () => {
    const { hub, panel } = await mountBatchHistory({
      batch_history_ops_summary: true,
    });
    await hub.loadBatchHistory();
    expect(panel.batchHistoryOpsSummaryLine.value).toContain('成功率');
    const shortJob = {
      job_id: 'j-short',
      status: 'completed',
      started_at: '2026-06-04T10:00:00Z',
      finished_at: '2026-06-04T10:00:20Z',
      start_chapter: 9,
      end_chapter: 9,
    };
    expect(panel.batchJobDurationLabel(shortJob)).toBe('耗时 <1 分钟');
    expect(panel.batchHistoryFailureReasonLabel({ status: 'failed', error: 'boom' })).toBe('boom');
  });

  test('charts return null when profile flags disabled', async () => {
    const { hub, panel } = await mountBatchHistory({
      batch_history_success_rate_chart: false,
      batch_history_status_stack_chart: false,
      batch_history_duration_distribution: false,
      batch_history_concurrency_chart: false,
      batch_history_queue_depth_chart: false,
      batch_history_throughput_chart: false,
      batch_history_cost_efficiency_chart: false,
      batch_history_retry_rate_stack: false,
      batch_history_chapter_failure_heatmap: false,
      batch_history_avg_duration: false,
      batch_history_failure_trend: false,
      batch_history_weekly_summary: false,
      batch_history_monthly_summary: false,
    });
    await hub.loadBatchHistory();
    expect(panel.batchHistorySuccessRateChart.value).toBeNull();
    expect(panel.batchHistoryStatusStackChart.value).toBeNull();
    expect(panel.batchHistoryWeeklySummary.value).toEqual([]);
  });
});
