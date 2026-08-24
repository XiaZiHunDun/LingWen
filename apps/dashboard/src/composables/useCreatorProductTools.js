/**
 * useCreatorProductTools — 创作偏好、导出、发布向导、介入摘要
 *
 * Phase 19 Task 1 完成版：抽出全部 4 个 .ts 子模块，本主 hook 改为组合 facade。
 * 下游 API（panelContext shape）保持完全兼容，22+ 处 import 无需修改。
 *
 * 子模块：
 * - useProductPreferences  (创作偏好/模型同步)
 * - useProductMemory       (记忆资产/搜索/标注/导航动作)
 * - useProductExport       (导出向导 + Markdown/EPUB/DOCX)
 * - useProductPublish      (发布向导 + 历史 + 平台)
 *
 * 跨子模块 computeds（避免循环依赖，由主 hook 组合）：
 * - memoryRagEnabled       = payload.memory_rag_enabled ?? preferences.memoryRagEnabled
 * - preferencesSummary     = buildSummary(prefs, { memoryRagEnabled, modelOptions })
 * - interventionItems      = 聚合 + 偏好规则
 */
import { computed, ref } from 'vue';
import { highlightMemorySnippet, formatMemoryCitation } from '../utils/creatorMemoryHighlightUtils.js';
import { buildCreatorPreferencesSummary } from '../utils/creatorPreferencesSummaryUtils.js';
import { useStudioProject } from './useStudioProject.js';
import {
  useProductPreferences,
  useProductMemory,
  useProductExport,
  useProductPublish,
} from './useCreatorProductTools/index.ts';

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

  // --- 1) Preferences 子模块 ---
  const preferencesApi = useProductPreferences({
    error,
    saveMessage,
  });

  // --- 2) Memory 子模块（依赖 preferences.preferences.memoryRagTopK） ---
  // 注意: 必须先建 preferences，再建 memory（memory 读 memoryRagTopK）
  const memoryRagTopK = computed(() => preferencesApi.preferences.value.memoryRagTopK);

  const memory = useProductMemory({
    overview,
    editableVolumes,
    visibleDeviations,
    pillarsText,
    globalOutlineText,
    error,
    saveMessage,
    memoryRagTopK,
    setWorkspaceTab,
    jumpToChapter,
    navigateTo,
  });

  // --- 3) Export 子模块 ---
  const exporter = useProductExport({
    overview,
    error,
    saveMessage,
    pillarsText,
    globalOutlineText,
    activeSlug,
  });

  // --- 4) Publish 子模块（依赖 exporter）---
  const publisher = useProductPublish({
    exportIntro: exporter.exportIntro,
    exportDescription: exporter.exportDescription,
    buildExportMarkdown: exporter.buildExportMarkdown,
    resolveExportChapterNums: exporter.resolveExportChapterNums,
    setExportMode: exporter.setExportMode,
    error,
    saveMessage,
  });

  // --- 跨切 computeds（主 hook 组合）---

  // memoryRagEnabled = payload ?? preferences
  const memoryRagEnabled = computed(() => {
    const payload = memory.memoryAssetsPayload.value;
    return payload?.memory_rag_enabled ?? Boolean(preferencesApi.preferences.value.memoryRagEnabled);
  });

  // preferencesSummary
  const preferencesSummary = computed(() => buildCreatorPreferencesSummary(
    preferencesApi.preferences.value,
    {
      memoryRagEnabled: memoryRagEnabled.value,
      modelOptions: preferencesApi.creatorModelOptions.value,
    },
  ));

  // interventionRuleEnabled helper
  /** @param {string} ruleId */
  function interventionRuleEnabled(ruleId) {
    const rules = preferencesApi.preferences.value.interventionRules;
    return rules?.[ruleId] !== false;
  }

  // interventionItems
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
    if (interventionRuleEnabled('preferencesUnsaved') && preferencesApi.preferencesDirty.value) {
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
      && memory.memoryAssetsLoadedOnce.value
      && !memory.memoryAssetsLoading.value
      && memoryRagEnabled.value
      && !memory.memoryAvailable.value
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

  // --- panelContext 聚合（保持原 shape）---
  const panelContext = {
    // Preferences
    preferences: preferencesApi.preferences,
    preferencesDirty: preferencesApi.preferencesDirty,
    preferencesSummary,
    creatorModelOptions: preferencesApi.creatorModelOptions,
    loadCreatorModels: preferencesApi.loadCreatorModels,
    preferencesSavedHint: preferencesApi.preferencesSavedHint,
    preferencesSyncSource: preferencesApi.preferencesSyncSource,
    markPreferencesDirty: preferencesApi.markPreferencesDirty,
    resetPreferences: preferencesApi.resetPreferences,
    savePreferences: preferencesApi.savePreferences,
    loadPreferencesFromServer: preferencesApi.loadPreferencesFromServer,
    // Memory
    memoryAssets: memory.memoryAssets,
    memoryAssetsFiltered: memory.memoryAssetsFiltered,
    memoryAssetsLoading: memory.memoryAssetsLoading,
    memoryFilter: memory.memoryFilter,
    memoryFocusAssetId: memory.memoryFocusAssetId,
    memoryAvailable: memory.memoryAvailable,
    memoryRagEnabled,
    loadMemoryAssets: memory.loadMemoryAssets,
    saveMemoryAnnotation: memory.saveMemoryAnnotation,
    toggleMemoryPin: memory.toggleMemoryPin,
    saveMemoryNote: memory.saveMemoryNote,
    memoryAnnotationSaving: memory.memoryAnnotationSaving,
    runMemorySearch: memory.runMemorySearch,
    structureGraph: memory.structureGraph,
    structureGraphView: memory.structureGraphView,
    isWorkspaceColumnVisible,
    deskDrawerActive: () => isDeskDrawerColumn('memory'),
    closeDeskDrawer,
    memorySearchQuery: memory.memorySearchQuery,
    memorySearchScope: memory.memorySearchScope,
    memorySearchResults: memory.memorySearchResults,
    memorySearchBusy: memory.memorySearchBusy,
    memorySearchRan: memory.memorySearchRan,
    memorySearchUsedFallback: memory.memorySearchUsedFallback,
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
    handleInterventionAction: memory.handleInterventionAction,
    goToSettingsForAsset: memory.goToSettingsForAsset,
    jumpToChapter,
    setWorkspaceTab,
    focusMemoryEntity: memory.focusMemoryEntity,
  };

  return {
    panelContext,
    loadPreferencesFromServer: preferencesApi.loadPreferencesFromServer,
    loadMemoryAssets: memory.loadMemoryAssets,
    loadCreatorModels: preferencesApi.loadCreatorModels,
  };
}
