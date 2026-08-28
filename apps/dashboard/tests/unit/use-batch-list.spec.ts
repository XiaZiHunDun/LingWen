/**
 * useBatchList 子模块独立测试
 *
 * Phase 40: 为 Phase 19.4 useBatchList 子模块添加专门测试。
 * 重点测试：批次列表 + 过滤 + 分组 + 周月汇总。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref, computed, ComputedRef } from 'vue';

const batchMocks = vi.hoisted(() => ({
  fetchCreatorBatchHistory: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorBatchHistory: (...args: unknown[]) => batchMocks.fetchCreatorBatchHistory(...args),
}));

// v16.2.7 T6a: also mock the typed wrapper module. Per v16.2.5 §5.1 lesson 3.
vi.mock('../../src/api/content', () => ({
  fetchCreatorBatchHistory: (...args: unknown[]) => batchMocks.fetchCreatorBatchHistory(...args),
}));

import { useBatchList } from '../../src/composables/useCreatorBatchHistory/useBatchList';

function mountBatchList(uiProfileOverrides: Record<string, unknown> = {}) {
  const uiProfile = ref<Record<string, unknown>>({
    batch_history_panel: true,
    ...uiProfileOverrides,
  });
  const batchHistory = ref<Array<Record<string, unknown>>>([]);
  const batchJobDurationMinutes = vi.fn((job: Record<string, unknown>) => {
    if (!job.started_at || !job.finished_at) return null;
    return Math.round((new Date(job.finished_at as string).getTime() - new Date(job.started_at as string).getTime()) / 60000);
  });
  const batchJobIsoWeekKey = vi.fn((job: Record<string, unknown>) => {
    const ts = job.finished_at || job.started_at;
    return ts ? `2026-W10` : '未知周';
  });
  const batchJobMonthKey = vi.fn((job: Record<string, unknown>) => {
    const ts = job.finished_at || job.started_at;
    return ts ? `2026-06` : '未知月';
  });

  const ctx = useBatchList({
    uiProfile: uiProfile as unknown as ComputedRef<Record<string, unknown>>,
    batchHistory, batchJobDurationMinutes, batchJobIsoWeekKey, batchJobMonthKey,
    } as unknown as Parameters<typeof useBatchList>[0]);
  return { ...ctx, uiProfile, batchHistory };
}

describe('useBatchList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    batchMocks.fetchCreatorBatchHistory.mockResolvedValue({ jobs: [] });
  });

  it('initial state has empty filter and options', () => {
    const b = mountBatchList();
    expect(b.batchHistoryStatusFilter.value).toBe('');
    expect(b.batchHistoryStatusOptions.value).toEqual([]);
    expect(b.filteredBatchHistory.value).toEqual([]);
  });

  it('loadBatchHistory populates list from API', async () => {
    batchMocks.fetchCreatorBatchHistory.mockResolvedValueOnce({
      jobs: [
        { id: 'job-1', status: 'completed', started_at: '2026-06-01T00:00:00Z', finished_at: '2026-06-01T00:30:00Z' },
      ],
    });
    const b = mountBatchList();
    await b.loadBatchHistory();
    expect(b.batchHistory.value).toHaveLength(1);
  });

  it('loadBatchHistory no-op when panel disabled', async () => {
    batchMocks.fetchCreatorBatchHistory.mockClear();
    const b = mountBatchList({ batch_history_panel: false });
    await b.loadBatchHistory();
    expect(batchMocks.fetchCreatorBatchHistory).not.toHaveBeenCalled();
    expect(b.batchHistory.value).toEqual([]);
  });

  it('loadBatchHistory clears on failure', async () => {
    batchMocks.fetchCreatorBatchHistory.mockRejectedValueOnce(new Error('down'));
    const b = mountBatchList();
    b.batchHistory.value = [{ id: 'old' }];
    await b.loadBatchHistory();
    expect(b.batchHistory.value).toEqual([]);
  });

  it('batchHistoryStatusOptions exposes unique statuses', async () => {
    batchMocks.fetchCreatorBatchHistory.mockResolvedValueOnce({
      jobs: [
        { id: '1', status: 'completed' },
        { id: '2', status: 'failed' },
        { id: '3', status: 'completed' },
      ],
    });
    const b = mountBatchList();
    await b.loadBatchHistory();
    expect(b.batchHistoryStatusOptions.value.sort()).toEqual(['completed', 'failed']);
  });

  it('filteredBatchHistory filters by status', async () => {
    batchMocks.fetchCreatorBatchHistory.mockResolvedValueOnce({
      jobs: [
        { job_id: '1', status: 'completed' },
        { job_id: '2', status: 'failed' },
      ],
    });
    const b = mountBatchList({ batch_history_status_filter: true });
    await b.loadBatchHistory();
    b.batchHistoryStatusFilter.value = 'failed';
    expect(b.filteredBatchHistory.value).toHaveLength(1);
    expect(b.filteredBatchHistory.value[0].job_id).toBe('2');
  });

  it('filteredBatchHistory returns all when filter empty', async () => {
    batchMocks.fetchCreatorBatchHistory.mockResolvedValueOnce({
      jobs: [{ id: '1', status: 'completed' }, { id: '2', status: 'failed' }],
    });
    const b = mountBatchList();
    await b.loadBatchHistory();
    expect(b.filteredBatchHistory.value).toHaveLength(2);
  });

  it('batchHistoryDateGroups groups jobs by date when enabled', async () => {
    batchMocks.fetchCreatorBatchHistory.mockResolvedValueOnce({
      jobs: [
        { id: '1', status: 'completed', finished_at: '2026-06-01T10:00:00Z' },
        { id: '2', status: 'failed', finished_at: '2026-06-02T10:00:00Z' },
      ],
    });
    const b = mountBatchList({ batch_history_date_group: true });
    await b.loadBatchHistory();
    const groups = b.batchHistoryDateGroups.value;
    expect(groups.length).toBeGreaterThan(0);
  });

  it('batchJobDurationLabel returns formatted text', () => {
    const b = mountBatchList({ batch_history_duration: true });
    const job = {
      started_at: '2026-06-01T00:00:00Z',
      finished_at: '2026-06-01T00:05:00Z',
    };
    const label = b.batchJobDurationLabel(job);
    expect(label).toContain('耗时');
  });

  it('batchJobDurationLabel returns empty when duration null', () => {
    const b = mountBatchList({ batch_history_duration: true });
    expect(b.batchJobDurationLabel({})).toBe('');
  });

  it('batchHistoryWeeklySummary aggregates jobs by week', async () => {
    batchMocks.fetchCreatorBatchHistory.mockResolvedValueOnce({
      jobs: [
        { id: '1', status: 'completed' },
        { id: '2', status: 'failed' },
      ],
    });
    const b = mountBatchList({ batch_history_weekly_summary: true });
    await b.loadBatchHistory();
    expect(b.batchHistoryWeeklySummary.value.length).toBeGreaterThan(0);
  });

  it('batchHistoryMonthlySummary aggregates by month', async () => {
    batchMocks.fetchCreatorBatchHistory.mockResolvedValueOnce({
      jobs: [{ id: '1', status: 'completed' }],
    });
    const b = mountBatchList({ batch_history_monthly_summary: true });
    await b.loadBatchHistory();
    expect(b.batchHistoryMonthlySummary.value.length).toBeGreaterThan(0);
  });
});
