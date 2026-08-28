/**
 * useBatchList — 批次历史列表 + 加载 + 分组 + 过滤
 *
 * Phase 19 Task 4：从 useCreatorBatchHistory.js 拆出（完整实现）。
 * 负责: batchHistory state + loadBatchHistory + status filter + 过滤/分组 +
 *       周/月汇总 + 时间 helpers（isoWeek/month/duration）。
 *
 * 注: batchJobDurationMinutes 也被 useBatchDiff 使用（duration distribution），
 *     通过 deps.batchJobDurationMinutes 接收。
 */
import { computed, ref } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import { fetchCreatorBatchHistory } from '@/api/content';

export interface BatchJob {
  job_id?: string;
  status?: string;
  started_at?: string;
  finished_at?: string;
  queued_at?: string;
  created_at?: string;
  start_chapter?: number;
  end_chapter?: number;
  duration_ms?: number;
  failure_reason?: string;
  error?: string;
  budget_usd?: number;
  retry_count?: number;
}

export interface BatchListDeps {
  uiProfile: ComputedRef<Record<string, unknown>>;
  batchHistory: Ref<BatchJob[]>;
  batchJobDurationMinutes: (job: BatchJob) => number | null;
  batchJobIsoWeekKey: (job: BatchJob) => string;
  batchJobMonthKey: (job: BatchJob) => string;
}

export interface BatchListReturn {
  batchHistoryStatusFilter: Ref<string>;
  batchHistoryStatusOptions: ComputedRef<string[]>;
  filteredBatchHistory: ComputedRef<BatchJob[]>;
  batchHistoryDateGroups: ComputedRef<Array<{ date: string; jobs: BatchJob[] }>>;
  batchHistoryWeeklySummary: ComputedRef<Array<{ weekKey: string; weekLabel: string; total: number; completed: number; failed: number }>>;
  batchHistoryMonthlySummary: ComputedRef<Array<{ monthKey: string; monthLabel: string; total: number; completed: number; failed: number }>>;
  batchJobDurationLabel: (job: BatchJob) => string;
  loadBatchHistory: () => Promise<void>;
}

export function useBatchList(deps: BatchListDeps): BatchListReturn {
  const { uiProfile, batchHistory, batchJobDurationMinutes, batchJobIsoWeekKey, batchJobMonthKey } = deps;

  const batchHistoryStatusFilter = ref('');

  async function loadBatchHistory(): Promise<void> {
    if (!(uiProfile.value as { batch_history_panel?: boolean }).batch_history_panel) {
      batchHistory.value = [];
      return;
    }
    try {
      const payload = await fetchCreatorBatchHistory() as { jobs?: BatchJob[] };
      batchHistory.value = payload?.jobs || [];
    } catch {
      batchHistory.value = [];
    }
  }

  const batchHistoryStatusOptions = computed<string[]>(() => {
    const statuses = new Set<string>();
    for (const job of batchHistory.value) {
      if (job?.status) statuses.add(String(job.status));
    }
    return Array.from(statuses).sort();
  });

  const filteredBatchHistory = computed<BatchJob[]>(() => {
    if (!(uiProfile.value as { batch_history_status_filter?: boolean }).batch_history_status_filter || !batchHistoryStatusFilter.value) {
      return batchHistory.value;
    }
    const status = batchHistoryStatusFilter.value;
    return batchHistory.value.filter((job) => String(job.status) === status);
  });

  const batchHistoryDateGroups = computed(() => {
    const jobs = filteredBatchHistory.value;
    if (!(uiProfile.value as { batch_history_date_group?: boolean }).batch_history_date_group) {
      return [{ date: '', jobs }];
    }
    const groups = new Map<string, BatchJob[]>();
    for (const job of jobs) {
      const raw = job.finished_at || job.started_at || '未知日期';
      const date = String(raw).slice(0, 10);
      if (!groups.has(date)) groups.set(date, []);
      groups.get(date)!.push(job);
    }
    return Array.from(groups.entries()).map(([date, groupedJobs]) => ({
      date,
      jobs: groupedJobs,
    }));
  });

  const batchHistoryWeeklySummary = computed(() => {
    if (!(uiProfile.value as { batch_history_weekly_summary?: boolean }).batch_history_weekly_summary || !batchHistory.value.length) return [];
    const groups = new Map<string, { weekKey: string; weekLabel: string; total: number; completed: number; failed: number }>();
    for (const job of batchHistory.value) {
      const weekKey = batchJobIsoWeekKey(job);
      if (!groups.has(weekKey)) {
        groups.set(weekKey, { weekKey, weekLabel: weekKey, total: 0, completed: 0, failed: 0 });
      }
      const row = groups.get(weekKey)!;
      row.total += 1;
      const status = String(job?.status).toLowerCase();
      if (status === 'completed') row.completed += 1;
      if (status === 'failed') row.failed += 1;
    }
    return Array.from(groups.values()).sort((a, b) => b.weekKey.localeCompare(a.weekKey));
  });

  const batchHistoryMonthlySummary = computed(() => {
    if (!(uiProfile.value as { batch_history_monthly_summary?: boolean }).batch_history_monthly_summary || !batchHistory.value.length) return [];
    const groups = new Map<string, { monthKey: string; monthLabel: string; total: number; completed: number; failed: number }>();
    for (const job of batchHistory.value) {
      const monthKey = batchJobMonthKey(job);
      if (!groups.has(monthKey)) {
        groups.set(monthKey, { monthKey, monthLabel: monthKey, total: 0, completed: 0, failed: 1 });
      }
      const row = groups.get(monthKey)!;
      row.total += 1;
      const status = String(job?.status).toLowerCase();
      if (status === 'completed') row.completed += 1;
      if (status === 'failed') row.failed += 1;
    }
    return Array.from(groups.values()).sort((a, b) => b.monthKey.localeCompare(a.monthKey));
  });

  function batchJobDurationLabel(job: BatchJob): string {
    if (!(uiProfile.value as { batch_history_duration?: boolean }).batch_history_duration || !job) return '';
    const minutes = batchJobDurationMinutes(job);
    if (minutes == null) return '';
    if (minutes < 1) return '耗时 <1 分钟';
    return `耗时 ${minutes} 分钟`;
  }

  return {
    batchHistoryStatusFilter,
    batchHistoryStatusOptions,
    filteredBatchHistory,
    batchHistoryDateGroups,
    batchHistoryWeeklySummary,
    batchHistoryMonthlySummary,
    batchJobDurationLabel,
    loadBatchHistory,
  };
}
