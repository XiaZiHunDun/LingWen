/**
 * useBatchRestore — 批次预算/范围/重试/JSON 导出
 *
 * Phase 19 Task 4 占位：useCreatorBatchHistory.js 629 行拆为 3 子模块之一。
 * 负责: applyBatchHistoryBudgetFromJob + applyBatchHistoryRange +
 *       retryBatchHistoryJob + exportBatchHistory + downloadJsonExport。
 *
 * 注: 本会话仅建立类型骨架（Task 8 同模式），实际提取在后续会话完成。
 */
export interface BatchRestoreDeps {
  // 暂未使用（待后续会话填充）
}

export interface BatchRestoreReturn {
  applyBatchHistoryBudgetFromJob: (job: Record<string, unknown>) => void;
  applyBatchHistoryRange: (job: Record<string, unknown>) => void;
  retryBatchHistoryJob: (job: Record<string, unknown>) => Promise<void>;
  exportBatchHistory: () => Promise<void>;
  downloadJsonExport: (filename: string, payload: unknown) => void;
}

// 占位实现 — 后续会话填充实际逻辑
export function useBatchRestore(_deps: BatchRestoreDeps): BatchRestoreReturn {
  throw new Error('useBatchRestore: not yet implemented (Phase 19 Task 4.3)');
}