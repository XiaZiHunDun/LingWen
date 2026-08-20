/**
 * useCreatorBatchHistory — Batch 历史面板逻辑（从 CreatorPage 抽出）
 *
 * Phase 19 Task 4 完成版：抽出全部 3 个 .ts 子模块，本主 hook 改为组合 facade。
 * 下游 API（panelContext shape）保持完全兼容。
 *
 * 子模块：
 * - useBatchList    (批次历史列表 + 加载 + 过滤/分组 + 周月汇总)
 * - useBatchDiff    (状态/diff/图表统计 + ops summary)
 * - useBatchRestore (批次预算/范围/重试/JSON 导出)
 *
 * 共享状态（主 hook 编排）：
 * - batchHistory: 主 hook 拥有，list + diff 读取
 * - batchJobDurationMinutes/IsoWeekKey/MonthKey: 主 hook helper（被 list 和 diff 调用）
 */
import { computed, ref } from 'vue';
import {
  useBatchList,
  useBatchDiff,
  useBatchRestore,
} from './useCreatorBatchHistory/index.ts';

/**
 * @param {{
 *   uiProfile: import('vue').ComputedRef<object>,
 *   batchStart: import('vue').Ref<number>,
 *   batchEnd: import('vue').Ref<number>,
 *   batchBudget: import('vue').Ref<number>,
 *   saveMessage: import('vue').Ref<string>,
 *   error: import('vue').Ref<string|null>,
 * }} deps
 */
export function useCreatorBatchHistory(deps) {
  const { uiProfile, batchStart, batchEnd, batchBudget, saveMessage, error } = deps;

  // --- 共享 ref: batchHistory（list + diff 共用）---
  const batchHistory = ref([]);

  // --- 共享 helpers: 时间/duration 解析 ---
  function batchJobDurationMinutes(job) {
    const start = job?.started_at ? Date.parse(job.started_at) : Number.NaN;
    const end = job?.finished_at ? Date.parse(job.finished_at) : Number.NaN;
    if (!Number.isFinite(start) || !Number.isFinite(end) || end < start) return null;
    return Math.round((end - start) / 60000);
  }

  function batchJobIsoWeekKey(job) {
    const raw = job?.finished_at || job?.started_at;
    if (!raw) return '未知周';
    const date = new Date(`${String(raw).slice(0, 10)}T00:00:00Z`);
    if (Number.isNaN(date.getTime())) return '未知周';
    const day = (date.getUTCDay() + 6) % 7;
    date.setUTCDate(date.getUTCDate() - day + 3);
    const week1 = new Date(Date.UTC(date.getUTCFullYear(), 0, 4));
    const weekNum = 1 + Math.round(
      ((date.getTime() - week1.getTime()) / 86400000 - 3 + ((week1.getUTCDay() + 6) % 7)) / 7,
    );
    return `${date.getUTCFullYear()}-W${String(weekNum).padStart(2, '0')}`;
  }

  function batchJobMonthKey(job) {
    const raw = job?.finished_at || job?.started_at;
    if (!raw) return '未知月';
    const monthKey = String(raw).slice(0, 7);
    return /^\d{4}-\d{2}$/.test(monthKey) ? monthKey : '未知月';
  }

  // --- 1) List 子模块（依赖 batchHistory + 时间 helpers）---
  const list = useBatchList({
    uiProfile,
    batchHistory,
    batchJobDurationMinutes,
    batchJobIsoWeekKey,
    batchJobMonthKey,
  });

  // --- 2) Diff 子模块（依赖 batchHistory + durationMinutes）---
  const diff = useBatchDiff({
    uiProfile,
    batchHistory,
    batchJobDurationMinutes,
  });

  // --- 3) Restore 子模块（依赖 filteredBatchHistory）---
  const restore = useBatchRestore({
    uiProfile,
    saveMessage,
    error,
    batchStart,
    batchEnd,
    batchBudget,
    filteredBatchHistory: list.filteredBatchHistory,
  });

  // --- panelContext 聚合（保持原 shape）---
  const panelContext = {
    uiProfile,
    batchHistory,
    batchHistoryBudgetHint: restore.batchHistoryBudgetHint,
    batchHistoryOpsSummaryOpen: diff.batchHistoryOpsSummaryOpen,
    toggleBatchHistoryOpsSummary: diff.toggleBatchHistoryOpsSummary,
    batchHistoryOpsSummaryLine: diff.batchHistoryOpsSummaryLine,
    batchHistorySuccessRate: diff.batchHistorySuccessRate,
    batchHistorySuccessRateChart: diff.batchHistorySuccessRateChart,
    batchHistoryStatusStackChart: diff.batchHistoryStatusStackChart,
    batchHistoryDurationDistribution: diff.batchHistoryDurationDistribution,
    batchHistoryConcurrencyChart: diff.batchHistoryConcurrencyChart,
    batchHistoryQueueDepthChart: diff.batchHistoryQueueDepthChart,
    batchHistoryThroughputChart: diff.batchHistoryThroughputChart,
    batchHistoryCostEfficiencyChart: diff.batchHistoryCostEfficiencyChart,
    batchHistoryRetryRateStack: diff.batchHistoryRetryRateStack,
    batchHistoryChapterFailureHeatmap: diff.batchHistoryChapterFailureHeatmap,
    batchHistoryAvgDuration: diff.batchHistoryAvgDuration,
    batchHistoryFailureTrend: diff.batchHistoryFailureTrend,
    batchHistoryWeeklySummary: list.batchHistoryWeeklySummary,
    batchHistoryMonthlySummary: list.batchHistoryMonthlySummary,
    exportBatchHistory: restore.exportBatchHistory,
    batchHistoryStatusFilter: list.batchHistoryStatusFilter,
    batchHistoryStatusOptions: list.batchHistoryStatusOptions,
    filteredBatchHistory: list.filteredBatchHistory,
    batchHistoryDateGroups: list.batchHistoryDateGroups,
    highlightedBatchHistoryId: restore.highlightedBatchHistoryId,
    batchHistoryStatusClass: diff.batchHistoryStatusClass,
    applyBatchHistoryRange: restore.applyBatchHistoryRange,
    batchJobDurationLabel: list.batchJobDurationLabel,
    batchHistoryFailureReasonLabel: diff.batchHistoryFailureReasonLabel,
    retryBatchHistoryJob: restore.retryBatchHistoryJob,
  };

  return {
    panelContext,
    batchHistoryBudgetHint: restore.batchHistoryBudgetHint,
    loadBatchHistory: list.loadBatchHistory,
  };
}
