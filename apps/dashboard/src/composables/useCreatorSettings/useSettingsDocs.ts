/**
 * useSettingsDocs — 设定文档编辑 + 3-way diff + 保存流程
 *
 * Phase 19 Task 3.3：从 useCreatorSettings.js 拆出（完整实现）。
 * Phase 126 v16.2.2 T4b：从 `'../../api/index.js'` 迁到 `'../../api/settings.js'`
 * typed wrapper。`request()` 自动加 `/api/` 前缀（无 `/api/` 写死在代码里，
 * v16.2.1 教训）。
 *
 * 负责: settingsDocs 加载 + diff 预览 + mergeStrategy preview + requestSaveSettings +
 *       confirmSaveSettings + bindGlobalOutlineEditorRef。
 */
import { ref, shallowRef } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import {
  fetchSettingsDocs,
  saveSettingsDocs,
  previewSettingsDocsDiff,
  previewSettingsThreeWay,
  previewSettingsMergeStrategy,
} from '@/api/settings';
import type { CreatorSettingsDocsResponse } from '@lingwen/dashboard-contracts/shared';

interface SettingsDocs {
  pillars?: string;
  outline?: string;
  pillars_text?: string;
  global_outline_text?: string;
}

export interface SettingsDocsDeps {
  uiProfile: ComputedRef<Record<string, unknown>>;
  overview: Ref<Record<string, unknown> | null>;
  error: Ref<string | null>;
  saveMessage: Ref<string>;
  conflictMessage: Ref<string>;
  handleSaveError: (err: unknown) => void;
  onAfterSettingsSave: () => Promise<void>;
  globalOutlineEditorRef: Ref<HTMLElement | null>;
  globalOutlineText: Ref<string>;
  // settingsBaseline 由主 hook 拥有并传入（避免双同步 wrapper）
  settingsBaseline: Ref<{ pillars: string; outline: string }>;
}

export interface SettingsDocsReturn {
  settingsDocs: Ref<SettingsDocs | null>;
  pillarsText: Ref<string>;
  settingsBaseline: Ref<{ pillars: string; outline: string }>;
  settingsDiffPreview: Ref<unknown>;
  showSettingsDiff: Ref<boolean>;
  settingsSaving: Ref<boolean>;
  mergeStrategyPreview: Ref<unknown>;
  threeWayPreview: Ref<unknown>;
  loadSettingsDocs: () => Promise<void>;
  refreshMergeStrategyPreview: () => Promise<void>;
  refreshThreeWayPreview: () => Promise<void>;
  requestSaveSettings: () => Promise<void>;
  confirmSaveSettings: () => Promise<void>;
  cancelSettingsDiff: () => void;
  bindGlobalOutlineEditorRef: (el: HTMLElement | null) => void;
}

export function useSettingsDocs(deps: SettingsDocsDeps): SettingsDocsReturn {
  const {
    overview, error, saveMessage, handleSaveError,
    onAfterSettingsSave, globalOutlineEditorRef, globalOutlineText, settingsBaseline,
  } = deps;

  const settingsDocs = shallowRef<SettingsDocs | null>(null); // Phase 78: shallowRef — wholesale replacement
  const pillarsText = shallowRef(''); // Phase 78: shallowRef — wholesale replacement
  const settingsDiffPreview = shallowRef<unknown>(null); // Phase 78: shallowRef — wholesale replacement
  const showSettingsDiff = ref(false);
  const settingsSaving = ref(false);
  const mergeStrategyPreview = shallowRef<unknown>(null); // Phase 78: shallowRef — wholesale replacement
  const threeWayPreview = shallowRef<unknown>(null); // Phase 78: shallowRef — wholesale replacement

  async function loadSettingsDocs(): Promise<void> {
    try {
      const data: CreatorSettingsDocsResponse = await fetchSettingsDocs();
      settingsDocs.value = data as unknown as SettingsDocs;
      // typed wrapper uses snake_case (`pillars_text`, `global_outline_text`) — accept
      // legacy `pillars`/`outline` aliases for backward compatibility.
      const pillars = (data as unknown as SettingsDocs).pillars_text
        ?? (data as unknown as Record<string, unknown>).pillars
        ?? '';
      const outline = (data as unknown as SettingsDocs).global_outline_text
        ?? (data as unknown as Record<string, unknown>).outline
        ?? '';
      pillarsText.value = String(pillars);
      globalOutlineText.value = String(outline);
      settingsBaseline.value = { pillars: String(pillars), outline: String(outline) };
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function refreshMergeStrategyPreview(): Promise<void> {
    try {
      const data = await previewSettingsMergeStrategy({
        pillars_text: pillarsText.value,
        global_outline_text: globalOutlineText.value,
      });
      mergeStrategyPreview.value = data;
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function refreshThreeWayPreview(): Promise<void> {
    try {
      const data = await previewSettingsThreeWay({
        pillars_text: pillarsText.value,
        global_outline_text: globalOutlineText.value,
      });
      threeWayPreview.value = data;
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function requestSaveSettings(): Promise<void> {
    settingsSaving.value = true;
    error.value = null;
    try {
      const preview = await previewSettingsDocsDiff({
        pillars_text: pillarsText.value,
        global_outline_text: globalOutlineText.value,
      });
      settingsDiffPreview.value = preview;
      showSettingsDiff.value = true;
    } catch (e) {
      handleSaveError(e);
    } finally {
      settingsSaving.value = false;
    }
  }

  async function confirmSaveSettings(): Promise<void> {
    settingsSaving.value = true;
    try {
      await saveSettingsDocs({
        pillars_text: pillarsText.value,
        global_outline_text: globalOutlineText.value,
      });
      settingsBaseline.value = { pillars: pillarsText.value, outline: globalOutlineText.value };
      showSettingsDiff.value = false;
      saveMessage.value = '设定已保存';
      await onAfterSettingsSave();
    } catch (e) {
      handleSaveError(e);
    } finally {
      settingsSaving.value = false;
    }
  }

  function cancelSettingsDiff(): void {
    showSettingsDiff.value = false;
    settingsDiffPreview.value = null;
  }

  function bindGlobalOutlineEditorRef(el: HTMLElement | null): void {
    globalOutlineEditorRef.value = el;
  }

  return {
    settingsDocs,
    pillarsText,
    settingsBaseline,
    settingsDiffPreview,
    showSettingsDiff,
    settingsSaving,
    mergeStrategyPreview,
    threeWayPreview,
    loadSettingsDocs,
    refreshMergeStrategyPreview,
    refreshThreeWayPreview,
    requestSaveSettings,
    confirmSaveSettings,
    cancelSettingsDiff,
    bindGlobalOutlineEditorRef,
  };
}
