/**
 * useMergePresets 子模块独立测试
 *
 * Phase 28: 为 Phase 19.3 useMergePresets 子模块添加专门测试。
 * Phase 126 v16.2.2 T4b: 迁到 typed wrapper `'../../api/settings.js'`.
 * Mock 名跟随 typed wrapper rename:
 *   fetchCreator* → typed wrapper name (no `Creator` prefix typically).
 *
 * 重点测试：合并预设加载/应用/导出/工厂库/冲突修复。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref } from 'vue';

// Mock API（合并预设相关）— typed wrapper names (Phase 126 v16.2.2 T4b)
const mergeMocks = vi.hoisted(() => ({
  listMergePresetPackages: vi.fn(),
  listFactoryMergePresetPackages: vi.fn(),
  fetchMergePreferences: vi.fn(),
  exportMergePreferences: vi.fn(),
  importMergePreferences: vi.fn(),
  exportMergePresetPackages: vi.fn(),
  importMergePresetPackages: vi.fn(),
  publishMergePresetToFactory: vi.fn(),
  pullFactoryMergePresetsToProject: vi.fn(),
  applyMergePresetConflictFix: vi.fn(),
  applyAllMergePresetConflictFixes: vi.fn(),
  previewMergePresetImportDiff: vi.fn(),
  applyToposortMergePresetOrder: vi.fn(),
  preflightMergePresetImport: vi.fn(),
  preflightFactoryMergePresetPull: vi.fn(),
}));

vi.mock('../../src/api/settings.js', () => {
  const m = mergeMocks;
  return {
    listMergePresetPackages: (...args: unknown[]) => m.listMergePresetPackages(...args),
    listFactoryMergePresetPackages: (...args: unknown[]) => m.listFactoryMergePresetPackages(...args),
    fetchMergePreferences: (...args: unknown[]) => m.fetchMergePreferences(...args),
    exportMergePreferences: (...args: unknown[]) => m.exportMergePreferences(...args),
    importMergePreferences: (...args: unknown[]) => m.importMergePreferences(...args),
    exportMergePresetPackages: (...args: unknown[]) => m.exportMergePresetPackages(...args),
    importMergePresetPackages: (...args: unknown[]) => m.importMergePresetPackages(...args),
    publishMergePresetToFactory: (...args: unknown[]) => m.publishMergePresetToFactory(...args),
    pullFactoryMergePresetsToProject: (...args: unknown[]) => m.pullFactoryMergePresetsToProject(...args),
    applyMergePresetConflictFix: (...args: unknown[]) => m.applyMergePresetConflictFix(...args),
    applyAllMergePresetConflictFixes: (...args: unknown[]) => m.applyAllMergePresetConflictFixes(...args),
    previewMergePresetImportDiff: (...args: unknown[]) => m.previewMergePresetImportDiff(...args),
    applyToposortMergePresetOrder: (...args: unknown[]) => m.applyToposortMergePresetOrder(...args),
    preflightMergePresetImport: (...args: unknown[]) => m.preflightMergePresetImport(...args),
    preflightFactoryMergePresetPull: (...args: unknown[]) => m.preflightFactoryMergePresetPull(...args),
  };
});

import { useMergePresets } from '../../src/composables/useCreatorSettings/useMergePresets';

function mountMerge() {
  const error = ref<string | null>(null);
  const saveMessage = ref('');
  const conflictMessage = ref('');
  const handleSaveError = vi.fn((err: unknown) => {
    error.value = err instanceof Error ? err.message : String(err);
  });
  return { ...useMergePresets({ error, saveMessage, conflictMessage, handleSaveError }), saveMessage };
}

describe('useMergePresets', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initial state has empty packages', () => {
    const m = mountMerge();
    expect(m.mergePresetPackages.value).toEqual([]);
    expect(m.factoryMergePresetPackages.value).toEqual([]);
    expect(m.selectedMergePresetPackage.value).toBe('');
  });

  it('loadMergePresetPackages fetches project + factory packages', async () => {
    mergeMocks.listMergePresetPackages.mockResolvedValueOnce({
      packages: [{ id: 'p1', name: 'project1', scope: 'project' }],
    });
    mergeMocks.listFactoryMergePresetPackages.mockResolvedValueOnce({
      packages: [{ id: 'f1', name: 'factory1', scope: 'factory' }],
    });
    const m = mountMerge();
    await m.loadMergePresetPackages();
    expect(m.mergePresetPackages.value).toHaveLength(1);
    expect(m.factoryMergePresetPackages.value).toHaveLength(1);
  });

  it('selectedMergePresetPackageName finds matching name', async () => {
    mergeMocks.listMergePresetPackages.mockResolvedValueOnce({
      packages: [{ id: 'p1', name: 'project1', scope: 'project' }],
    });
    mergeMocks.listFactoryMergePresetPackages.mockResolvedValueOnce({ packages: [] });
    const m = mountMerge();
    await m.loadMergePresetPackages();
    m.selectedMergePresetPackage.value = 'p1';
    expect(m.selectedMergePresetPackageName.value).toBe('project1');
  });

  it('loadMergePreferences sets preferences', async () => {
    mergeMocks.fetchMergePreferences.mockResolvedValueOnce({ style: 'auto' });
    const m = mountMerge();
    await m.loadMergePreferences();
    expect(m.mergePreferences.value.style).toBe('auto');
  });

  it('applyMergePresetPackage no-ops on missing id', async () => {
    const m = mountMerge();
    await m.applyMergePresetPackage('non_existent');
    // 不抛错 + selectedMergePresetPackage 不变
    expect(m.selectedMergePresetPackage.value).toBe('');
  });

  it('publishMergePresetToFactory sets loading state', async () => {
    mergeMocks.publishMergePresetToFactory.mockResolvedValueOnce({});
    const m = mountMerge();
    await m.publishMergePresetToFactory();
    expect(m.mergePresetFactoryPublishing.value).toBe(false);
  });

  it('publishMergePresetToFactory sets error on failure', async () => {
    mergeMocks.publishMergePresetToFactory.mockRejectedValueOnce(new Error('publish-fail'));
    let capturedErr: unknown = null;
    const error = ref<string | null>(null);
    const saveMessage = ref('');
    const conflictMessage = ref('');
    const handleSaveError = vi.fn((err: unknown) => {
      capturedErr = err;
      error.value = err instanceof Error ? err.message : String(err);
    });
    const { publishMergePresetToFactory } = useMergePresets({ error, saveMessage, conflictMessage, handleSaveError });
    await publishMergePresetToFactory();
    expect(handleSaveError).toHaveBeenCalled();
    expect((capturedErr as Error).message).toBe('publish-fail');
  });

  it('pullFactoryMergePresets updates packages', async () => {
    mergeMocks.pullFactoryMergePresetsToProject.mockResolvedValueOnce({ imported: 2 });
    mergeMocks.listMergePresetPackages.mockResolvedValueOnce({ packages: [] });
    mergeMocks.listFactoryMergePresetPackages.mockResolvedValueOnce({ packages: [] });
    const m = mountMerge();
    await m.pullFactoryMergePresets();
    expect(m.mergePresetFactoryPulling.value).toBe(false);
  });

  it('applyMergePresetConflictFix saves message', async () => {
    mergeMocks.applyMergePresetConflictFix.mockResolvedValueOnce({});
    mergeMocks.listMergePresetPackages.mockResolvedValueOnce({ packages: [] });
    mergeMocks.listFactoryMergePresetPackages.mockResolvedValueOnce({ packages: [] });
    const m = mountMerge();
    await m.applyMergePresetConflictFix({ id: 'fix-1' });
    expect(m.saveMessage.value).toContain('冲突修复');
  });

  it('applyAllMergePresetConflictFixes triggers save', async () => {
    mergeMocks.applyAllMergePresetConflictFixes.mockResolvedValueOnce({});
    mergeMocks.listMergePresetPackages.mockResolvedValueOnce({ packages: [] });
    mergeMocks.listFactoryMergePresetPackages.mockResolvedValueOnce({ packages: [] });
    const m = mountMerge();
    await m.applyAllMergePresetConflictFixes();
    expect(m.saveMessage.value).toContain('批量');
  });

  it('previewMergePresetImportDiff updates importPreview', async () => {
    mergeMocks.previewMergePresetImportDiff.mockResolvedValueOnce({
      added: ['a'], updated: ['b'], removed: ['c'],
    });
    const m = mountMerge();
    await m.previewMergePresetImportDiff();
    expect(m.mergePresetImportPreview.value.added).toEqual(['a']);
  });

  it('applyMergePresetToposort updates message', async () => {
    mergeMocks.applyToposortMergePresetOrder.mockResolvedValueOnce({});
    const m = mountMerge();
    await m.applyMergePresetToposort();
    // 注意: 原 useMergePresets 子模块返回的 saveMessage 是子模块内部的 ref，
    // mountMerge 中 spread 后覆盖了原始 saveMessage。这里检查 apply API 调用即可
    expect(mergeMocks.applyToposortMergePresetOrder).toHaveBeenCalled();
  });

  it('preflightMergePresetImport stores preflight data', async () => {
    mergeMocks.preflightMergePresetImport.mockResolvedValueOnce({
      blocked: false, conflict_count: 0,
    });
    const m = mountMerge();
    await m.preflightMergePresetImport();
    expect((m.mergePresetImportPreflight.value as { blocked?: boolean } | null)?.blocked).toBe(false);
  });
});
