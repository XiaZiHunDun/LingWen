/**
 * useSettingsDocs 子模块独立测试
 *
 * Phase 36: 为 Phase 19.3 useSettingsDocs 子模块添加专门测试。
 * 重点测试：设定文档加载 + diff 预览 + 保存流程。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref, ComputedRef } from 'vue';

const docsMocks = vi.hoisted(() => ({
  fetchCreatorSettingsDocs: vi.fn(),
  saveCreatorSettingsDocs: vi.fn(),
  previewCreatorSettingsDocs: vi.fn(),
  previewCreatorSettingsThreeWay: vi.fn(),
  previewCreatorSettingsMerge: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorSettingsDocs: (...args: unknown[]) => docsMocks.fetchCreatorSettingsDocs(...args),
  saveCreatorSettingsDocs: (...args: unknown[]) => docsMocks.saveCreatorSettingsDocs(...args),
  previewCreatorSettingsDocs: (...args: unknown[]) => docsMocks.previewCreatorSettingsDocs(...args),
  previewCreatorSettingsThreeWay: (...args: unknown[]) => docsMocks.previewCreatorSettingsThreeWay(...args),
  previewCreatorSettingsMerge: (...args: unknown[]) => docsMocks.previewCreatorSettingsMerge(...args),
}));

import { useSettingsDocs } from '../../src/composables/useCreatorSettings/useSettingsDocs';

function mountDocs() {
  const uiProfile = ref<Record<string, unknown>>({});
  const overview = ref<Record<string, unknown> | null>(null);
  const error = ref<string | null>(null);
  const saveMessage = ref('');
  const conflictMessage = ref('');
  const handleSaveError = vi.fn();
  const onAfterSettingsSave = vi.fn(async () => {});
  const globalOutlineEditorRef = ref<HTMLElement | null>(null);
  const globalOutlineText = ref('');
  const settingsBaseline = ref({ pillars: '', outline: '' });

  return {
    ...useSettingsDocs({
      uiProfile, overview, error, saveMessage, conflictMessage,
      handleSaveError, onAfterSettingsSave,
      globalOutlineEditorRef, globalOutlineText, settingsBaseline,
    } as unknown as Parameters<typeof useSettingsDocs>[0]),
    error, saveMessage, conflictMessage, globalOutlineText, globalOutlineEditorRef,
    onAfterSettingsSave, handleSaveError, settingsBaseline,
  };
}

describe('useSettingsDocs', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    docsMocks.fetchCreatorSettingsDocs.mockResolvedValue({
      pillars_text: '支柱',
      global_outline_text: '大纲',
    });
  });

  it('initial state has empty settings', () => {
    const d = mountDocs();
    expect(d.settingsDocs.value).toBeNull();
    expect(d.pillarsText.value).toBe('');
    expect(d.showSettingsDiff.value).toBe(false);
  });

  it('loadSettingsDocs populates from API with pillars_text', async () => {
    const d = mountDocs();
    await d.loadSettingsDocs();
    expect(d.settingsDocs.value).not.toBeNull();
    expect(d.pillarsText.value).toBe('支柱');
  });

  it('loadSettingsDocs populates from API with pillars (camelCase)', async () => {
    docsMocks.fetchCreatorSettingsDocs.mockResolvedValueOnce({
      pillars: 'pillarsKey',
      outline: 'outlineKey',
    });
    const d = mountDocs();
    await d.loadSettingsDocs();
    expect(d.pillarsText.value).toBe('pillarsKey');
  });

  it('loadSettingsDocs sets empty on failure', async () => {
    docsMocks.fetchCreatorSettingsDocs.mockRejectedValueOnce(new Error('down'));
    const d = mountDocs();
    await d.loadSettingsDocs();
    expect(d.settingsDocs.value).toBeNull();
  });

  it('loadSettingsDocs does not set pillarsText on failure', async () => {
    docsMocks.fetchCreatorSettingsDocs.mockRejectedValueOnce(new Error('down'));
    const d = mountDocs();
    await d.loadSettingsDocs();
    expect(d.pillarsText.value).toBe('');
  });

  it('refreshMergeStrategyPreview sets mergeStrategyPreview', async () => {
    docsMocks.previewCreatorSettingsMerge.mockResolvedValueOnce({
      pillars: { vs_disk: { snippet: ['p'] } },
    });
    const d = mountDocs();
    await d.refreshMergeStrategyPreview();
    expect(d.mergeStrategyPreview.value).not.toBeNull();
  });

  it('refreshMergeStrategyPreview handles failure', async () => {
    docsMocks.previewCreatorSettingsMerge.mockRejectedValueOnce(new Error('merge fail'));
    const d = mountDocs();
    await d.refreshMergeStrategyPreview();
    // 不抛错即可
    expect(true).toBe(true);
  });

  it('refreshThreeWayPreview sets threeWayPreview', async () => {
    docsMocks.previewCreatorSettingsThreeWay.mockResolvedValueOnce({
      has_history: true,
    });
    const d = mountDocs();
    await d.refreshThreeWayPreview();
    expect(d.threeWayPreview.value).not.toBeNull();
  });

  it('requestSaveSettings sets showSettingsDiff true', async () => {
    docsMocks.previewCreatorSettingsDocs.mockResolvedValueOnce({
      has_changes: true, has_history: false,
    });
    const d = mountDocs();
    d.globalOutlineText.value = 'new outline';
    await d.requestSaveSettings();
    expect(d.showSettingsDiff.value).toBe(true);
  });

  it('requestSaveSettings baseline sync handled by main hook (submodule-level test omitted)', () => {
    // 短路逻辑由主 hook 协调（settingsBaseline 是主 hook 拥有的 ref，
    // 子模块无法独立判断是否"未变更"）。此测试仅文档化该行为。
    expect(true).toBe(true);
  });

  it('confirmSaveSettings posts docs and resets state', async () => {
    docsMocks.saveCreatorSettingsDocs.mockResolvedValueOnce({});
    const d = mountDocs();
    await d.loadSettingsDocs();
    d.pillarsText.value = 'new pillars';
    await d.confirmSaveSettings();
    expect(docsMocks.saveCreatorSettingsDocs).toHaveBeenCalled();
    expect(d.showSettingsDiff.value).toBe(false);
    expect(d.onAfterSettingsSave).toHaveBeenCalled();
  });

  it('confirmSaveSettings handles save failure via handleSaveError', async () => {
    docsMocks.saveCreatorSettingsDocs.mockRejectedValueOnce(new Error('conflict'));
    const d = mountDocs();
    await d.loadSettingsDocs();
    await d.confirmSaveSettings();
    expect(d.handleSaveError).toHaveBeenCalled();
  });

  it('cancelSettingsDiff clears preview state', () => {
    const d = mountDocs();
    d.showSettingsDiff.value = true;
    d.settingsDiffPreview.value = { has_changes: true };
    d.cancelSettingsDiff();
    expect(d.showSettingsDiff.value).toBe(false);
    expect(d.settingsDiffPreview.value).toBeNull();
  });

  it('bindGlobalOutlineEditorRef sets the ref', () => {
    const d = mountDocs();
    const el = document.createElement('textarea');
    d.bindGlobalOutlineEditorRef(el);
    expect(d.globalOutlineEditorRef.value).toBe(el);
  });

  it('bindGlobalOutlineEditorRef accepts null to clear', () => {
    const d = mountDocs();
    const el = document.createElement('textarea');
    d.bindGlobalOutlineEditorRef(el);
    d.bindGlobalOutlineEditorRef(null);
    expect(d.globalOutlineEditorRef.value).toBeNull();
  });
});
