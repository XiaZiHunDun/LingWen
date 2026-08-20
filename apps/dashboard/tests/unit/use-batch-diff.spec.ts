/**
 * useBatchDiff 子模块独立测试
 *
 * Phase 40: 为 Phase 19.4 useBatchDiff 子模块添加专门测试。
 * 重点测试：状态分类 + 图表数据 + 失败原因标签 + ops summary。
 */
import { describe, it, expect } from 'vitest';
import { ref, computed, ComputedRef } from 'vue';

import { useBatchDiff } from '../../src/composables/useCreatorBatchHistory/useBatchDiff';

function mountBatchDiff() {
  const uiProfile = ref<Record<string, unknown>>({});
  const batchHistory = ref<Array<Record<string, unknown>>>([]);
  const batchJobDurationMinutes = vi.fn((job: Record<string, unknown>) => {
    if (!job.started_at || !job.finished_at) return null;
    return Math.round((new Date(job.finished_at as string).getTime() - new Date(job.started_at as string).getTime()) / 60000);
  });

  const ctx = useBatchDiff({
    uiProfile: uiProfile as unknown as ComputedRef<Record<string, unknown>>,
    batchHistory, batchJobDurationMinutes: batchJobDurationMinutes as unknown as (job: { started_at?: string; finished_at?: string }) => number | null,
  });
  return { ...ctx, uiProfile, batchHistory };
}

describe('useBatchDiff', () => {
  it('initial state has closed ops summary', () => {
    const d = mountBatchDiff();
    expect(d.batchHistoryOpsSummaryOpen.value).toBe(false);
  });

  it('batchHistorySuccessRate returns null when panel disabled', () => {
    const d = mountBatchDiff();
    expect(d.batchHistorySuccessRate.value).toBeNull();
  });

  it('batchHistorySuccessRate returns null when no jobs', () => {
    const d = mountBatchDiff();
    d.uiProfile.value = { batch_history_success_rate: true };
    expect(d.batchHistorySuccessRate.value).toBeNull();
  });

  it('batchHistorySuccessRate computes completed percentage', () => {
    const d = mountBatchDiff();
    d.uiProfile.value = { batch_history_success_rate: true };
    d.batchHistory.value = [
      { id: '1', status: 'completed' },
      { id: '2', status: 'completed' },
      { id: '3', status: 'failed' },
      { id: '4', status: 'running' },
    ];
    const rate = d.batchHistorySuccessRate.value;
    expect(rate).not.toBeNull();
    expect(rate?.total).toBe(4);
    expect(rate?.completed).toBe(2);
    expect(rate?.pct).toBe(50);
  });

  it('batchHistorySuccessRateChart returns null when disabled', () => {
    const d = mountBatchDiff();
    expect(d.batchHistorySuccessRateChart.value).toBeNull();
  });

  it('batchHistorySuccessRateChart returns null when < 2 jobs', () => {
    const d = mountBatchDiff();
    d.uiProfile.value = { batch_history_success_rate_chart: true };
    d.batchHistory.value = [{ id: '1', status: 'completed' }];
    expect(d.batchHistorySuccessRateChart.value).toBeNull();
  });

  it('batchHistorySuccessRateChart returns polyline when >= 2 jobs', () => {
    const d = mountBatchDiff();
    d.uiProfile.value = { batch_history_success_rate_chart: true };
    d.batchHistory.value = [
      { id: '1', status: 'completed', finished_at: '2026-06-01T10:00:00Z' },
      { id: '2', status: 'completed', finished_at: '2026-06-02T10:00:00Z' },
      { id: '3', status: 'failed', finished_at: '2026-06-03T10:00:00Z' },
    ];
    const chart = d.batchHistorySuccessRateChart.value;
    expect(chart).not.toBeNull();
    expect(chart?.polyline).toBeTruthy();
  });

  it('batchHistoryStatusStackChart returns null when disabled', () => {
    const d = mountBatchDiff();
    expect(d.batchHistoryStatusStackChart.value).toBeNull();
  });

  it('batchHistoryStatusStackChart returns segments when enabled', () => {
    const d = mountBatchDiff();
    d.uiProfile.value = { batch_history_status_stack_chart: true };
    d.batchHistory.value = [
      { id: '1', status: 'completed' },
      { id: '2', status: 'failed' },
    ];
    const chart = d.batchHistoryStatusStackChart.value;
    expect(chart).not.toBeNull();
    expect(chart?.segments.length).toBeGreaterThan(0);
  });

  it('batchHistoryDurationDistribution returns null when disabled', () => {
    const d = mountBatchDiff();
    expect(d.batchHistoryDurationDistribution.value).toBeNull();
  });

  it('batchHistoryDurationDistribution returns null when no jobs', () => {
    const d = mountBatchDiff();
    d.uiProfile.value = { batch_history_duration_distribution: true };
    expect(d.batchHistoryDurationDistribution.value).toBeNull();
  });

  it('batchHistoryConcurrencyChart returns null when disabled', () => {
    const d = mountBatchDiff();
    expect(d.batchHistoryConcurrencyChart.value).toBeNull();
  });

  it('batchHistoryFailureReasonLabel returns empty for non-failed job', () => {
    const d = mountBatchDiff();
    d.uiProfile.value = { batch_history_failure_reason_label: true };
    expect(d.batchHistoryFailureReasonLabel({ status: 'completed' })).toBe('');
  });

  it('batchHistoryFailureReasonLabel returns reason for failed job', () => {
    const d = mountBatchDiff();
    d.uiProfile.value = { batch_history_failure_reason_label: true };
    const label = d.batchHistoryFailureReasonLabel({ status: 'failed', failure_reason: 'timeout' });
    expect(label).toBe('timeout');
  });

  it('batchHistoryOpsSummaryLine returns empty when disabled', () => {
    const d = mountBatchDiff();
    expect(d.batchHistoryOpsSummaryLine.value).toBe('');
  });

  it('toggleBatchHistoryOpsSummary flips state', () => {
    const d = mountBatchDiff();
    d.toggleBatchHistoryOpsSummary();
    expect(d.batchHistoryOpsSummaryOpen.value).toBe(true);
    d.toggleBatchHistoryOpsSummary();
    expect(d.batchHistoryOpsSummaryOpen.value).toBe(false);
  });
});
