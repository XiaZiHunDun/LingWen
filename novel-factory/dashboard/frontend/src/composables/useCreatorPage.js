/**
 * useCreatorPage — 创作页 hub 编排、refresh 与 provide（从 CreatorPage 抽出）
 */
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { fetchCreatorOverview, runCreatorLogicCheck } from '../api/index.js';
import { creatorDefaultUiProfile } from './creatorDefaultUiProfile.js';
import { getModeUiProfileDefaults, isHumanFirstDeskMode } from '../config/creatorPanelMatrix.js';
import { useStudioProject } from './useStudioProject.js';
import { useDashboardNav } from './useDashboardNav.js';
import { useCreatorWorkspace } from './useCreatorWorkspace.js';
import { useCreatorVolumePlan } from './useCreatorVolumePlan.js';
import { useCreatorBatchHistory } from './useCreatorBatchHistory.js';
import { useCreatorModeGuide } from './useCreatorModeGuide.js';
import { useCreatorOnboarding } from './useCreatorOnboarding.js';
import { useCreatorSettings } from './useCreatorSettings.js';
import { useCreatorWrite } from './useCreatorWrite.js';
import { useCreatorPageHeader } from './useCreatorPageHeader.js';
import { useCreatorAdvanceBatch } from './useCreatorAdvanceBatch.js';
import { useCreatorPulse } from './useCreatorPulse.js';
import { createCreatorPageRefresh } from './useCreatorPageRefresh.js';
import { useCreatorPageProviders } from './useCreatorPageProviders.js';
import { useCreatorProductTools } from './useCreatorProductTools.js';

