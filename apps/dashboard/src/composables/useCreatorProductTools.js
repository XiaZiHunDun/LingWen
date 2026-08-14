/**
 * useCreatorProductTools — 创作偏好、导出、发布向导、介入摘要
 *
 * Phase 19 Task 1: 抽出 useProductExport + useProductPublish 两个子模块（无循环依赖），
 * 本主 hook 改为组合 facade。下游 API（panelContext shape）保持完全兼容，
 * 22+ 处 import 无需修改。
 *
 * 子模块：
 * - useProductExport       (导出向导 + Markdown/EPUB/DOCX)
 * - useProductPublish      (发布向导 + 历史 + 平台)
 *
 * 暂未抽出的（保留内联，避免循环依赖）：
 * - useProductPreferences  (创作偏好/模型同步 — 与 memory 双向依赖)
 * - useProductMemory       (记忆资产/搜索/标注 — 与 preferences 双向依赖)
 *   → 后续 Task 1.5 / Task 1.6 单独 PR 渐进接入
 */
import { computed, ref, watch } from 'vue';
import {
  fetchCreatorPreferences,
  saveCreatorPreferencesApi,
  fetchCreatorMemoryAssets,
  saveCreatorMemoryAnnotation,
  queryCreatorMemory,
  fetchCreatorModels,
} from '../api/index.js';
import {
  loadCreatorPreferences,
  saveCreatorPreferences,
  defaultCreatorPreferences,
  CREATOR_MODEL_OPTIONS,
} from '../utils/creatorPreferencesStorage.js';
import { preferencesFromApi, preferencesToApi } from '../utils/creatorPreferencesApi.js';
import { buildMemoryAssetItems } from '../utils/creatorMemoryAssetsUtils.js';
import { buildStructureGraph } from '../utils/creatorStructureGraphUtils.js';
import { highlightMemorySnippet, formatMemoryCitation } from '../utils/creatorMemoryHighlightUtils.js';
import { buildCreatorPreferencesSummary } from '../utils/creatorPreferencesSummaryUtils.js';
import { useStudioProject } from './useStudioProject.js';
import {
  useProductExport,
  useProductPublish,
} from './useCreatorProductTools/index.ts';

export { CREATOR_PUBLISH_PLATFORMS } from './useCreatorProductTools/useProductPublish.ts';

/**
 * @param {{
 *   overview: import('vue').Ref<object|null>,
 *   error: import('vue').Ref<string|null>,
 *   saveMessage: import('vue').Ref<string>,
 *   visibleDeviations: import('vue').ComputedRef<object[]>,
 *   editableVolumes: import('vue').Ref<object[]>,
 *   pillarsText: import('vue').Ref<string>,
 *   globalOutlineText: import('vue').Ref<string>,
 *   logicCheckResult: import('vue').Ref<object|null>,
 *   batchJob: import('vue').Ref<object|null>,
 *   batchRunning: import('vue').Ref<boolean>,
 *   isWorkspaceColumnVisible: (col: string) => boolean,
 *   isDeskDrawerColumn?: (col: string) => boolean,
 *   closeDeskDrawer?: () => void,
 *   setWorkspaceTab: (tab: string) => void,
 *   jumpToChapter: (chapter: number) => Promise<void>,
 *   navigateTo: (page: string, opts?: object) => void,
 *   settingsHasUnsavedChanges?: import('vue').ComputedRef<boolean>,
 * }} deps
 */
