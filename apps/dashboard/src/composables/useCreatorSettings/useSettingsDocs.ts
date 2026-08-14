/**
 * useSettingsDocs — 设定文档编辑 + 3-way diff + 保存流程
 *
 * Phase 19 Task 3.3：从 useCreatorSettings.js 拆出（完整实现）。
 * 负责: settingsDocs 加载 + diff 预览 + mergeStrategy preview + requestSaveSettings +
 *       confirmSaveSettings + bindGlobalOutlineEditorRef。
 */
import { ref } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import {
  fetchCreatorSettingsDocs,
  saveCreatorSettingsDocs,
  previewCreatorSettingsDocs,
  previewCreatorSettingsThreeWay,
  previewCreatorSettingsMerge,
} from '../../api/index.js';

interface SettingsDocs {
  pillars?: string;
  outline?: string;
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
    onAfterSettingsSave, globalOutlineEditorRef, globalOutlineText,
  } = deps;

  const settingsDocs = ref<SettingsDocs | null>(null);
  const pillarsText = ref('');
  const settingsBaseline = ref({ pillars: '', outline: '' });
  const settingsDiffPreview = ref<unknown>(null);
  const showSettingsDiff = ref(false);
  const settingsSaving = ref(false);
  const mergeStrategyPreview = ref<unknown>(null);
  const threeWayPreview = ref<unknown>(null);

  async function loadSettingsDocs(): Promise<void> {
    try {
      const data = await fetchCreatorSettingsDocs() as SettingsDocs;
      settingsDocs.value = data;
      const pillars = data.pillars || (data as Record<string, unknown>).pillars_text || '';
      const outline = data.outline || (data as Record<string, unknown>).global_outline_text || '';
      pillarsText.value = String(pillars);
      globalOutlineText.value = String(outline);
      settingsBaseline.value = { pillars: String(pillars), outline: String(outline) };
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function refreshMergeStrategyPreview(): Promise<void> {
    try {
      const data = await previewCreatorSettingsMerge({
        pillars: pillarsText.value,
        outline: globalOutlineText.value,
      });
      mergeStrategyPreview.value = data;
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function refreshThreeWayPreview(): Promise<void> {
    try {
      const data = await previewCreatorSettingsThreeWay({
        pillars: pillarsText.value,
        outline: globalOutlineText.value,
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
      const preview = await previewCreatorSettingsDocs({
        pillars: pillarsText.value,
        outline: globalOutlineText.value,
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
      await saveCreatorSettingsDocs({
        pillars: pillarsText.value,
        outline: globalOutlineText.value,
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