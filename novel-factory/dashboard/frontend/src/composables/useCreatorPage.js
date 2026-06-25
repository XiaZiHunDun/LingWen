/**
 * useCreatorPage — 创作页 hub 编排、refresh 与 provide（从 CreatorPage 抽出）
 */
import { computed, onMounted, onUnmounted, provide, ref, watch } from 'vue';
import { fetchCreatorOverview, runCreatorLogicCheck } from '../api/index.js';
import { creatorDefaultUiProfile } from './creatorDefaultUiProfile.js';
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
import { CREATOR_MODE_GUIDE_KEY, createCreatorModeGuideContext } from '../components/creator/creatorModeGuideKey.js';
import { CREATOR_ONBOARDING_KEY, createCreatorOnboardingContext } from '../components/creator/creatorOnboardingKey.js';
import { CREATOR_SETTINGS_KEY, createCreatorSettingsContext } from '../components/creator/creatorSettingsKey.js';
import { CREATOR_WRITE_KEY, createCreatorWriteContext } from '../components/creator/creatorWriteKey.js';
import { CREATOR_PULSE_KEY, createCreatorPulseContext } from '../components/creator/creatorPulseKey.js';
import { CREATOR_ADVANCE_BATCH_KEY, createCreatorAdvanceBatchContext } from '../components/creator/creatorAdvanceBatchKey.js';
import { CREATOR_BATCH_HISTORY_KEY, createCreatorBatchHistoryContext } from '../components/creator/creatorBatchHistoryKey.js';
import { CREATOR_VOLUME_PLAN_KEY, createCreatorVolumePlanContext } from '../components/creator/creatorVolumePlanKey.js';

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

  const uiProfile = computed(() => overview.value?.ui_profile || creatorDefaultUiProfile);

  const {
    modeLabel,
    creationModeBadgeHintText,
    modeBadgeHintEnabled,
    displayDeviationBadge,
    displayDeviationCount,
    showCreationModeBadgeHint,
  } = useCreatorPageHeader({ uiProfile, overview, saveMessage });

  const {
    activeTab: workspaceActiveTab,
    tabsEnabled: workspaceTabsEnabled,
    workspaceTabs,
    isColumnVisible: isWorkspaceColumnVisible,
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
    setWorkspaceTab,
    editableVolumes,
    visibleDeviations,
    deviationHighlightEnabled,
    highlightedDeviationChapter,
    handleDeviationClick: (...args) => writeRef.hub.handleDeviationClick(...args),
    jumpToChapter: (...args) => writeRef.hub.jumpToChapter(...args),
    onAfterVolumeSummarySave: async () => refresh(),
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
  const { panelContext: settingsPanelContext, loadSettingsDocs, loadSettingsHistory, loadMergePreferences, loadMergePresetPackages } = settingsHub;

  async function refresh() {
    loading.value = true;
    error.value = null;
    conflictMessage.value = '';
    try {
      const [ov] = await Promise.all([
        fetchCreatorOverview(),
        loadVolumePlan(),
        loadSettingsDocs(),
        loadSettingsHistory(),
        loadVolumeTemplates(),
        loadTemplateSyncSources(),
        loadOnboardingWizard(),
        pollBatchJob(),
      ]);
      overview.value = ov;
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
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      loading.value = false;
    }
  }

  refreshRef.fn = refresh;

  provide(CREATOR_PULSE_KEY, createCreatorPulseContext(pulsePanelContext));
  provide(CREATOR_ADVANCE_BATCH_KEY, createCreatorAdvanceBatchContext(advanceBatchPanelContext));
  provide(CREATOR_WRITE_KEY, createCreatorWriteContext(writePanelContext));
  provide(CREATOR_SETTINGS_KEY, createCreatorSettingsContext(settingsPanelContext));
  provide(CREATOR_ONBOARDING_KEY, createCreatorOnboardingContext(onboardingPanelContext));
  provide(CREATOR_MODE_GUIDE_KEY, createCreatorModeGuideContext(modeGuidePanelContext));
  provide(CREATOR_BATCH_HISTORY_KEY, createCreatorBatchHistoryContext(batchHistoryPanelContext));
  provide(CREATOR_VOLUME_PLAN_KEY, createCreatorVolumePlanContext(volumePlanPanelContext));

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
