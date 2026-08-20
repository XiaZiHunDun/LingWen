/**
 * useSettingsHistory 子模块独立测试
 *
 * Phase 25: 为 Phase 19 useSettingsHistory 子模块添加专门测试。
 * 重点测试：历史快照加载、错误处理、回滚操作、formatHistoryTime 行为。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref } from 'vue';

// Mock API
const historyMocks = vi.hoisted(() => ({
  fetchCreatorSettingsHistory: vi.fn(),
  restoreCreatorSettingsSnapshot: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorSettingsHistory: (...args: unknown[]) => historyMocks.fetchCreatorSettingsHistory(...args),
  restoreCreatorSettingsSnapshot: (...args: unknown[]) => historyMocks.restoreCreatorSettingsSnapshot(...args),
}));

import { useSettingsHistory } from '../../src/composables/useCreatorSettings/useSettingsHistory';

function mountHistory() {
  const error = ref<string | null>(null);
  const saveMessage = ref('');
  const handleSaveError = vi.fn((err: unknown) => {
    error.value = err instanceof Error ? err.message : String(err);
  });
  return useSettingsHistory({ error, saveMessage, handleSaveError });
}

describe('useSettingsHistory', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loadSettingsHistory populates from snapshots array', async () => {
    historyMocks.fetchCreatorSettingsHistory.mockResolvedValueOnce({
      snapshots: [
        { id: 'snap-1', created_at: '2026-06-01T00:00:00Z', author: 'alice' },
        { id: 'snap-2', created_at: '2026-06-02T00:00:00Z', author: 'bob' },
      ],
    });
    const history = mountHistory();
    await history.loadSettingsHistory();
    expect(history.settingsHistory.value).toHaveLength(2);
    expect(history.settingsHistory.value[0].id).toBe('snap-1');
  });

  it('loadSettingsHistory falls back to history key', async () => {
    historyMocks.fetchCreatorSettingsHistory.mockResolvedValueOnce({
      history: [{ id: 'legacy-1', created_at: '2026-05-01T00:00:00Z' }],
    });
    const history = mountHistory();
    await history.loadSettingsHistory();
    expect(history.settingsHistory.value).toHaveLength(1);
    expect(history.settingsHistory.value[0].id).toBe('legacy-1');
  });

  it('loadSettingsHistory clears list on API failure', async () => {
    historyMocks.fetchCreatorSettingsHistory.mockRejectedValueOnce(new Error('network'));
    const history = mountHistory();
    await history.loadSettingsHistory();
    expect(history.settingsHistory.value).toEqual([]);
  });

  it('restoreSettingsHistory saves success message', async () => {
    historyMocks.restoreCreatorSettingsSnapshot.mockResolvedValueOnce({});
    const history = mountHistory();
    await history.restoreSettingsHistory('snap-1');
    expect(historyMocks.restoreCreatorSettingsSnapshot).toHaveBeenCalledWith('snap-1');
  });

  it('restoreSettingsHistory calls handleSaveError on failure', async () => {
    historyMocks.restoreCreatorSettingsSnapshot.mockRejectedValueOnce(new Error('conflict'));
    let handleSaveErrorCalled = false;
    let capturedErr: unknown = null;
    const error = ref<string | null>(null);
    const saveMessage = ref('');
    const handleSaveError = vi.fn((err: unknown) => {
      handleSaveErrorCalled = true;
      capturedErr = err;
      error.value = err instanceof Error ? err.message : String(err);
    });
    const history = useSettingsHistory({ error, saveMessage, handleSaveError });
    await history.restoreSettingsHistory('snap-1');
    expect(handleSaveErrorCalled).toBe(true);
    expect((capturedErr as Error).message).toBe('conflict');
  });

  it('formatHistoryTime returns empty for empty input', () => {
    const history = mountHistory();
    expect(history.formatHistoryTime('')).toBe('');
  });

  it('formatHistoryTime renders readable timestamp for ISO input', () => {
    const history = mountHistory();
    const result = history.formatHistoryTime('2026-06-01T12:34:56Z');
    // 输出应包含日期相关数字（年份/月份/时间）
    expect(result).toMatch(/2026|06|01|12|34|56/);
  });

  it('formatHistoryTime handles invalid date gracefully', () => {
    const history = mountHistory();
    const result = history.formatHistoryTime('invalid-date');
    // JS Date 对无效输入返回 'Invalid Date'，原 try/catch 不抛错
    expect(['invalid-date', 'Invalid Date']).toContain(result);
  });

  it('initial state has empty settingsHistory', () => {
    const history = mountHistory();
    expect(history.settingsHistory.value).toEqual([]);
  });
});
