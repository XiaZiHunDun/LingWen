/**
 * useCreatorSettings — 设定栏与合并预设逻辑（从 CreatorPage 抽出）
 *
 * Phase 19 Task 3.5 完成版：抽出全部 3 个 .ts 子模块 + 主 hook 顶层 API 包装。
 * 下游 API（panelContext shape + 顶层 load* 导出）保持完全兼容。
 *
 * 子模块：
 * - useSettingsHistory   (设定历史快照 + 恢复)
 * - useMergePresets      (合并预设 + 工厂库 + 冲突修复)
 * - useSettingsDocs      (设定文档编辑 + 3-way diff + 保存)
 *
 * 主 hook 编排：
 * 1. 创建跨子模块共享 ref（pillarsMergeSource/outlineMergeSource 等）
 * 2. 初始化 3 个子模块（每个接收 deps）
 * 3. 暴露原 panelContext shape（70+ keys） + 顶层 load*
 */
import { computed, ref, shallowRef, watch } from 'vue';
// T4a (Phase 126 v16.2.2): simple settings subset now uses typed wrapper
// (`@/api/settings`). /api/ prefix is added by `core.js`'s `request()`.
import {
  fetchSettingsHistory,
  restoreSettingsSnapshot,
  saveSettingsDocs,
  previewSettingsDocsDiff,
  previewSettingsThreeWay,
} from '../api/settings.js';
// Legacy imports — T4b carryover (merge preset / changelog / conflict / etc.).
import {
  fetchCreatorMergePresetChangelog,
  fetchCreatorMergePresetChangelogDiff,
  fetchCreatorMergePreferences,
  exportCreatorMergePreferences,
  importCreatorMergePreferences,
} from '../api/index.js';
import {
  useSettingsHistory,
  useMergePresets,
  useSettingsDocs,
} from './useCreatorSettings/index.ts';

function formatHistoryTime(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleString('zh-CN', { hour12: false });
  } catch {
    return iso;
  }
}

/**
 * @param {{
 *   uiProfile: import('vue').ComputedRef<object>,
 *   overview: import('vue').Ref<object|null>,
 *   error: import('vue').Ref<string|null>,
 *   saveMessage: import('vue').Ref<string>,
 *   conflictMessage: import('vue').Ref<string>,
 *   handleSaveError: (err: unknown) => void,
 *   onAfterSettingsSave: () => Promise<void>,
 *   globalOutlineEditorRef: import('vue').Ref<HTMLElement|null>,
 *   globalOutlineText: import('vue').Ref<string>,
 *   isWorkspaceColumnVisible: (col: string) => boolean,
 *   workspaceTabsEnabled: import('vue').ComputedRef<boolean>,
 *   logicCheckRunning: import('vue').Ref<boolean>,
 *   logicCheckResult: import('vue').Ref<object|null>,
 *   activeLogicCheckIssueIdx: import('vue').Ref<number|null>,
 *   runCompanionLogicCheck: () => Promise<void>,
 *   handleLogicCheckIssueClick: (issue: object, idx: number) => Promise<void>,
 *   onLogicCheckIssueKeydown: (event: KeyboardEvent, issue: object, idx: number) => void,
 * }} deps
 */
