/**
 * useCreatorSettings — 设定栏与合并预设逻辑（从 CreatorPage 抽出）
 */
import { computed, ref, watch } from 'vue';
import {
  fetchCreatorSettingsDocs,
  saveCreatorSettingsDocs,
  previewCreatorSettingsDocs,
  previewCreatorSettingsThreeWay,
  previewCreatorSettingsMerge,
  fetchCreatorMergePreferences,
  exportCreatorMergePreferences,
  importCreatorMergePreferences,
  fetchCreatorSettingsHistory,
  restoreCreatorSettingsSnapshot,
  preflightCreatorFactoryMergePresetPull,
  fetchCreatorMergePresetChangelog,
  fetchCreatorMergePresetChangelogDiff,
  fetchCreatorMergePresetToposort,
  fetchCreatorMergePresetPackages,
  fetchCreatorFactoryMergePresetPackages,
  fetchCreatorMergePresetGraph,
  fetchCreatorMergePresetConflicts,
  fetchCreatorMergePresetConflictFixes,
  applyCreatorMergePresetConflictFix,
  applyAllCreatorMergePresetConflictFixes,
  preflightCreatorMergePresetImport,
  previewCreatorMergePresetImportDiff,
  applyCreatorMergePresetToposort,
  exportCreatorMergePresetPackages,
  importCreatorMergePresetPackages,
  publishCreatorMergePresetToFactory,
  pullCreatorFactoryMergePresetPackages,
} from '../api/index.js';

function formatHistoryTime(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleString('zh-CN', { hour12: false });
  } catch {
    return iso;
  }
}

/**
 * @param {
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
 * } deps
 */
