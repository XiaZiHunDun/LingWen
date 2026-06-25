<!--
  CreatorPage.vue — 创作者三栏：写 / 脉络 / 设定 + 卷纲锁定与偏离 diff
-->
<template>
  <div class="creator-page">
    <CreatorPageHeader
      :overview="overview"
      :loading="loading"
      :ui-profile="uiProfile"
      :mode-label="modeLabel"
      :creation-mode-badge-hint-text="creationModeBadgeHintText"
      :mode-badge-hint-enabled="modeBadgeHintEnabled"
      :display-deviation-badge="displayDeviationBadge"
      :display-deviation-count="displayDeviationCount"
      :workspace-tabs-enabled="workspaceTabsEnabled"
      @refresh="refresh"
      @deviation-badge-click="onDeviationBadgeClick"
      @mode-badge-hint="showCreationModeBadgeHint"
    />

    <CreatorPageBanners
      :error="error"
      :conflict-message="conflictMessage"
      :save-message="saveMessage"
      @reload="refresh"
    />

    <CreatorWorkspaceShell
      v-model:active-tab="workspaceActiveTab"
      :overview="overview"
      :tabs-enabled="workspaceTabsEnabled"
      :workspace-tabs="workspaceTabs"
      :tab-badges="workspaceTabBadges"
    >
      <CreatorWritePanel />
      <CreatorPulsePanel />
      <CreatorSettingsPanel />
    </CreatorWorkspaceShell>

    <CreatorModeGuidePanel :mode-label="modeLabel" />

    <CreatorVolumePlanShareModals
      :ui-profile="uiProfile"
      :volume-plan-diff-share-link-preview="volumePlanDiffShareLinkPreview"
      :share-e2e-apply-done="shareE2eApplyDone"
      :pending-share-apply="pendingShareApply"
      :pending-share-merge="pendingShareMerge"
      :show-volume-plan-diff-print-preview="showVolumePlanDiffPrintPreview"
      :volume-plan-diff-print-preview-text="volumePlanDiffPrintPreviewText"
      @request-apply-share="requestApplyVolumePlanDiffShareLink"
      @dismiss-share-preview="dismissVolumePlanDiffShareLinkPreview"
      @confirm-share-apply="confirmApplyVolumePlanDiffShareLink"
      @cancel-share-apply="cancelApplyVolumePlanDiffShareLink"
      @confirm-share-merge="confirmShareMergeUseShare"
      @cancel-share-merge="cancelShareMerge"
      @print-preview="printVolumePlanDiffPrintPreview"
      @close-print-preview="closeVolumePlanDiffPrintPreview"
    />

    <CreatorOnboardingWizardPanel />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, provide, ref, watch } from 'vue';
import {
  fetchCreatorOverview,
  runCreatorLogicCheck,
} from '../api/index.js';
import { creatorDefaultUiProfile } from '../composables/creatorDefaultUiProfile.js';
import { useStudioProject } from '../composables/useStudioProject.js';
import { useDashboardNav } from '../composables/useDashboardNav.js';
import { useCreatorWorkspace } from '../composables/useCreatorWorkspace.js';
import { useCreatorVolumePlan } from '../composables/useCreatorVolumePlan.js';
import { useCreatorBatchHistory } from '../composables/useCreatorBatchHistory.js';
import CreatorPageHeader from '../components/creator/CreatorPageHeader.vue';
import CreatorPageBanners from '../components/creator/CreatorPageBanners.vue';
import CreatorWorkspaceShell from '../components/creator/CreatorWorkspaceShell.vue';
import CreatorPulsePanel from '../components/creator/CreatorPulsePanel.vue';
import CreatorVolumePlanShareModals from '../components/creator/CreatorVolumePlanShareModals.vue';
import CreatorModeGuidePanel from '../components/creator/CreatorModeGuidePanel.vue';
import CreatorOnboardingWizardPanel from '../components/creator/CreatorOnboardingWizardPanel.vue';
import CreatorSettingsPanel from '../components/creator/CreatorSettingsPanel.vue';
import CreatorWritePanel from '../components/creator/CreatorWritePanel.vue';
import { useCreatorModeGuide } from '../composables/useCreatorModeGuide.js';
import { useCreatorOnboarding } from '../composables/useCreatorOnboarding.js';
import { useCreatorSettings } from '../composables/useCreatorSettings.js';
import { useCreatorWrite } from '../composables/useCreatorWrite.js';
import { useCreatorPageHeader } from '../composables/useCreatorPageHeader.js';
import { useCreatorAdvanceBatch } from '../composables/useCreatorAdvanceBatch.js';
import { useCreatorPulse } from '../composables/useCreatorPulse.js';
import { CREATOR_MODE_GUIDE_KEY, createCreatorModeGuideContext } from '../components/creator/creatorModeGuideKey.js';
import { CREATOR_ONBOARDING_KEY, createCreatorOnboardingContext } from '../components/creator/creatorOnboardingKey.js';
import { CREATOR_SETTINGS_KEY, createCreatorSettingsContext } from '../components/creator/creatorSettingsKey.js';
import { CREATOR_WRITE_KEY, createCreatorWriteContext } from '../components/creator/creatorWriteKey.js';
import { CREATOR_PULSE_KEY, createCreatorPulseContext } from '../components/creator/creatorPulseKey.js';
import { CREATOR_ADVANCE_BATCH_KEY, createCreatorAdvanceBatchContext } from '../components/creator/creatorAdvanceBatchKey.js';
import { CREATOR_BATCH_HISTORY_KEY, createCreatorBatchHistoryContext } from '../components/creator/creatorBatchHistoryKey.js';
import { CREATOR_VOLUME_PLAN_KEY, createCreatorVolumePlanContext } from '../components/creator/creatorVolumePlanKey.js';