export function useCreatorSettings(deps) {
  const {
    uiProfile, overview, error, saveMessage, conflictMessage, handleSaveError, onAfterSettingsSave,
    globalOutlineEditorRef, globalOutlineText,
    isWorkspaceColumnVisible, workspaceTabsEnabled,
    logicCheckRunning, logicCheckResult, activeLogicCheckIssueIdx,
    runCompanionLogicCheck, handleLogicCheckIssueClick, onLogicCheckIssueKeydown,
  } = deps;

  // --- 共享 ref（跨子模块）---
  const settingsDocs = shallowRef(null); // Phase 77: shallowRef — wholesale replacement
  // pillarsText: 使用 settingsDocsApi 子模块的 ref 以保持单一真源
  const settingsBaseline = shallowRef({ pillars: '', outline: '' }); // Phase 77: shallowRef — wholesale replacement
  const settingsDiffPreview = shallowRef(null); // Phase 77: shallowRef — wholesale replacement
  const showSettingsDiff = ref(false);
  const settingsSaving = ref(false);
  const settingsHistory = shallowRef([]); // Phase 77: shallowRef — wholesale replacement
  const settingsRestoring = ref(false);
  const usesGlobalMergeDefault = ref(false);
  const mergePresetPackages = shallowRef([]); // Phase 77: shallowRef — wholesale replacement
  const factoryMergePresetPackages = shallowRef([]); // Phase 77: shallowRef — wholesale replacement
  const selectedMergePresetPackage = ref('');
  const showImportMergePresetPackages = ref(false);
  const importMergePresetPackagesJson = ref('');
  const mergePresetPackagesImporting = ref(false);
  const mergePresetImportDiff = shallowRef({ added: [], updated: [], removed: [] }); // Phase 77: shallowRef — wholesale replacement
  const mergePresetChangelog = shallowRef({ package_id: '', entry_count: 0, entries: [] }); // Phase 77: shallowRef — wholesale replacement
  const mergePresetChangelogDiff = shallowRef({ change_count: 0, changes: [] }); // Phase 77: shallowRef — wholesale replacement
  const factoryMergePresetPullConflicts = shallowRef({ conflict_count: 0, conflicts: [] }); // Phase 77: shallowRef — wholesale replacement
  const mergePresetImportPreflight = shallowRef(null); // Phase 77: shallowRef — wholesale replacement
  const mergePresetFactoryPublishing = ref(false);
  const mergePresetFactoryPulling = ref(false);
  const showImportMergePrefs = ref(false);
  const importMergePrefsJson = ref('');
  const mergePrefsImporting = ref(false);
  const pillarsSnapshotId = ref('');
  const outlineSnapshotId = ref('');
  const compareSnapshotId = ref('');
  const pillarsMergeSource = ref('editor');
  const outlineMergeSource = ref('editor');
  const mergeStrategyPreview = ref(null);

  // --- 子模块初始化 ---
  const history = useSettingsHistory({
    error, saveMessage, handleSaveError,
  });
  const mergePresets = useMergePresets({
    error, saveMessage, conflictMessage, handleSaveError,
  });
  const settingsDocsApi = useSettingsDocs({
    uiProfile, overview, error, saveMessage, conflictMessage,
    handleSaveError, onAfterSettingsSave,
    globalOutlineEditorRef, globalOutlineText, settingsBaseline,
  });

  // --- Computed ---
  const settingsDiffSnippet = computed(() => {
    const preview = settingsDiffPreview.value;
    if (!preview) return [];
    const lines = [];
    if (preview.pillars?.snippet?.length) lines.push(...preview.pillars.snippet);
    if (preview.global_outline?.snippet?.length) lines.push(...preview.global_outline.snippet);
    return lines.slice(0, 12);
  });

  const settingsHasUnsavedChanges = computed(
    () => settingsDocsApi.pillarsText.value !== settingsBaseline.value.pillars
      || globalOutlineText.value !== settingsBaseline.value.outline,
  );

  const factoryMergePresetCount = computed(
    () => mergePresetPackages.value.filter((pkg) => pkg.scope === 'factory').length,
  );

  const selectedProjectMergePreset = computed(() => {
    const pkg = mergePresetPackages.value.find((row) => row.id === selectedMergePresetPackage.value);
    return pkg?.scope === 'project' && !pkg?.builtin;
  });

  const showMergeStrategy = computed(() => {
    const preview = settingsDiffPreview.value;
    if (!preview?.has_history) return false;
    const diskHist = preview.disk_vs_history;
    const editorHist = preview.editor_vs_history;
    return Boolean(
      diskHist?.pillars?.changed
      || diskHist?.global_outline?.changed
      || editorHist?.pillars?.changed
      || editorHist?.global_outline?.changed,
    );
  });

  const mergeStrategySnippet = computed(() => {
    const preview = mergeStrategyPreview.value;
    if (!preview) return [];
    return [
      ...(preview.pillars?.vs_disk?.snippet || []),
      ...(preview.global_outline?.vs_disk?.snippet || []),
    ].slice(0, 12);
  });

  // --- Helpers ---
  function formatMergePresetOption(pkg) {
    if (pkg.version_label) {
      const prefix = pkg.version_semver_valid === false ? '!' : '';
      return `${prefix}[${pkg.version_label}] ${pkg.name}`;
    }
    return pkg.name;
  }

  function bindGlobalOutlineEditorRef(el) {
    globalOutlineEditorRef.value = el;
  }

  // --- 合并流程（main hook 内部，因为跨多个 ref）---
  function refreshMergeStrategyPreview() {
    return settingsDocsApi.refreshMergeStrategyPreview();
  }

  function applyMergePreset(source) {
    pillarsMergeSource.value = source;
    outlineMergeSource.value = source;
    selectedMergePresetPackage.value = '';
    if (source === 'history' && settingsHistory.value.length) {
      const snapId = compareSnapshotId.value || settingsHistory.value[0].id;
      pillarsSnapshotId.value = snapId;
      outlineSnapshotId.value = snapId;
    }
    refreshMergeStrategyPreview();
  }

  function applyMergePresetPackage(packageId) {
    const pkg = mergePresetPackages.value.find((row) => row.id === packageId);
    if (!pkg) return;
    pillarsMergeSource.value = pkg.pillars_merge_source;
    outlineMergeSource.value = pkg.global_outline_merge_source;
    if (pkg.pillars_merge_source === 'history' && settingsHistory.value.length) {
      pillarsSnapshotId.value = compareSnapshotId.value || settingsHistory.value[0].id;
    }
    if (pkg.global_outline_merge_source === 'history' && settingsHistory.value.length) {
      outlineSnapshotId.value = compareSnapshotId.value || settingsHistory.value[0].id;
    }
    refreshMergeStrategyPreview();
  }

  function onMergePresetPackageChange() {
    const packageId = selectedMergePresetPackage.value;
    if (packageId) applyMergePresetPackage(packageId);
  }

  // --- Settings History 加载（用子模块 + watch）---
  async function loadSettingsHistory() {
    try {
      const data = await fetchSettingsHistory();
      const list = data?.snapshots || data?.history || [];
      settingsHistory.value = list;
      history.settingsHistory.value = list;
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    }
  }

  async function restoreSettingsHistory(snapshotId) {
    settingsRestoring.value = true;
    try {
      const docs = await restoreSettingsSnapshot({ snapshot_id: snapshotId });
      settingsDocs.value = docs;
      const pillars = docs?.pillars_text || docs?.pillars || '';
      const outline = docs?.global_outline_text || docs?.outline || '';
      settingsDocsApi.pillarsText.value = String(pillars);
      globalOutlineText.value = String(outline);
      settingsBaseline.value = {
        pillars: String(pillars),
        outline: String(outline),
      };
      settingsDocsApi.settingsBaseline.value = settingsBaseline.value;
      saveMessage.value = '已从历史版本恢复设定';
    } catch (e) {
      handleSaveError(e);
    } finally {
      settingsRestoring.value = false;
    }
  }

  // --- Merge Preset 加载（用子模块 + 共享 ref）---
  async function loadMergePresetPackages() {
    mergePresets.mergePresetPackages.value = mergePresetPackages.value;
    try {
      const { fetchCreatorMergePresetPackages, fetchCreatorFactoryMergePresetPackages } = await import('../api/index.js');
      const data = await fetchCreatorMergePresetPackages();
      mergePresetPackages.value = data?.packages || [];
      const factoryData = await fetchCreatorFactoryMergePresetPackages();
      factoryMergePresetPackages.value = factoryData?.packages || [];
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function loadMergePreferences() {
    try {
      const data = await fetchCreatorMergePreferences();
      mergePresets.mergePreferences.value = data;
      usesGlobalMergeDefault.value = Boolean(data?.uses_global_default);
    } catch (e) {
      handleSaveError(e);
    }
  }

  // --- Save / Diff 流程（用 settingsDocs 子模块 + 共享 ref）---
  async function refreshThreeWayPreview() {
    return settingsDocsApi.refreshThreeWayPreview();
  }

  async function requestSaveSettings() {
    settingsSaving.value = true;
    error.value = null;
    if (
      settingsDocsApi.pillarsText.value === settingsBaseline.value.pillars
      && globalOutlineText.value === settingsBaseline.value.outline
    ) {
      saveMessage.value = '设定无变更';
      return;
    }
    try {
      if (settingsHistory.value.length) {
        const threeWay = await previewSettingsThreeWay({
          pillars_text: settingsDocsApi.pillarsText.value,
          global_outline_text: globalOutlineText.value,
          snapshot_id: compareSnapshotId.value || undefined,
        });
        settingsDiffPreview.value = threeWay;
        settingsDocsApi.settingsDiffPreview.value = threeWay;
        settingsDocsApi.threeWayPreview.value = threeWay;
      } else {
        const preview = await previewSettingsDocsDiff({
          pillars_text: settingsDocsApi.pillarsText.value,
          global_outline_text: globalOutlineText.value,
        });
        settingsDiffPreview.value = preview;
        settingsDocsApi.settingsDiffPreview.value = preview;
      }
      settingsDocsApi.showSettingsDiff.value = true;
      showSettingsDiff.value = true;
      saveMessage.value = '已生成变更预览';
    } catch (e) {
      handleSaveError(e);
    } finally {
      settingsSaving.value = false;
    }
  }

  async function confirmSaveSettings() {
    settingsSaving.value = true;
    try {
      await saveSettingsDocs({
        pillars_text: settingsDocsApi.pillarsText.value,
        global_outline_text: globalOutlineText.value,
      });
      settingsBaseline.value = {
        pillars: settingsDocsApi.pillarsText.value,
        outline: globalOutlineText.value,
      };
      settingsDocsApi.settingsBaseline.value = settingsBaseline.value;
      settingsDocsApi.showSettingsDiff.value = false;
      showSettingsDiff.value = false;
      settingsDiffPreview.value = null;
      settingsDocsApi.settingsDiffPreview.value = null;
      mergeStrategyPreview.value = null;
      saveMessage.value = '设定已保存';
      conflictMessage.value = '';
      await onAfterSettingsSave();
    } catch (e) {
      handleSaveError(e);
    } finally {
      settingsSaving.value = false;
    }
  }

  function cancelSettingsDiff() {
    settingsDocsApi.showSettingsDiff.value = false;
    showSettingsDiff.value = false;
    settingsDiffPreview.value = null;
    settingsDocsApi.settingsDiffPreview.value = null;
    settingsDocsApi.mergeStrategyPreview.value = null;
  }

  // --- Watch: selectedMergePresetPackage 变化时加载 changelog ---
  watch(selectedMergePresetPackage, async (packageId) => {
    if (packageId) {
      applyMergePresetPackage(packageId);
      try {
        mergePresetChangelog.value = await fetchCreatorMergePresetChangelog(packageId);
      } catch {
        mergePresetChangelog.value = { package_id: packageId, entry_count: 0, entries: [] };
      }
    } else {
      mergePresetChangelog.value = { package_id: '', entry_count: 0, entries: [] };
    }
  });

  // --- 包装 mergePreset 操作（链接到 ref）---
  async function exportMergePresetPackages() {
    try {
      const { exportCreatorMergePresetPackages } = await import('../api/index.js');
      const data = await exportCreatorMergePresetPackages();
      const text = JSON.stringify(data, null, 2);
      importMergePresetPackagesJson.value = text;
      if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
        saveMessage.value = '已导出预设包并复制到剪贴板';
      } else {
        saveMessage.value = '已导出预设包（见导入框）';
        showImportMergePresetPackages.value = true;
      }
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function importMergePresetPackagesFromJson() {
    mergePresetPackagesImporting.value = true;
    error.value = null;
    try {
      const payload = JSON.parse(importMergePresetPackagesJson.value);
      if (mergePresetImportPreflight.value?.blocked) {
        saveMessage.value = '预检仍有冲突，请先修复或调整 JSON';
        return;
      }
      const { importCreatorMergePresetPackages } = await import('../api/index.js');
      await importCreatorMergePresetPackages(payload);
      importMergePresetPackagesJson.value = '';
      showImportMergePresetPackages.value = false;
      mergePresetImportPreflight.value = null;
      saveMessage.value = '已导入合并预设';
      await loadMergePresetPackages();
    } catch (e) {
      handleSaveError(e);
    } finally {
      mergePresetPackagesImporting.value = false;
    }
  }

  async function publishMergePresetToFactory() {
    mergePresetFactoryPublishing.value = true;
    try {
      const { publishCreatorMergePresetToFactory } = await import('../api/index.js');
      await publishCreatorMergePresetToFactory({});
      saveMessage.value = '已发布到工厂库';
    } catch (e) {
      handleSaveError(e);
    } finally {
      mergePresetFactoryPublishing.value = false;
    }
  }

  async function pullFactoryMergePresets() {
    mergePresetFactoryPulling.value = true;
    try {
      const { pullCreatorFactoryMergePresetPackages, preflightCreatorFactoryMergePresetPull } = await import('../api/index.js');
      const preflight = await preflightCreatorFactoryMergePresetPull({});
      factoryMergePresetPullConflicts.value = preflight || { conflict_count: 0, conflicts: [] };
      if (preflight?.conflict_count > 0) {
        saveMessage.value = `预检发现 ${preflight.conflict_count} 处冲突`;
        return;
      }
      const result = await pullCreatorFactoryMergePresetPackages({});
      saveMessage.value = `已从工厂库拉取 ${result.imported} 个预设`;
      await loadMergePresetPackages();
    } catch (e) {
      handleSaveError(e);
    } finally {
      mergePresetFactoryPulling.value = false;
    }
  }

  async function pullFactoryMergePresetsWithStrategy(packageId, strategy) {
    mergePresetFactoryPulling.value = true;
    try {
      const { pullCreatorFactoryMergePresetPackages, preflightCreatorFactoryMergePresetPull } = await import('../api/index.js');
      const preflight = await preflightCreatorFactoryMergePresetPull({ package_id: packageId, strategy });
      factoryMergePresetPullConflicts.value = preflight || { conflict_count: 0, conflicts: [] };
      if (preflight?.conflict_count > 0) {
        saveMessage.value = `预检发现 ${preflight.conflict_count} 处冲突`;
        return;
      }
      const result = await pullCreatorFactoryMergePresetPackages({ package_id: packageId, strategy });
      saveMessage.value = `已拉取 ${result.imported} 个预设`;
      await loadMergePresetPackages();
    } catch (e) {
      handleSaveError(e);
    } finally {
      mergePresetFactoryPulling.value = false;
    }
  }

  async function previewMergePresetChangelogDiff(entryIndex) {
    try {
      const data = await fetchCreatorMergePresetChangelogDiff(entryIndex);
      mergePresetChangelogDiff.value = data;
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function applyMergePresetConflictFix(fix) {
    try {
      const { applyCreatorMergePresetConflictFix } = await import('../api/index.js');
      await applyCreatorMergePresetConflictFix(fix);
      saveMessage.value = '已应用冲突修复';
      await loadMergePresetPackages();
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function applyAllMergePresetConflictFixes() {
    try {
      const { applyAllCreatorMergePresetConflictFixes } = await import('../api/index.js');
      await applyAllCreatorMergePresetConflictFixes();
      saveMessage.value = '已批量应用冲突修复';
      await loadMergePresetPackages();
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function previewMergePresetImportDiff() {
    try {
      const { previewCreatorMergePresetImportDiff } = await import('../api/index.js');
      const data = await previewCreatorMergePresetImportDiff({});
      mergePresetImportDiff.value = data || { added: [], updated: [], removed: [] };
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function applyMergePresetToposort() {
    try {
      const { applyCreatorMergePresetToposort } = await import('../api/index.js');
      await applyCreatorMergePresetToposort();
      saveMessage.value = '已应用拓扑排序';
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function preflightMergePresetImport() {
    try {
      const { preflightCreatorMergePresetImport } = await import('../api/index.js');
      const data = await preflightCreatorMergePresetImport({});
      mergePresetImportPreflight.value = data;
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function exportMergePreferences() {
    error.value = null;
    try {
      const data = await exportCreatorMergePreferences();
      const text = JSON.stringify(data, null, 2);
      importMergePrefsJson.value = text;
      if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
        saveMessage.value = '已导出合并策略并复制到剪贴板';
      } else {
        saveMessage.value = '已导出合并策略（见导入框）';
        showImportMergePrefs.value = true;
      }
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function importMergePreferencesFromJson() {
    mergePrefsImporting.value = true;
    error.value = null;
    try {
      const payload = JSON.parse(importMergePrefsJson.value);
      await importCreatorMergePreferences({ ...payload, scope: payload.scope || 'both' });
      saveMessage.value = '已导入合并策略';
      importMergePrefsJson.value = '';
      showImportMergePrefs.value = false;
      await loadMergePreferences();
    } catch (e) {
      handleSaveError(e);
    } finally {
      mergePrefsImporting.value = false;
    }
  }

  // --- loadSettingsDocs: settingsBaseline 已通过 deps 共享给子模块（无需包装）---

  // --- panelContext 聚合 ---
  const panelContext = {
    uiProfile,
    overview,
    isWorkspaceColumnVisible,
    pillarsText: settingsDocsApi.pillarsText,
    globalOutlineText,
    settingsDocs,
    settingsSaving,
    settingsHasUnsavedChanges,
    requestSaveSettings,
    showSettingsDiff: settingsDocsApi.showSettingsDiff,
    settingsDiffPreview: settingsDocsApi.settingsDiffPreview,
    settingsDiffSnippet,
    settingsHistory,
    compareSnapshotId,
    refreshThreeWayPreview,
    formatHistoryTime,
    showMergeStrategy,
    usesGlobalMergeDefault,
    applyMergePreset,
    mergePresetPackages,
    formatMergePresetOption,
    selectedMergePresetPackage,
    onMergePresetPackageChange,
    exportMergePresetPackages,
    showImportMergePresetPackages,
    mergePresetFactoryPublishing,
    selectedProjectMergePreset,
    publishMergePresetToFactory,
    mergePresetFactoryPulling,
    factoryMergePresetCount,
    pullFactoryMergePresets,
    mergePresetChangelog,
    previewMergePresetChangelogDiff,
    mergePresetChangelogDiff,
    factoryMergePresetPullConflicts,
    pullFactoryMergePresetsWithStrategy,
    applyAllMergePresetConflictFixes,
    applyMergePresetConflictFix,
    importMergePresetPackagesJson,
    mergePresetPackagesImporting,
    previewMergePresetImportDiff,
    applyMergePresetToposort,
    mergePresetImportDiff,
    preflightMergePresetImport,
    importMergePresetPackagesFromJson,
    pillarsMergeSource,
    refreshMergeStrategyPreview,
    pillarsSnapshotId,
    outlineMergeSource,
    outlineSnapshotId,
    mergeStrategyPreview,
    mergeStrategySnippet,
    exportMergePreferences,
    showImportMergePrefs,
    importMergePrefsJson,
    mergePrefsImporting,
    importMergePreferencesFromJson,
    confirmSaveSettings,
    cancelSettingsDiff,
    settingsRestoring,
    restoreSettingsHistory,
    workspaceTabsEnabled,
    logicCheckRunning,
    runCompanionLogicCheck,
    logicCheckResult,
    activeLogicCheckIssueIdx,
    handleLogicCheckIssueClick,
    onLogicCheckIssueKeydown,
    bindGlobalOutlineEditorRef,
  };

  return {
    panelContext,
    pillarsText: settingsDocsApi.pillarsText,
    settingsHasUnsavedChanges,
    loadSettingsDocs: settingsDocsApi.loadSettingsDocs,
    loadSettingsHistory,
    loadMergePreferences,
    loadMergePresetPackages,
  };
}
