/**
 * useBatchList — 批次历史列表 + 加载/分组/过滤
 *
 * Phase 19 Task 4 占位：useCreatorBatchHistory.js 629 行拆为 3 子模块之一。
 * 负责: batchHistory 列表 + loadBatchHistory + isoWeekKey/monthKey 分组 +
 *       durationMinutes/durationLabel 派生 + 过滤与排序。
 *
 * 注: 本会话仅建立类型骨架（Task 8 同模式），实际提取在后续会话完成。
 */
import type { ComputedRef, Ref } from 'vue';

export interface BatchJob {
  id: string;
  created_at?: string;
  finished_at?: string;
  status?: 'running' | 'success' | 'failed' | 'cancelled';
  duration_ms?: number;
  failure_reason?: string;
  budget_consumed?: Record<string, number>;
}

export interface BatchListDeps {
  // 暂未使用（待后续会话填充）
}

export interface BatchListReturn {
  batchHistory: Ref<BatchJob[]>;
  batchHistoryLoading: Ref<boolean>;
  batchHistoryLoadedOnce: Ref<boolean>;
  batchHistoryFilter: Ref<string>;
  batchHistoryWeekBuckets: ComputedRef<Array<{ key: string; jobs: BatchJob[] }>>;
  loadBatchHistory: () => Promise<void>;
  batchJobIsoWeekKey: (job: BatchJob) => string;
  batchJobMonthKey: (job: BatchJob) => string;
  batchJobDurationMinutes: (job: BatchJob) => number;
  batchJobDurationLabel: (job: BatchJob) => string;
}

// 占位实现 — 后续会话填充实际逻辑
export function useBatchList(_deps: BatchListDeps): BatchListReturn {
  throw new Error('useBatchList: not yet implemented (Phase 19 Task 4.1)');
}