const { projectRevision } = useStudioProject();
const { focusWizard, focusWizardStep, focusWizardDone, focusWizardNotes, setWizardDeepLink, buildWizardShareUrl, navigateTo, focusCreatorWorkspace, setCreatorWorkspace } = useDashboardNav();
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
  showVolumePlanDiffPrintPreview,
  volumePlanDiffShareLinkPreview,
  pendingShareApply,
  pendingShareMerge,
  shareE2eApplyDone,
  volumePlanDiffPrintPreviewText,
  loadVolumePlan,
  loadVolumeTemplates,
  loadTemplateSyncSources,
  loadTemplateApprovals,
  loadDiffCollabNotes,
  refreshVolumePlanDiffPreview,
  tryLoadVolumePlanDiffShareLinkPreview,
  dismissVolumePlanDiffShareLinkPreview,
  requestApplyVolumePlanDiffShareLink,
  confirmApplyVolumePlanDiffShareLink,
  cancelApplyVolumePlanDiffShareLink,
  confirmShareMergeUseShare,
  cancelShareMerge,
  closeVolumePlanDiffPrintPreview,
  printVolumePlanDiffPrintPreview,
  applyVolumePlanDiffShareLink,
  formatHistoryTime,
} = volumePlan;


const modeGuideHub = useCreatorModeGuide({
  uiProfile,
  overview,
  saveMessage,
  onboardingWizard: onboardingHub.onboardingWizard,
  linkModeToOnboardingStep: onboardingHub.linkModeToOnboardingStep,
});
const { panelContext: modeGuidePanelContext, loadCreationModeSwitchHistory, onCreationModeSwitchHotkey } = modeGuideHub;

















refreshRef.fn = refresh;

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
const {
  panelContext: settingsPanelContext,
  loadSettingsDocs,
  loadSettingsHistory,
  loadMergePreferences,
  loadMergePresetPackages,
} = settingsHub;


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



provide(
  CREATOR_PULSE_KEY,
  createCreatorPulseContext(pulsePanelContext),
);
provide(
  CREATOR_ADVANCE_BATCH_KEY,
  createCreatorAdvanceBatchContext(advanceBatchPanelContext),
);
provide(
  CREATOR_WRITE_KEY,
  createCreatorWriteContext(writePanelContext),
);
provide(
  CREATOR_SETTINGS_KEY,
  createCreatorSettingsContext(settingsPanelContext),
);
provide(
  CREATOR_ONBOARDING_KEY,
  createCreatorOnboardingContext(onboardingPanelContext),
);
provide(
  CREATOR_MODE_GUIDE_KEY,
  createCreatorModeGuideContext(modeGuidePanelContext),
);

provide(
  CREATOR_BATCH_HISTORY_KEY,
  createCreatorBatchHistoryContext(batchHistoryPanelContext),
);

provide(
  CREATOR_VOLUME_PLAN_KEY,
  createCreatorVolumePlanContext(volumePlanPanelContext),
);

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
</script>

<style scoped>
.creator-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
</style>