export function useCreatorProductTools(deps) {
  const {
    overview,
    error,
    saveMessage,
    visibleDeviations,
    editableVolumes,
    pillarsText,
    globalOutlineText,
    logicCheckResult,
    batchJob,
    batchRunning,
    isWorkspaceColumnVisible,
    isDeskDrawerColumn = () => false,
    closeDeskDrawer = () => {},
    setWorkspaceTab,
    jumpToChapter,
    navigateTo,
    settingsHasUnsavedChanges,
  } = deps;

  const { activeSlug: activeSlugRef } = useStudioProject();
  const activeSlug = activeSlugRef ?? ref(null);

  // --- Preferences 内联（与 memory 双向依赖，单独 PR 处理）---
  const preferences = ref(loadCreatorPreferences());
  const preferencesDirty = ref(false);
  const preferencesSavedHint = ref('');
  const preferencesSyncSource = ref('local');
  const creatorModelOptions = ref([...CREATOR_MODEL_OPTIONS]);

  // --- Memory 内联（与 preferences 双向依赖，单独 PR 处理）---
  const memoryAssetsPayload = ref(null);
  const memoryAssetsLoading = ref(false);
  const memoryAssetsLoadedOnce = ref(false);
  const memoryFilter = ref('all');
  const memoryFocusAssetId = ref(null);
  const memorySearchQuery = ref('');
  const memorySearchScope = ref('all');
  const memorySearchResults = ref([]);
  const memorySearchBusy = ref(false);
  const memorySearchRan = ref(false);
  const memorySearchUsedFallback = ref(false);
  const memoryAnnotationSaving = ref(null);
  const structureGraphView = ref('tree');

  // --- Export 子模块（Phase 19 Task 1 抽出）---
  const exporter = useProductExport({
    overview,
    error,
    saveMessage,
    pillarsText,
    globalOutlineText,
    activeSlug,
  });

  // --- Publish 子模块（依赖 exporter）---
  const publisher = useProductPublish({
    exportIntro: exporter.exportIntro,
    exportDescription: exporter.exportDescription,
    buildExportMarkdown: exporter.buildExportMarkdown,
    resolveExportChapterNums: exporter.resolveExportChapterNums,
    setExportMode: exporter.setExportMode,
    error,
    saveMessage,
  });

  // --- 跨切 computeds ---
  const memoryAssets = computed(() => {
    if (memoryAssetsPayload.value?.items?.length) {
      return memoryAssetsPayload.value.items;
    }
    return buildMemoryAssetItems({
      overview: overview.value,
      pillarsText: pillarsText.value,
      outlineText: globalOutlineText.value,
    });
  });

  const memoryAssetsFiltered = computed(() => {
    const filter = memoryFilter.value;
    if (filter === 'all') return memoryAssets.value;
    return memoryAssets.value.filter((item) => item.kind === filter);
  });

  const memoryAvailable = computed(() => Boolean(memoryAssetsPayload.value?.memory_available));
  const memoryRagEnabled = computed(
    () => memoryAssetsPayload.value?.memory_rag_enabled ?? preferences.value.memoryRagEnabled,
  );

  const preferencesSummary = computed(() => buildCreatorPreferencesSummary(
    preferences.value,
    {
      memoryRagEnabled: memoryRagEnabled.value,
      modelOptions: creatorModelOptions.value,
    },
  ));

  /** @param {string} ruleId */
  function interventionRuleEnabled(ruleId) {
    return preferences.value.interventionRules?.[ruleId] !== false;
  }

  const structureGraph = computed(() => buildStructureGraph({
    overview: overview.value,
    volumes: editableVolumes.value,
    deviations: visibleDeviations.value,
  }));

  const interventionItems = computed(() => {
    const items = [];
    const alerts = visibleDeviations.value.filter((d) => d.severity === 'alert');
    if (interventionRuleEnabled('deviationAlerts') && alerts.length) {
      items.push({
        id: 'deviation-alerts',
        kind: 'deviation',
        title: `${alerts.length} 处需关注偏离`,
        detail: alerts[0].message || '点击查看脉络详情',
        action: 'pulse',
        chapter: alerts[0].chapter,
      });
    }
    if (interventionRuleEnabled('batchProgress') && (batchRunning.value || batchJob.value?.status === 'running')) {
      items.push({
        id: 'batch-running',
        kind: 'batch',
        title: '批量推进进行中',
        detail: batchJob.value?.message || '可在脉络栏查看进度',
        action: 'pulse',
      });
    }
    const issues = logicCheckResult.value?.issues || [];
    const p0 = issues.filter((i) => i.severity === 'P0' || i.priority === 'P0');
    if (interventionRuleEnabled('logicP0') && p0.length) {
      items.push({
        id: 'logic-p0',
        kind: 'logic',
        title: `${p0.length} 条 P0 逻辑问题`,
        detail: p0[0].message || '请在写栏处理',
        action: 'write',
        chapter: logicCheckResult.value?.chapter,
      });
    }
    if (interventionRuleEnabled('settingsUnsaved') && settingsHasUnsavedChanges?.value) {
      items.push({
        id: 'settings-unsaved',
        kind: 'settings',
        title: '设定尚未保存',
        detail: '支柱或全局大纲有未保存的修改',
        action: 'settings',
      });
    }
    if (interventionRuleEnabled('preferencesUnsaved') && preferencesDirty.value) {
      items.push({
        id: 'preferences-unsaved',
        kind: 'preferences',
        title: '创作偏好尚未保存',
        detail: '模型或记忆检索设置已改但未同步',
        action: 'settings',
      });
    }
    if (
      interventionRuleEnabled('memoryOffline')
      && memoryAssetsLoadedOnce.value
      && !memoryAssetsLoading.value
      && memoryRagEnabled.value
      && !memoryAvailable.value
    ) {
      items.push({
        id: 'memory-offline',
        kind: 'memory',
        title: '记忆系统离线',
        detail: 'RAG 已开启但记忆网关不可用，搜索将降级为本地匹配',
        action: 'memory',
      });
    }
    if (
      interventionRuleEnabled('emptyWriteHint')
      && !items.length
      && overview.value?.chapters_written === 0
      && overview.value?.creation_mode !== 'companion'
      && overview.value?.creation_mode !== 'advance'
    ) {
      items.push({
        id: 'onboarding-write',
        kind: 'hint',
        title: '尚未开始写作',
        detail: '从写栏选择章节或运行入门向导',
        action: 'write',
      });
    }
    return items;
  });

  // --- 偏好/模型 actions (内联) ---
  async function loadCreatorModels() {
    try {
      const data = await fetchCreatorModels();
      if (data.models?.length) {
        creatorModelOptions.value = data.models;
      }
    } catch {
      creatorModelOptions.value = [...CREATOR_MODEL_OPTIONS];
    }
  }

  async function loadPreferencesFromServer() {
    try {
      const data = await fetchCreatorPreferences();
      preferences.value = preferencesFromApi(data);
      saveCreatorPreferences(preferences.value);
      preferencesSyncSource.value = 'server';
      preferencesDirty.value = false;
    } catch {
      preferences.value = loadCreatorPreferences();
      preferencesSyncSource.value = 'local';
    }
  }

  function markPreferencesDirty() {
    preferencesDirty.value = true;
    preferencesSavedHint.value = '';
  }

  function resetPreferences() {
    preferences.value = defaultCreatorPreferences();
    preferencesDirty.value = true;
    preferencesSavedHint.value = '';
  }

  async function savePreferences() {
    saveCreatorPreferences(preferences.value);
    try {
      await saveCreatorPreferencesApi(preferencesToApi(preferences.value));
      preferencesSyncSource.value = 'server';
      preferencesSavedHint.value = '偏好已同步到项目';
      saveMessage.value = '创作偏好已保存';
    } catch (e) {
      preferencesSyncSource.value = 'local';
      preferencesSavedHint.value = '已保存到本机（服务器暂不可用）';
      saveMessage.value = '创作偏好已保存到本机';
      error.value = e instanceof Error ? e.message : String(e);
    }
    preferencesDirty.value = false;
  }

  // --- Memory actions (内联) ---
  async function loadMemoryAssets() {
    memoryAssetsLoading.value = true;
    try {
      memoryAssetsPayload.value = await fetchCreatorMemoryAssets();
    } catch {
      memoryAssetsPayload.value = null;
    } finally {
      memoryAssetsLoading.value = false;
      memoryAssetsLoadedOnce.value = true;
    }
  }

  async function runMemorySearch() {
    const q = memorySearchQuery.value.trim();
    if (!q) return;
    memorySearchBusy.value = true;
    memorySearchRan.value = false;
    try {
      const data = await queryCreatorMemory({
        query: q,
        scope: memorySearchScope.value,
        top_k: preferences.value.memoryRagTopK,
      });
      memorySearchResults.value = data.results || [];
      memorySearchUsedFallback.value = Boolean(data.used_fallback);
      memorySearchRan.value = true;
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
      memorySearchResults.value = [];
      memorySearchRan.value = true;
    } finally {
      memorySearchBusy.value = false;
    }
  }

  async function saveMemoryAnnotation(assetId, patch) {
    memoryAnnotationSaving.value = assetId;
    try {
      await saveCreatorMemoryAnnotation(assetId, patch);
      await loadMemoryAssets();
      saveMessage.value = '记忆备注已保存';
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      memoryAnnotationSaving.value = null;
    }
  }

  async function toggleMemoryPin(item) {
    if (!item?.id || item.placeholder) return;
    await saveMemoryAnnotation(item.id, { pinned: !item.pinned });
  }

  async function saveMemoryNote(item, note) {
    if (!item?.id || item.placeholder) return;
    await saveMemoryAnnotation(item.id, { note });
  }

  // --- Intervention / 导航 actions (内联) ---
  async function handleInterventionAction(item) {
    if (!item) return;
    if (item.action === 'pulse') {
      setWorkspaceTab('pulse');
      if (item.chapter) await jumpToChapter(item.chapter);
      return;
    }
    if (item.action === 'write') {
      setWorkspaceTab('write');
      if (item.chapter) await jumpToChapter(item.chapter);
      return;
    }
    if (item.action === 'memory') {
      setWorkspaceTab('memory');
      return;
    }
    if (item.action === 'settings') {
      setWorkspaceTab('settings');
      return;
    }
    if (item.action === 'decisions') {
      navigateTo('decisions', { clearFocus: true });
    }
  }

  function goToSettingsForAsset(item) {
    if (item?.editable) {
      setWorkspaceTab('settings');
    }
  }

  function focusMemoryEntity(entity) {
    if (!entity) {
      memoryFocusAssetId.value = null;
      setWorkspaceTab('memory');
      return;
    }
    memoryFocusAssetId.value = entity.id || null;
    const kind = entity.kind;
    memoryFilter.value = kind === 'foreshadow' ? 'foreshadow' : kind === 'character' ? 'character' : 'all';
    memorySearchQuery.value = (entity.name || '').replace(/^伏笔：/, '').trim();
    setWorkspaceTab('memory');
  }

  // --- panelContext 聚合 ---
  const panelContext = {
    // Preferences
    preferences,
    preferencesDirty,
    preferencesSummary,
    creatorModelOptions,
    loadCreatorModels,
    preferencesSavedHint,
    preferencesSyncSource,
    markPreferencesDirty,
    resetPreferences,
    savePreferences,
    loadPreferencesFromServer,
    // Memory
    memoryAssets,
    memoryAssetsFiltered,
    memoryAssetsLoading,
    memoryFilter,
    memoryFocusAssetId,
    memoryAvailable,
    memoryRagEnabled,
    loadMemoryAssets,
    saveMemoryAnnotation,
    toggleMemoryPin,
    saveMemoryNote,
    memoryAnnotationSaving,
    runMemorySearch,
    structureGraph,
    structureGraphView,
    isWorkspaceColumnVisible,
    deskDrawerActive: () => isDeskDrawerColumn('memory'),
    closeDeskDrawer,
    memorySearchQuery,
    memorySearchScope,
    memorySearchResults,
    memorySearchBusy,
    memorySearchRan,
    memorySearchUsedFallback,
    highlightMemorySnippet,
    formatMemoryCitation,
    // Export (子模块)
    exportModalOpen: exporter.exportModalOpen,
    exportMode: exporter.exportMode,
    exportRangeStart: exporter.exportRangeStart,
    exportRangeEnd: exporter.exportRangeEnd,
    exportIntro: exporter.exportIntro,
    exportAuthor: exporter.exportAuthor,
    exportDescription: exporter.exportDescription,
    exportSubmissionSampleCount: exporter.exportSubmissionSampleCount,
    exportBusy: exporter.exportBusy,
    exportPreview: exporter.exportPreview,
    openExportModal: exporter.openExportModal,
    closeExportModal: exporter.closeExportModal,
    refreshExportPreview: exporter.refreshExportPreview,
    runExportDownload: exporter.runExportDownload,
    runExportEpub: exporter.runExportEpub,
    runExportDocx: exporter.runExportDocx,
    // Publish (子模块)
    publishModalOpen: publisher.publishModalOpen,
    publishStep: publisher.publishStep,
    publishPlatform: publisher.publishPlatform,
    publishIncludeOutline: publisher.publishIncludeOutline,
    publishIntro: publisher.publishIntro,
    publishStatus: publisher.publishStatus,
    publishMessage: publisher.publishMessage,
    publishHistory: publisher.publishHistory,
    publishPlatforms: publisher.publishPlatforms,
    publishHistoryModalOpen: publisher.publishHistoryModalOpen,
    publishPackPreview: publisher.publishPackPreview,
    publishPackBusy: publisher.publishPackBusy,
    publishSubmissionChapters: publisher.publishSubmissionChapters,
    activePublishPlatform: publisher.activePublishPlatform,
    openPublishWizard: publisher.openPublishWizard,
    closePublishWizard: publisher.closePublishWizard,
    openPublishHistoryModal: publisher.openPublishHistoryModal,
    closePublishHistoryModal: publisher.closePublishHistoryModal,
    prefillPublishFromSubmission: publisher.prefillPublishFromSubmission,
    nextPublishStep: publisher.nextPublishStep,
    prevPublishStep: publisher.prevPublishStep,
    submitPublish: publisher.submitPublish,
    loadPublishHistory: publisher.loadPublishHistory,
    loadPublishPlatforms: publisher.loadPublishPlatforms,
    // Intervention / Navigation
    interventionItems,
    handleInterventionAction,
    goToSettingsForAsset,
    jumpToChapter,
    setWorkspaceTab,
    focusMemoryEntity,
  };

  return {
    panelContext,
    loadPreferencesFromServer,
    loadMemoryAssets,
    loadCreatorModels,
  };
}