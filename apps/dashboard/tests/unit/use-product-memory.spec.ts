/**
 * useProductMemory 子模块独立测试
 *
 * Phase 34: 为 Phase 19.1 useProductMemory 子模块添加专门测试。
 * 重点测试：记忆资产 + 搜索 + 标注 + 结构图 + 介入项。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref, ComputedRef } from 'vue';

const memMocks = vi.hoisted(() => ({
  fetchCreatorMemoryAssets: vi.fn(),
  saveCreatorMemoryAnnotation: vi.fn(),
  queryCreatorMemory: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorMemoryAssets: (...args: unknown[]) => memMocks.fetchCreatorMemoryAssets(...args),
  saveCreatorMemoryAnnotation: (...args: unknown[]) => memMocks.saveCreatorMemoryAnnotation(...args),
  queryCreatorMemory: (...args: unknown[]) => memMocks.queryCreatorMemory(...args),
}));

import { useProductMemory } from '../../src/composables/useCreatorProductTools/useProductMemory';

function mountMemory() {
  const overview = ref<Record<string, unknown> | null>(null);
  const editableVolumes = ref<Array<Record<string, unknown>>>([]);
  const visibleDeviations = ref<Array<Record<string, unknown>>>([]);
  const batchJob = ref<Record<string, unknown> | null>(null);
  const batchRunning = ref(false);
  const logicCheckResult = ref<Record<string, unknown> | null>(null);
  const pillarsText = ref('');
  const globalOutlineText = ref('');
  const error = ref<string | null>(null);
  const saveMessage = ref('');
  const preferences = ref<{ memoryRagTopK?: number; interventionRules?: Record<string, boolean> }>({
    memoryRagTopK: 5,
    interventionRules: {},
  });
  const setWorkspaceTab = vi.fn();
  const jumpToChapter = vi.fn(async () => {});

  const ctx = useProductMemory({
    overview, editableVolumes, visibleDeviations, batchJob, batchRunning,
    logicCheckResult, pillarsText, globalOutlineText, error, saveMessage,
    preferences, memoryRagTopK: ref(5),
    settingsHasUnsavedChanges: ref(false),
    setWorkspaceTab, jumpToChapter,
    } as unknown as Parameters<typeof useProductMemory>[0]);
  return {
    ...ctx, error, saveMessage, batchJob, batchRunning, logicCheckResult,
    overview, editableVolumes, visibleDeviations, preferences,
    setWorkspaceTab, jumpToChapter,
  };
}

describe('useProductMemory', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    memMocks.fetchCreatorMemoryAssets.mockResolvedValue({ items: [] });
  });

  it('initial state has all filter and loading false', () => {
    const m = mountMemory();
    expect(m.memoryFilter.value).toBe('all');
    expect(m.memoryAssetsLoading.value).toBe(false);
    expect(m.memoryAssetsLoadedOnce.value).toBe(false);
  });

  it('loadMemoryAssets populates from API', async () => {
    memMocks.fetchCreatorMemoryAssets.mockResolvedValueOnce({
      items: [
        { id: '1', kind: 'character', label: 'Alice' },
        { id: '2', kind: 'plot', label: '主线' },
      ],
      memory_available: true,
    });
    const m = mountMemory();
    await m.loadMemoryAssets();
    expect(m.memoryAssets.value).toHaveLength(2);
  });

  it('loadMemoryAssets sets loaded once on failure', async () => {
    memMocks.fetchCreatorMemoryAssets.mockRejectedValueOnce(new Error('down'));
    const m = mountMemory();
    await m.loadMemoryAssets();
    expect(m.memoryAssetsLoadedOnce.value).toBe(true);
  });

  it('memoryAssets falls back to local builder when API returns empty', async () => {
    const m = mountMemory();
    m.editableVolumes.value = [{ label: '第一卷', start_chapter: 1, end_chapter: 5 }];
    await m.loadMemoryAssets();
    // builder 返回基于 volumes 的 fallback
    expect(m.memoryAssets.value.length).toBeGreaterThan(0);
  });

  it('memoryAvailable reflects API payload', async () => {
    memMocks.fetchCreatorMemoryAssets.mockResolvedValueOnce({
      items: [],
      memory_available: true,
    });
    const m = mountMemory();
    await m.loadMemoryAssets();
    expect(m.memoryAvailable.value).toBe(true);
  });

  it('runMemorySearch no-op on empty query', async () => {
    memMocks.queryCreatorMemory.mockClear();
    const m = mountMemory();
    await m.runMemorySearch();
    expect(memMocks.queryCreatorMemory).not.toHaveBeenCalled();
  });

  it('runMemorySearch fetches results on valid query', async () => {
    memMocks.queryCreatorMemory.mockResolvedValueOnce({
      results: [{ id: '1', text: 'match' }],
      used_fallback: false,
    });
    const m = mountMemory();
    m.memorySearchQuery.value = 'test query';
    await m.runMemorySearch();
    expect(memMocks.queryCreatorMemory).toHaveBeenCalled();
    expect(m.memorySearchResults.value).toHaveLength(1);
  });

  it('runMemorySearch sets error on failure', async () => {
    memMocks.queryCreatorMemory.mockRejectedValueOnce(new Error('search fail'));
    const m = mountMemory();
    m.memorySearchQuery.value = 'test';
    await m.runMemorySearch();
    expect(m.error.value).toBe('search fail');
  });

  it('memoryAssetsFiltered returns all when filter is all', async () => {
    memMocks.fetchCreatorMemoryAssets.mockResolvedValueOnce({
      items: [
        { id: '1', kind: 'character' },
        { id: '2', kind: 'plot' },
        { id: '3', kind: 'character' },
      ],
    });
    const m = mountMemory();
    await m.loadMemoryAssets();
    m.memoryFilter.value = 'all';
    expect(m.memoryAssetsFiltered.value).toHaveLength(3);
  });

  it('handleInterventionAction pulse jumps to pulse tab', async () => {
    const m = mountMemory();
    await m.handleInterventionAction({ action: 'pulse', chapter: 5 });
    expect(m.setWorkspaceTab).toHaveBeenCalledWith('pulse');
    expect(m.jumpToChapter).toHaveBeenCalledWith(5);
  });

  it('handleInterventionAction settings jumps to settings tab', async () => {
    const m = mountMemory();
    await m.handleInterventionAction({ action: 'settings' });
    expect(m.setWorkspaceTab).toHaveBeenCalledWith('settings');
  });

  it('handleInterventionAction no-op on null', async () => {
    const m = mountMemory();
    await m.handleInterventionAction(null);
    expect(m.setWorkspaceTab).not.toHaveBeenCalled();
  });

  it('focusMemoryEntity clears focus and jumps to memory tab on null', () => {
    const m = mountMemory();
    m.memoryFocusAssetId.value = 'old';
    m.focusMemoryEntity(null);
    expect(m.memoryFocusAssetId.value).toBeNull();
    expect(m.setWorkspaceTab).toHaveBeenCalledWith('memory');
  });

  it('focusMemoryEntity sets focus and search query from name', () => {
    const m = mountMemory();
    m.focusMemoryEntity({ id: '1', kind: 'character', name: '伏笔：Alice' });
    expect(m.memoryFocusAssetId.value).toBe('1');
    expect(m.memoryFilter.value).toBe('character');
    expect(m.memorySearchQuery.value).toBe('Alice');
  });

  it('saveMemoryAnnotation calls API and reloads', async () => {
    memMocks.fetchCreatorMemoryAssets.mockResolvedValueOnce({ items: [] });
    const m = mountMemory();
    await m.saveMemoryAnnotation('asset-1', { pinned: true });
    expect(memMocks.saveCreatorMemoryAnnotation).toHaveBeenCalledWith('asset-1', { pinned: true });
    expect(m.saveMessage.value).toContain('记忆备注已保存');
  });
});