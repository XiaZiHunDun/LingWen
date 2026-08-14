/**
 * useBatchDiff — 批次状态/失败/duration/ops summary
 *
 * Phase 19 Task 4 占位：useCreatorBatchHistory.js 629 行拆为 3 子模块之一。
 * 负责: batchJobStatusClass + batchHistoryFailureReasonLabel +
 *       toggleBatchHistoryOpsSummary + ops summary 计算。
 *
 * 注: 本会话仅建立类型骨架（Task 8 同模式），实际提取在后续会话完成。
 */
import type { Ref } from 'vue';

export interface BatchDiffDeps {
  // 暂未使用（待后续会话填充）
}

export interface BatchDiffReturn {
  batchHistoryOpsSummaryOpen: Ref<boolean>;
  batchHistoryOpsSummary: Ref<unknown>;
  batchJobStatusClass: (job: Record<string, unknown>) => string;
  batchHistoryFailureReasonLabel: (job: Record<string, unknown>) => string;
  toggleBatchHistoryOpsSummary: () => void;
}

// 占位实现 — 后续会话填充实际逻辑
export function useBatchDiff(_deps: BatchDiffDeps): BatchDiffReturn {
  throw new Error('useBatchDiff: not yet implemented (Phase 19 Task 4.2)');
}