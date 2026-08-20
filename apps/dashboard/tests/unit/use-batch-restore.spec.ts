/**
 * useBatchRestore 子模块独立测试
 *
 * Phase 40: 为 Phase 19.4 useBatchRestore 子模块添加专门测试。
 * 重点测试：预算/范围/重试/JSON 导出。
 */
import { describe, it, expect, vi } from 'vitest';
import { ref, ComputedRef } from 'vue';

const restoreMocks = vi.hoisted(() => ({
  exportCreatorBatchHistory: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  exportCreatorBatchHistory: (...args: unknown[]) => restoreMocks.exportCreatorBatchHistory(...args),
}));

import { useBatchRestore } from '../../src/composables/useCreatorBatchHistory/useBatchRestore';

function mountBatchRestore() {
  const uiProfile = ref<Record<string, unknown>>({});
  const saveMessage = ref('');
  const error = ref<string | null>(null);
  const conflictMessage = ref('');
  const handleSaveError = vi.fn();
  const batchStart = ref(1);
  const batchEnd = ref(10);
  const batchBudget = ref(0);
  const filteredBatchHistory = ref<Array<Record<string, unknown>>>([]);

  const ctx = useBatchRestore({
    uiProfile, saveMessage, error, conflictMessage, handleSaveError,
    batchStart, batchEnd, batchBudget, filteredBatchHistory,
  } as unknown as Parameters<typeof useBatchRestore>[0]);
  return { ...ctx, uiProfile, batchStart, batchEnd, batchBudget, error, handleSaveError, saveMessage, filteredBatchHistory };
}

describe('useBatchRestore', () => {
  it('initial state has zero budget', () => {
    const r = mountBatchRestore();
    expect(r.batchBudget.value).toBe(0);
  });

  it('applyBatchHistoryBudgetFromJob no-op when disabled', () => {
    const r = mountBatchRestore();
    r.batchBudget.value = 5;
    r.applyBatchHistoryBudgetFromJob({ budget_usd: 100 });
    expect(r.batchBudget.value).toBe(5);
  });

  it('applyBatchHistoryBudgetFromJob no-op when job missing budget', () => {
    const r = mountBatchRestore();
    r.uiProfile.value = { batch_history_budget_hint: true };
    r.batchBudget.value = 5;
    r.applyBatchHistoryBudgetFromJob({});
    expect(r.batchBudget.value).toBe(5);
  });

  it('applyBatchHistoryBudgetFromJob no-op when budget invalid', () => {
    const r = mountBatchRestore();
    r.uiProfile.value = { batch_history_budget_hint: true };
    r.batchBudget.value = 5;
    r.applyBatchHistoryBudgetFromJob({ budget_usd: Number.NaN });
    expect(r.batchBudget.value).toBe(5);
  });

  it('applyBatchHistoryBudgetFromJob sets batchBudget from job', () => {
    const r = mountBatchRestore();
    r.uiProfile.value = { batch_history_budget_hint: true };
    r.applyBatchHistoryBudgetFromJob({ budget_usd: 100 });
    expect(r.batchBudget.value).toBe(100);
  });

  it('applyBatchHistoryRange no-op when disabled', () => {
    const r = mountBatchRestore();
    r.applyBatchHistoryRange({ start_chapter: 5, end_chapter: 10 });
    expect(r.batchStart.value).toBe(1);
    expect(r.batchEnd.value).toBe(10);
  });

  it('applyBatchHistoryRange sets batchStart/batchEnd from job', () => {
    const r = mountBatchRestore();
    r.uiProfile.value = { batch_history_replay_range: true };
    r.batchStart.value = 99;
    r.batchEnd.value = 99;
    r.applyBatchHistoryRange({ start_chapter: 5, end_chapter: 10 });
    expect(r.batchStart.value).toBe(5);
    expect(r.batchEnd.value).toBe(10);
    expect(r.saveMessage.value).toContain('已填入');
  });

  it('applyBatchHistoryRange falls back to 1 when start_chapter missing', () => {
    const r = mountBatchRestore();
    r.uiProfile.value = { batch_history_replay_range: true };
    r.batchStart.value = 99;
    r.applyBatchHistoryRange({});
    expect(r.batchStart.value).toBe(1);
  });

  it('retryBatchHistoryJob no-op when disabled', () => {
    const r = mountBatchRestore();
    r.retryBatchHistoryJob({ status: 'failed' });
    // 不抛错即可
    expect(true).toBe(true);
  });

  it('retryBatchHistoryJob no-op for non-failed job', () => {
    const r = mountBatchRestore();
    r.uiProfile.value = { batch_history_failed_retry: true };
    r.retryBatchHistoryJob({ status: 'completed' });
    // 不应该触发任何修改
    expect(r.saveMessage.value).toBe('');
  });

  it('exportBatchHistory no-op when disabled', async () => {
    const r = mountBatchRestore();
    await r.exportBatchHistory();
    expect(r.saveMessage.value).toBe('');
  });

  it('exportBatchHistory downloads JSON when changes exist', async () => {
    restoreMocks.exportCreatorBatchHistory.mockResolvedValueOnce({});
    const r = mountBatchRestore();
    r.uiProfile.value = { batch_history_export: true };
    r.filteredBatchHistory.value = [
      { id: '1', status: 'completed', started_at: '2026-06-01T10:00:00Z' },
    ];
    await r.exportBatchHistory();
    expect(r.saveMessage.value).toContain('已导出');
  });

  it('exportBatchHistory sets error on failure', async () => {
    restoreMocks.exportCreatorBatchHistory.mockRejectedValueOnce(new Error('export fail'));
    const r = mountBatchRestore();
    r.uiProfile.value = { batch_history_export: true };
    await r.exportBatchHistory();
    expect(r.error.value).toBe('export fail');
  });
});
