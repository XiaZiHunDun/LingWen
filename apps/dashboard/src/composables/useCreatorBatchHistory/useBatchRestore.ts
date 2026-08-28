/**
 * useBatchRestore — 批次预算/范围/重试/JSON 导出
 *
 * Phase 19 Task 4：从 useCreatorBatchHistory.js 拆出（完整实现）。
 * 负责: applyBatchHistoryBudgetFromJob + applyBatchHistoryRange +
 *       retryBatchHistoryJob + exportBatchHistory + downloadJsonExport +
 *       batchHistoryBudgetHint + highlightedBatchHistoryId 状态。
 */
import { ref } from 'vue';
import type { Ref } from 'vue';
import { exportCreatorBatchHistory } from '@/api/content';
import type { BatchJob } from './useBatchList';

export interface BatchRestoreDeps {
  uiProfile: import('vue').ComputedRef<Record<string, unknown>>;
  saveMessage: Ref<string>;
  error: Ref<string | null>;
  batchStart: Ref<number>;
  batchEnd: Ref<number>;
  batchBudget: Ref<number>;
  filteredBatchHistory: import('vue').ComputedRef<BatchJob[]>;
}

export interface BatchRestoreReturn {
  batchHistoryBudgetHint: Ref<string>;
  highlightedBatchHistoryId: Ref<string>;
  applyBatchHistoryBudgetFromJob: (job: BatchJob | null | undefined) => void;
  applyBatchHistoryRange: (job: BatchJob | null | undefined) => void;
  retryBatchHistoryJob: (job: BatchJob | null | undefined) => void;
  exportBatchHistory: () => Promise<void>;
}

export function useBatchRestore(deps: BatchRestoreDeps): BatchRestoreReturn {
  const { uiProfile, saveMessage, error, batchStart, batchEnd, batchBudget, filteredBatchHistory } = deps;

  const batchHistoryBudgetHint = ref('');
  const highlightedBatchHistoryId = ref('');

  function applyBatchHistoryBudgetFromJob(job: BatchJob | null | undefined): void {
    batchHistoryBudgetHint.value = '';
    if (!(uiProfile.value as { batch_history_budget_hint?: boolean }).batch_history_budget_hint || !job) return;
    if (job.budget_usd == null || Number.isNaN(Number(job.budget_usd))) return;
    batchBudget.value = Number(job.budget_usd);
    batchHistoryBudgetHint.value = `已从历史任务回填预算 $${batchBudget.value}`;
  }

  function applyBatchHistoryRange(job: BatchJob | null | undefined): void {
    if (!(uiProfile.value as { batch_history_replay_range?: boolean }).batch_history_replay_range || !job) return;
    batchStart.value = Number(job.start_chapter) || 1;
    batchEnd.value = Number(job.end_chapter) || batchStart.value;
    highlightedBatchHistoryId.value = job.job_id || '';
    applyBatchHistoryBudgetFromJob(job);
    saveMessage.value = `已填入 batch 范围 ch${String(batchStart.value).padStart(3, '0')}–ch${String(batchEnd.value).padStart(3, '0')}`;
  }

  function retryBatchHistoryJob(job: BatchJob | null | undefined): void {
    if (!(uiProfile.value as { batch_history_failed_retry?: boolean }).batch_history_failed_retry || !job) return;
    if (String(job.status).toLowerCase() !== 'failed') return;
    batchStart.value = Number(job.start_chapter) || 1;
    batchEnd.value = Number(job.end_chapter) || batchStart.value;
    applyBatchHistoryBudgetFromJob(job);
    highlightedBatchHistoryId.value = job.job_id || '';
    saveMessage.value = `已填入失败任务范围 ch${String(batchStart.value).padStart(3, '0')}–ch${String(batchEnd.value).padStart(3, '0')}，可重新运行 batch`;
  }

  function downloadJsonExport(filename: string, payload: unknown): void {
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function exportBatchHistory(): Promise<void> {
    if (!(uiProfile.value as { batch_history_export?: boolean }).batch_history_export) return;
    try {
      const payload = await exportCreatorBatchHistory() as { jobs?: BatchJob[]; schema_version?: string };
      const jobs = payload?.jobs?.length ? payload.jobs : filteredBatchHistory.value;
      downloadJsonExport('creator-batch-history.json', {
        schema_version: payload?.schema_version || '1',
        count: jobs.length,
        jobs,
      });
      saveMessage.value = `已导出 ${jobs.length} 条 batch 历史`;
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    }
  }

  return {
    batchHistoryBudgetHint,
    highlightedBatchHistoryId,
    applyBatchHistoryBudgetFromJob,
    applyBatchHistoryRange,
    retryBatchHistoryJob,
    exportBatchHistory,
  };
}