export function useCreatorPage() {
  const { projectRevision } = useStudioProject();
  const {
    focusWizard,
    focusWizardStep,
    focusWizardDone,
    focusWizardNotes,
    setWizardDeepLink,
    buildWizardShareUrl,
    navigateTo,
    focusCreatorWorkspace,
    setCreatorWorkspace,
    focusChapter,
  } = useDashboardNav();

  const overview = ref(null);
  const highlightedDeviationChapter = ref(null);
  const loading = ref(false);
  const saving = ref(false);
  const globalOutlineText = ref('');
  const globalOutlineEditorRef = ref(null);
  const conflictMessage = ref('');
  const error = ref(null);
  const saveMessage = ref('');
  const logicCheckRunning = ref(false);
  const logicCheckResult = ref(null);

  const uiProfile = computed(() => {
    const mode = overview.value?.creation_mode;
    const modeDefaults = mode ? getModeUiProfileDefaults(mode) : {};
    const serverProfile = overview.value?.ui_profile || {};
    const merged = { ...creatorDefaultUiProfile, ...modeDefaults, ...serverProfile };
    if (!isHumanFirstDeskMode(mode)) return merged;
    return {
      ...merged,
      creator_write_workbench: merged.creator_write_workbench !== false,
      chapter_inline_edit: true,
      chapter_outline_inline_edit: true,
      chapter_outline_read_preview: false,
      chapter_full_preview: false,
    };
  });

  const {
    modeLabel,
    creationModeBadgeHintText,
    modeBadgeHintEnabled,
    showCreationModeBadge,
    showPageTitle,
    showHeaderPreferences,
    showHeaderPublishExport,
    showHeaderRefresh,
    showHeaderActionsRow,
    displayDeviationBadge,
    displayDeviationCount,
    showCreationModeBadgeHint,
  } = useCreatorPageHeader({ uiProfile, overview, saveMessage });

  const {
    activeTab: workspaceActiveTab,
    tabsEnabled: workspaceTabsEnabled,
    workspaceTabs,
    workspacePrimaryTabs,
    workspaceSecondaryTabs,
    workspaceDrawerTabs,
    deskDrawerEnabled,
    deskDrawerPanel,
    deskDrawerOpen,
    isColumnVisible: isWorkspaceColumnVisible,
    isDeskDrawerColumn,
    openDeskDrawer,
    closeDeskDrawer,
    setWorkspaceTab,
    workspaceTabBadges,
    onDeviationBadgeClick,
  } = useCreatorWorkspace(uiProfile, overview, {
    focusCreatorWorkspace,
    setCreatorWorkspace,
    displayDeviationCount,
  });

  const deviationHighlightEnabled = computed(
    () => Boolean(
      uiProfile.value.deviation_list_highlight || uiProfile.value.deviation_click_highlight,
    ),
  );

  const visibleDeviations = computed(() => overview.value?.deviations || []);

  function isConflictError(err) {
    return err instanceof Error && err.message.includes('409');
  }

  function handleSaveError(err) {
    if (isConflictError(err)) {
      conflictMessage.value = '磁盘上的文件已被修改（可能在编辑器中），请重新加载后再保存。';
      error.value = null;
      return;
    }
    error.value = err instanceof Error ? err.message : String(err);
  }

  const onboardingHub = useCreatorOnboarding({
    uiProfile,
    overview,
    error,
    saveMessage,
    handleSaveError,
    focusWizard,
    focusWizardStep,
    focusWizardDone,
    focusWizardNotes,
    setWizardDeepLink,
    buildWizardShareUrl,
  });
  const {
    panelContext: onboardingPanelContext,
    wizardEmailTo,
    loadOnboardingWizard,
    syncWizardPanelOpen,
  } = onboardingHub;

  const refreshRef = { fn: async () => {} };
  const pulseRef = { hub: null };
  const writeRef = { hub: null };
  const batchCompletedRef = { fn: async () => {} };

  const advanceBatchHub = useCreatorAdvanceBatch({
    uiProfile,
    overview,
    saveMessage,
    error,
    navigateTo,
    onAfterBatchRefresh: async () => refreshRef.fn(),
    onBatchCompleted: (start, end) => batchCompletedRef.fn(start, end),
    loadBatchHistory: async () => loadBatchHistoryRef.fn(),
    setBatchSummaryPrompt: (prompt) => pulseRef.hub?.setBatchSummaryPrompt(prompt),
  });
  const {
    panelContext: advanceBatchPanelContext,
    batchStart,
    batchEnd,
    batchBudget,
    batchRunning,
    batchJob,
    pollBatchJob,
    resumeBatchPollingIfNeeded,
  } = advanceBatchHub;

  const loadBatchHistoryRef = { fn: async () => {} };

  const batchHistoryHub = useCreatorBatchHistory({
    uiProfile,
    batchStart,
    batchEnd,
    batchBudget,
    saveMessage,
    error,
  });
  const { panelContext: batchHistoryPanelContext, loadBatchHistory } = batchHistoryHub;
  loadBatchHistoryRef.fn = loadBatchHistory;

  const volumePlan = useCreatorVolumePlan({
    uiProfile,
    overview,
    saving,
    error,
    saveMessage,
    conflictMessage,
    globalOutlineEditorRef,
    globalOutlineText,
    batchStart,
    batchEnd,
    wizardEmailTo,
    handleSaveError,
    onAfterVolumePlanSave: async () => refreshRef.fn(),
  });
  const {
    panelContext: volumePlanPanelContext,
    editableVolumes,
    loadVolumePlan,
    loadVolumeTemplates,
    loadTemplateSyncSources,
    loadTemplateApprovals,
    loadDiffCollabNotes,
    refreshVolumePlanDiffPreview,
    tryLoadVolumePlanDiffShareLinkPreview,
  } = volumePlan;

  const modeGuideHub = useCreatorModeGuide({
    uiProfile,
    overview,
    saveMessage,
    onboardingWizard: onboardingHub.onboardingWizard,
    linkModeToOnboardingStep: onboardingHub.linkModeToOnboardingStep,
    modeLabel,
  });
  const { panelContext: modeGuidePanelContext, loadCreationModeSwitchHistory, onCreationModeSwitchHotkey } = modeGuideHub;

  async function runCompanionLogicCheck() {
    logicCheckRunning.value = true;
    error.value = null;
    try {
      logicCheckResult.value = await runCreatorLogicCheck();
      saveMessage.value = logicCheckResult.value.passed
        ? '逻辑审查通过'
        : `发现 ${logicCheckResult.value.p0_count} 条 P0`;
      await refresh();
    } catch (e) {
      handleSaveError(e);
    } finally {
      logicCheckRunning.value = false;
    }
  }

  const writeHub = useCreatorWrite({
    uiProfile,
    overview,
    error,
    saveMessage,
    handleSaveError,
    onAfterChapterSave: async () => refresh(),
    isWorkspaceColumnVisible,
    workspaceTabsEnabled,
    visibleDeviations,
    deviationHighlightEnabled,
    highlightedDeviationChapter,
    logicCheckRunning,
    logicCheckResult,
    runCompanionLogicCheck,
    openVolumeSummaryForRange: (...args) => pulseRef.hub?.openVolumeSummaryForRange(...args),
    focusChapter,
  });
  writeRef.hub = writeHub;
  const {
    panelContext: writePanelContext,
    maybeAutoSelectWritingChapter,
    activeLogicCheckIssueIdx,
    handleLogicCheckIssueClick,
    onLogicCheckIssueKeydown,
  } = writeHub;

  const pulseHub = useCreatorPulse({
    uiProfile,
    overview,
    error,
    saveMessage,
    workspaceTabsEnabled,
    isWorkspaceColumnVisible,
    isDeskDrawerColumn,
    closeDeskDrawer,
    setWorkspaceTab,
    editableVolumes,
    visibleDeviations,
    deviationHighlightEnabled,
    highlightedDeviationChapter,
    handleDeviationClick: (...args) => writeRef.hub.handleDeviationClick(...args),
    jumpToChapter: (...args) => writeRef.hub.jumpToChapter(...args),
    onAfterVolumeSummarySave: async () => refresh(),
    batchJob,
  });
  pulseRef.hub = pulseHub;
  const { panelContext: pulsePanelContext } = pulseHub;

  batchCompletedRef.fn = async (start, end) => {
    await pulseHub.onBatchCompleted(start, end);
    if (uiProfile.value.batch_scroll_deviation_list) {
      await writeHub.scrollToBatchDeviationList(start, end);
    }
    if (uiProfile.value.batch_open_first_deviation) {
      await writeHub.openFirstBatchDeviationChapter(start, end);
    }
    writeHub.updateBatchDeviationInlineSummary(start, end);
    await writeHub.linkBatchDeviationInlineSummary(start, end);
  };

  const settingsHub = useCreatorSettings({
    uiProfile,
    overview,
    error,
    saveMessage,
    conflictMessage,
    handleSaveError,
    onAfterSettingsSave: async () => refresh(),
    globalOutlineEditorRef,
    globalOutlineText,
    isWorkspaceColumnVisible,
    workspaceTabsEnabled,
    logicCheckRunning,
    logicCheckResult,
    activeLogicCheckIssueIdx,
    runCompanionLogicCheck,
    handleLogicCheckIssueClick,
    onLogicCheckIssueKeydown,
  });
  const { panelContext: settingsPanelContext, pillarsText, settingsHasUnsavedChanges, loadSettingsDocs, loadSettingsHistory, loadMergePreferences, loadMergePresetPackages } = settingsHub;

  const productToolsHub = useCreatorProductTools({
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
    isDeskDrawerColumn,
    closeDeskDrawer,
    setWorkspaceTab,
    jumpToChapter: (...args) => writeRef.hub.jumpToChapter(...args),
    navigateTo,
    settingsHasUnsavedChanges,
  });
  const {
    panelContext: productToolsPanelContext,
    loadPreferencesFromServer,
    loadMemoryAssets,
    loadCreatorModels,
  } = productToolsHub;

  watch(
    () => {
      const ma = productToolsPanelContext.memoryAssets;
      if (!ma || typeof ma !== 'object') return [];
      if ('value' in ma) {
        try {
          const resolved = ma.value;
          return Array.isArray(resolved) ? resolved : [];
        } catch {
          return [];
        }
      }
      return Array.isArray(ma) ? ma : [];
    },
    (assets) => {
      writeHub.syncMemoryAssets?.(assets);
    },
    { immediate: true },
  );

  const refresh = createCreatorPageRefresh({
    overview,
    loading,
    error,
    conflictMessage,
    fetchOverview: fetchCreatorOverview,
    loaders: {
      loadVolumePlan,
      loadSettingsDocs,
      loadSettingsHistory,
      loadVolumeTemplates,
      loadTemplateSyncSources,
      loadOnboardingWizard,
      pollBatchJob,
    },
    afterOverview: async () => {
      maybeAutoSelectWritingChapter();
      syncWizardPanelOpen();
      loadCreationModeSwitchHistory();
      await refreshVolumePlanDiffPreview();
      await loadMergePreferences();
      await loadMergePresetPackages();
      await loadTemplateApprovals();
      await loadBatchHistory();
      await loadDiffCollabNotes();
      tryLoadVolumePlanDiffShareLinkPreview();
      resumeBatchPollingIfNeeded();
      await Promise.all([loadPreferencesFromServer(), loadMemoryAssets(), loadCreatorModels()]);
    },
  });

  refreshRef.fn = refresh;

  const workspaceTabBadgesMerged = computed(() => {
    const badges = { ...(workspaceTabBadges.value || {}) };
    if (settingsHasUnsavedChanges.value || productToolsPanelContext.preferencesDirty) {
      badges.settings = '!';
    }
    return Object.keys(badges).length ? badges : null;
  });

  const chromeContext = {
    overview,
    loading,
    uiProfile,
    modeLabel,
    creationModeBadgeHintText,
    modeBadgeHintEnabled,
    showCreationModeBadge,
    showPageTitle,
    showHeaderPreferences,
    showHeaderPublishExport,
    showHeaderRefresh,
    showHeaderActionsRow,
    displayDeviationBadge,
    displayDeviationCount,
    showCreationModeBadgeHint,
    workspaceActiveTab,
    workspaceTabsEnabled,
    workspaceTabs,
    workspacePrimaryTabs,
    workspaceSecondaryTabs,
    workspaceDrawerTabs,
    deskDrawerEnabled,
    deskDrawerPanel,
    deskDrawerOpen,
    isDeskDrawerColumn,
    openDeskDrawer,
    closeDeskDrawer,
    workspaceTabBadges: workspaceTabBadgesMerged,
    setWorkspaceTab,
    onDeviationBadgeClick,
    error,
    conflictMessage,
    saveMessage,
    refresh,
    preferencesSummary: productToolsPanelContext.preferencesSummary,
    openExportModal: (...args) => productToolsPanelContext.openExportModal(...args),
    openPublishWizard: () => productToolsPanelContext.openPublishWizard(),
  };

  useCreatorPageProviders({
    chromeContext,
    pulsePanelContext,
    advanceBatchPanelContext,
    writePanelContext,
    settingsPanelContext,
    onboardingPanelContext,
    modeGuidePanelContext,
    batchHistoryPanelContext,
    volumePlanPanelContext,
    productToolsPanelContext,
  });

  onMounted(() => {
    refresh();
    window.addEventListener('keydown', onCreationModeSwitchHotkey);
  });

  onUnmounted(() => {
    window.removeEventListener('keydown', onCreationModeSwitchHotkey);
  });

  watch(projectRevision, () => {
    refresh();
  });

  watch(
    editableVolumes,
    () => {
      refreshVolumePlanDiffPreview();
    },
    { deep: true },
  );

  return {
    overview,
    loading,
    uiProfile,
    modeLabel,
    creationModeBadgeHintText,
    modeBadgeHintEnabled,
    showCreationModeBadge,
    showPageTitle,
    showHeaderPreferences,
    showHeaderPublishExport,
    showHeaderRefresh,
    showHeaderActionsRow,
    displayDeviationBadge,
    displayDeviationCount,
    showCreationModeBadgeHint,
    workspaceActiveTab,
    workspaceTabsEnabled,
    workspaceTabs,
    workspaceTabBadges,
    onDeviationBadgeClick,
    error,
    conflictMessage,
    saveMessage,
    refresh,
  };
}