export function useCreatorSettings(deps) {
  const {
    uiProfile, overview, error, saveMessage, conflictMessage, handleSaveError, onAfterSettingsSave,
    globalOutlineEditorRef, globalOutlineText,
    isWorkspaceColumnVisible, workspaceTabsEnabled,
    logicCheckRunning, logicCheckResult, activeLogicCheckIssueIdx,
    runCompanionLogicCheck, handleLogicCheckIssueClick, onLogicCheckIssueKeydown,
  } = deps;

const settingsSaving = ref(false);
const settingsDocs = ref(null);
const pillarsText = ref('');
const settingsBaseline = ref({ pillars: '', outline: '' });
const settingsDiffPreview = ref(null);
const showSettingsDiff = ref(false);
const settingsRevisions = ref({ pillars: '', outline: '' });
const settingsHistory = ref([]);
const settingsRestoring = ref(false);
const usesGlobalMergeDefault = ref(false);
const mergePresetPackages = ref([]);
const selectedMergePresetPackage = ref('');
const showImportMergePresetPackages = ref(false);
const importMergePresetPackagesJson = ref('');
const mergePresetPackagesImporting = ref(false);
const mergePresetImportDiff = ref({ added: [], updated: [], removed: [] });
const mergePresetToposort = ref({ order: [], edges: [], edge_count: 0 });
const mergePresetChangelog = ref({ package_id: '', entry_count: 0, entries: [] });
const mergePresetChangelogDiff = ref({ change_count: 0, changes: [] });
const factoryMergePresetPullConflicts = ref({ conflict_count: 0, conflicts: [] });
const mergePresetImportPreflight = ref(null);
const mergePresetGraph = ref({ node_count: 0, edge_count: 0, nodes: [], edges: [] });
const mergePresetConflicts = ref({ conflict_count: 0, conflicts: [] });
const mergePresetConflictFixes = ref({ fix_count: 0, fixes: [] });
const mergePresetFactoryPublishing = ref(false);
const mergePresetFactoryPulling = ref(false);
const factoryMergePresetPackages = ref([]);
const showImportMergePrefs = ref(false);
const importMergePrefsJson = ref('');
const mergePrefsImporting = ref(false);
const pillarsSnapshotId = ref('');
const outlineSnapshotId = ref('');
const compareSnapshotId = ref('');
const pillarsMergeSource = ref('editor');
const outlineMergeSource = ref('editor');
const mergeStrategyPreview = ref(null);

const settingsDiffSnippet = computed(() => {
  const preview = settingsDiffPreview.value;
  if (!preview) return [];
  const lines = [];
  if (preview.pillars?.snippet?.length) lines.push(...preview.pillars.snippet);
  if (preview.global_outline?.snippet?.length) lines.push(...preview.global_outline.snippet);
  return lines.slice(0, 12);
});

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

function bindGlobalOutlineEditorRef(el) {
  globalOutlineEditorRef.value = el;
}

function formatMergePresetOption(pkg) {
  if (pkg.version_label) {
    const prefix = pkg.version_semver_valid === false ? '!' : '';
    return `${prefix}[${pkg.version_label}] ${pkg.name}`;
  }
  return pkg.name;
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

async function exportMergePresetPackages() {
  error.value = null;
  try {
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
    await importCreatorMergePresetPackages(payload);
    importMergePresetPackagesJson.value = '';
    showImportMergePresetPackages.value = false;
    mergePresetImportPreflight.value = null;
    await loadMergePresetPackages();
    saveMessage.value = '已导入合并策略预设包';
  } catch (e) {
    handleSaveError(e);
  } finally {
    mergePresetPackagesImporting.value = false;
  }
}

async function loadMergePresetPackages() {
  try {
    const data = await fetchCreatorMergePresetPackages();
    mergePresetPackages.value = data.packages || [];
    const factoryData = await fetchCreatorFactoryMergePresetPackages();
    factoryMergePresetPackages.value = factoryData.packages || [];
    const graph = await fetchCreatorMergePresetGraph();
    mergePresetGraph.value = graph;
    const conflicts = await fetchCreatorMergePresetConflicts();
    mergePresetConflicts.value = conflicts;
    const fixes = await fetchCreatorMergePresetConflictFixes();
    mergePresetConflictFixes.value = fixes;
    const topo = await fetchCreatorMergePresetToposort();
    mergePresetToposort.value = topo;
    if (selectedMergePresetPackage.value) {
      const changelog = await fetchCreatorMergePresetChangelog(selectedMergePresetPackage.value);
      mergePresetChangelog.value = changelog;
    } else {
      mergePresetChangelog.value = { package_id: '', entry_count: 0, entries: [] };
    }
  } catch {
    mergePresetPackages.value = [];
    factoryMergePresetPackages.value = [];
    mergePresetGraph.value = { node_count: 0, edge_count: 0, nodes: [], edges: [] };
    mergePresetConflicts.value = { conflict_count: 0, conflicts: [] };
    mergePresetConflictFixes.value = { fix_count: 0, fixes: [] };
  }
}

async function applyMergePresetConflictFix(fix) {
  try {
    const result = await applyCreatorMergePresetConflictFix({
      package_id: fix.package_id,
      action: fix.action,
      dependency_id: fix.dependency_id,
      version_label: fix.version_label,
    });
    saveMessage.value = `已应用修复，剩余冲突 ${result.conflict_count}`;
    await loadMergePresetPackages();
  } catch (e) {
    handleSaveError(e);
  }
}

async function applyAllMergePresetConflictFixes() {
  try {
    const result = await applyAllCreatorMergePresetConflictFixes();
    saveMessage.value = `已批量应用 ${result.applied} 项，剩余冲突 ${result.conflict_count}`;
    await loadMergePresetPackages();
  } catch (e) {
    handleSaveError(e);
  }
}

async function previewMergePresetImportDiff() {
  try {
    const payload = JSON.parse(importMergePresetPackagesJson.value);
    mergePresetImportDiff.value = await previewCreatorMergePresetImportDiff(payload);
    saveMessage.value = `diff：新增 ${mergePresetImportDiff.value.added?.length || 0}，更新 ${mergePresetImportDiff.value.updated?.length || 0}`;
  } catch (e) {
    handleSaveError(e);
  }
}

async function applyMergePresetToposort() {
  try {
    const result = await applyCreatorMergePresetToposort();
    saveMessage.value = `已拓扑重排 ${result.reordered} 个预设包`;
    await loadMergePresetPackages();
  } catch (e) {
    handleSaveError(e);
  }
}

async function preflightMergePresetImport() {
  try {
    const payload = JSON.parse(importMergePresetPackagesJson.value);
    const result = await preflightCreatorMergePresetImport(payload);
    mergePresetImportPreflight.value = result;
    saveMessage.value = result.blocked
      ? `预检发现 ${result.conflict_count} 个冲突，导入已阻断`
      : `预检通过，可导入 ${result.would_import} 个包`;
  } catch (e) {
    handleSaveError(e);
  }
}

async function publishMergePresetToFactory() {
  if (!selectedProjectMergePreset.value) return;
  mergePresetFactoryPublishing.value = true;
  error.value = null;
  try {
    await publishCreatorMergePresetToFactory({ package_id: selectedMergePresetPackage.value });
    saveMessage.value = '已发布预设包到工厂库';
    await loadMergePresetPackages();
  } catch (e) {
    handleSaveError(e);
  } finally {
    mergePresetFactoryPublishing.value = false;
  }
}

async function pullFactoryMergePresets() {
  const ids = mergePresetPackages.value.filter((pkg) => pkg.scope === 'factory').map((pkg) => pkg.id);
  const fallback = factoryMergePresetPackages.value.map((pkg) => pkg.id);
  const packageIds = ids.length ? ids : fallback;
  if (!packageIds.length) return;
  mergePresetFactoryPulling.value = true;
  error.value = null;
  factoryMergePresetPullConflicts.value = { conflict_count: 0, conflicts: [] };
  try {
    const preflight = await preflightCreatorFactoryMergePresetPull({ package_ids: packageIds });
    if (preflight.conflict_count) {
      factoryMergePresetPullConflicts.value = preflight;
      saveMessage.value = `工厂拉取预检发现 ${preflight.conflict_count} 个冲突，请选择策略`;
      return;
    }
    const result = await pullCreatorFactoryMergePresetPackages({ package_ids: packageIds });
    saveMessage.value = `已从工厂库拉取 ${result.imported} 个预设包`;
    await loadMergePresetPackages();
  } catch (e) {
    handleSaveError(e);
  } finally {
    mergePresetFactoryPulling.value = false;
  }
}

async function pullFactoryMergePresetsWithStrategy(packageId, strategy) {
  const ids = factoryMergePresetPackages.value.map((pkg) => pkg.id);
  if (!ids.length) return;
  mergePresetFactoryPulling.value = true;
  error.value = null;
  try {
    const result = await pullCreatorFactoryMergePresetPackages({
      package_ids: ids,
      conflict_strategies: { [packageId]: strategy },
    });
    saveMessage.value = `拉取完成：导入 ${result.imported}，跳过 ${result.skipped || 0}`;
    factoryMergePresetPullConflicts.value = { conflict_count: 0, conflicts: [] };
    await loadMergePresetPackages();
  } catch (e) {
    handleSaveError(e);
  } finally {
    mergePresetFactoryPulling.value = false;
  }
}

async function previewMergePresetChangelogDiff(entryIndex) {
  if (!selectedMergePresetPackage.value) return;
  try {
    mergePresetChangelogDiff.value = await fetchCreatorMergePresetChangelogDiff(
      selectedMergePresetPackage.value,
      entryIndex,
    );
    saveMessage.value = `变更 diff：${mergePresetChangelogDiff.value.change_count} 项`;
  } catch (e) {
    handleSaveError(e);
  }
}

async function loadMergePreferences() {
  try {
    const prefs = await fetchCreatorMergePreferences();
    pillarsMergeSource.value = prefs.pillars_merge_source || 'editor';
    outlineMergeSource.value = prefs.global_outline_merge_source || 'editor';
    if (prefs.merge_snapshot_id) {
      const known = settingsHistory.value.some((s) => s.id === prefs.merge_snapshot_id);
      if (known) compareSnapshotId.value = prefs.merge_snapshot_id;
    }
    const pillarsSnap = prefs.pillars_merge_snapshot_id || prefs.merge_snapshot_id;
    const outlineSnap = prefs.global_outline_merge_snapshot_id || prefs.merge_snapshot_id;
    if (pillarsSnap && settingsHistory.value.some((s) => s.id === pillarsSnap)) {
      pillarsSnapshotId.value = pillarsSnap;
    }
    if (outlineSnap && settingsHistory.value.some((s) => s.id === outlineSnap)) {
      outlineSnapshotId.value = outlineSnap;
    }
    usesGlobalMergeDefault.value = Boolean(prefs.uses_global_default);
  } catch {
    /* optional */
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
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    mergePrefsImporting.value = false;
  }
}

async function loadSettingsHistory() {
  try {
    const data = await fetchCreatorSettingsHistory();
    settingsHistory.value = data.snapshots || [];
    if (settingsHistory.value.length && !compareSnapshotId.value) {
      compareSnapshotId.value = settingsHistory.value[0].id;
    }
  } catch {
    settingsHistory.value = [];
  }
}

async function restoreSettingsHistory(snapshotId) {
  settingsRestoring.value = true;
  error.value = null;
  try {
    const docs = await restoreCreatorSettingsSnapshot(snapshotId);
    settingsDocs.value = docs;
    pillarsText.value = docs.pillars_text || '';
    globalOutlineText.value = docs.global_outline_text || '';
    settingsBaseline.value = {
      pillars: docs.pillars_text || '',
      outline: docs.global_outline_text || '',
    };
    settingsRevisions.value = {
      pillars: docs.pillars_revision || '',
      outline: docs.global_outline_revision || '',
    };
    saveMessage.value = '已从历史版本恢复设定';
    conflictMessage.value = '';
    await loadSettingsHistory();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    settingsRestoring.value = false;
  }
}

async function loadSettingsDocs() {
  const docs = await fetchCreatorSettingsDocs();
  settingsDocs.value = docs;
  pillarsText.value = docs.pillars_text || '';
  globalOutlineText.value = docs.global_outline_text || '';
  settingsBaseline.value = {
    pillars: docs.pillars_text || '',
    outline: docs.global_outline_text || '',
  };
  settingsRevisions.value = {
    pillars: docs.pillars_revision || '',
    outline: docs.global_outline_revision || '',
  };
  settingsDiffPreview.value = null;
  showSettingsDiff.value = false;
}

function cancelSettingsDiff() {
  showSettingsDiff.value = false;
  settingsDiffPreview.value = null;
}

async function refreshMergeStrategyPreview() {
  if (!showMergeStrategy.value) {
    mergeStrategyPreview.value = null;
    return;
  }
  try {
    mergeStrategyPreview.value = await previewCreatorSettingsMerge({
      pillars_text: pillarsText.value,
      global_outline_text: globalOutlineText.value,
      pillars_merge_source: pillarsMergeSource.value,
      global_outline_merge_source: outlineMergeSource.value,
      snapshot_id: compareSnapshotId.value || undefined,
      pillars_merge_snapshot_id: pillarsSnapshotId.value || compareSnapshotId.value || undefined,
      global_outline_merge_snapshot_id: outlineSnapshotId.value || compareSnapshotId.value || undefined,
    });
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}

async function refreshThreeWayPreview() {
  if (!showSettingsDiff.value) return;
  try {
    settingsDiffPreview.value = await previewCreatorSettingsThreeWay({
      pillars_text: pillarsText.value,
      global_outline_text: globalOutlineText.value,
      snapshot_id: compareSnapshotId.value || undefined,
    });
    await refreshMergeStrategyPreview();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}

async function requestSaveSettings() {
  error.value = null;
  if (
    pillarsText.value === settingsBaseline.value.pillars
    && globalOutlineText.value === settingsBaseline.value.outline
  ) {
    saveMessage.value = '设定无变更';
    return;
  }
  try {
    if (settingsHistory.value.length) {
      settingsDiffPreview.value = await previewCreatorSettingsThreeWay({
        pillars_text: pillarsText.value,
        global_outline_text: globalOutlineText.value,
        snapshot_id: compareSnapshotId.value || undefined,
      });
    } else {
      settingsDiffPreview.value = await previewCreatorSettingsDocs({
        pillars_text: pillarsText.value,
        global_outline_text: globalOutlineText.value,
      });
    }
    showSettingsDiff.value = true;
    await refreshMergeStrategyPreview();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}

async function confirmSaveSettings() {
  settingsSaving.value = true;
  saveMessage.value = '';
  error.value = null;
  try {
    const body = {
      pillars_text: pillarsText.value,
      global_outline_text: globalOutlineText.value,
      expected_pillars_revision: settingsRevisions.value.pillars,
      expected_global_outline_revision: settingsRevisions.value.outline,
    };
    if (showMergeStrategy.value) {
      body.pillars_merge_source = pillarsMergeSource.value;
      body.global_outline_merge_source = outlineMergeSource.value;
      body.merge_snapshot_id = compareSnapshotId.value || undefined;
      body.pillars_merge_snapshot_id = pillarsSnapshotId.value || compareSnapshotId.value || undefined;
      body.global_outline_merge_snapshot_id = outlineSnapshotId.value || compareSnapshotId.value || undefined;
    }
    await saveCreatorSettingsDocs(body);
    saveMessage.value = '设定已保存';
    conflictMessage.value = '';
    showSettingsDiff.value = false;
    settingsDiffPreview.value = null;
    mergeStrategyPreview.value = null;
    await onAfterSettingsSave();
  } catch (e) {
    handleSaveError(e);
  } finally {
    settingsSaving.value = false;
  }
}

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

const panelContext = {
  uiProfile,
  overview,
  isWorkspaceColumnVisible,
  pillarsText,
  globalOutlineText,
  settingsDocs,
  settingsSaving,
  requestSaveSettings,
  showSettingsDiff,
  settingsDiffPreview,
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
  mergePresetToposort,
  mergePresetChangelog,
  previewMergePresetChangelogDiff,
  mergePresetChangelogDiff,
  factoryMergePresetPullConflicts,
  pullFactoryMergePresetsWithStrategy,
  mergePresetGraph,
  mergePresetConflicts,
  mergePresetConflictFixes,
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
  loadSettingsDocs,
  loadSettingsHistory,
  loadMergePreferences,
  loadMergePresetPackages,
};
}
