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

    <div v-if="error" class="error-banner pixel-border" data-testid="error-banner">
      {{ error }}
    </div>
    <div v-if="conflictMessage" class="conflict-banner pixel-border" data-testid="conflict-banner">
      {{ conflictMessage }}
      <button type="button" class="mini-btn pixel-border" data-testid="conflict-reload-btn" @click="refresh">
        重新加载
      </button>
    </div>
    <div v-if="saveMessage" class="save-banner pixel-border" data-testid="save-banner">
      {{ saveMessage }}
    </div>

    <HubTabBar
      v-if="overview && workspaceTabsEnabled"
      v-model="workspaceActiveTab"
      :tabs="workspaceTabs"
      :badges="workspaceTabBadges"
      test-id="creator-workspace-tab"
      class="creator-workspace-tabs"
      data-testid="creator-workspace-tabs"
    />

    <div
      v-if="overview"
      class="creator-grid"
      :class="{ 'creator-grid--tabbed': workspaceTabsEnabled }"
      data-testid="creator-grid"
    >
      <!-- 写 -->
      <CreatorWritePanel />

      <!-- 脉络 -->
      <CreatorPulsePanel />

      <!-- 设定 -->
      <CreatorSettingsPanel />
    </div>

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
  fetchCreatorVolumePlan,
  previewCreatorVolumePlanDiff,
  fetchCreatorBatchHistory,
  exportCreatorBatchHistory,
  dismissCreatorWizardPanel,
  saveCreatorWizardPanelCollapsed,
  fetchCreatorSettingsDocs,
  saveCreatorVolumePlan,
  mergeCreatorVolumePlan,
  splitCreatorVolumePlan,
  fetchCreatorVolumeTemplates,
  applyCreatorVolumeTemplate,
  saveCreatorVolumeTemplate,
  deleteCreatorVolumeTemplate,
  renameCreatorVolumeTemplate,
  exportCreatorVolumeTemplates,
  importCreatorVolumeTemplates,
  fetchCreatorVolumeTemplateSyncSources,
  syncCreatorVolumeTemplates,
  publishCreatorVolumeTemplateToFactory,
  pullCreatorFactoryVolumeTemplates,
  deleteCreatorFactoryVolumeTemplate,
  fetchCreatorOnboarding,
  saveCreatorOnboardingProgress,
  applyCreatorOnboardingShare,
  saveCreatorOnboardingNotes,
  fetchCreatorDiffCollabNotes,
  saveCreatorDiffCollabNotes,
  setCreatorVolumeTemplateVersion,
  fetchCreatorVolumeTemplateChangelog,
  rollbackCreatorVolumeTemplate,
  fetchCreatorTemplateApprovals,
  submitCreatorTemplateVersionApproval,
  approveCreatorTemplateApproval,
  rejectCreatorTemplateApproval,
  fetchCreatorTemplateApprovalChainConfig,
  saveCreatorTemplateApprovalChainConfig,
  fetchCreatorTemplateApprovalHistory,
  exportCreatorTemplateApprovalAudit,
  fetchCreatorTemplateApprovalSlaConfig,
  saveCreatorTemplateApprovalSlaConfig,
  fetchCreatorTemplateApprovalOverdue,
  transferCreatorTemplateApproval,
  fetchCreatorTemplateApprovalSnapshotDiff,
  fetchCreatorTemplateApprovalSnapshotDrift,
  batchApproveCreatorTemplateApprovals,
  batchRejectCreatorTemplateApprovals,
  fetchCreatorOnboardingDigestDeadLetter,
  replayCreatorOnboardingDigestDeadLetter,
  preflightCreatorFactoryMergePresetPull,
  fetchCreatorMergePresetChangelog,
  fetchCreatorMergePresetChangelogDiff,
  fetchCreatorMergePresetToposort,
  fetchCreatorOnboardingNotifications,
  fetchCreatorOnboardingNotificationDigest,
  fetchCreatorOnboardingDigestSchedule,
  saveCreatorOnboardingDigestSchedule,
  dispatchCreatorOnboardingDigest,
  fetchCreatorOnboardingDigestRetryQueue,
  fetchCreatorOnboardingDigestStats,
  processCreatorOnboardingDigestRetries,
  ackCreatorOnboardingNotifications,
  fetchCreatorOnboardingWebhook,
  saveCreatorOnboardingWebhook,
  fetchCreatorOnboardingEmail,
  saveCreatorOnboardingEmail,
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
  saveCreatorSettingsDocs,
  previewCreatorSettingsDocs,
  previewCreatorSettingsThreeWay,
  previewCreatorSettingsMerge,
  fetchCreatorMergePreferences,
  exportCreatorMergePreferences,
  importCreatorMergePreferences,
  fetchCreatorSettingsHistory,
  restoreCreatorSettingsSnapshot,
} from '../api/index.js';
import { useStudioProject } from '../composables/useStudioProject.js';
import { useDashboardNav } from '../composables/useDashboardNav.js';
import { useCreatorWorkspace } from '../composables/useCreatorWorkspace.js';
import { useCreatorVolumePlan } from '../composables/useCreatorVolumePlan.js';
import { useCreatorBatchHistory } from '../composables/useCreatorBatchHistory.js';
import HubTabBar from '../components/HubTabBar.vue';
import CreatorPageHeader from '../components/creator/CreatorPageHeader.vue';
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

const defaultUiProfile = {
  show_studio_workflow: true,
  show_digest_ops: true,
  show_factory_presets: true,
  show_template_version_ops: true,
  show_merge_preset_advanced: true,
  simplified_notifications: false,
  volume_pulse_enabled: false,
  wizard_default_collapsed: false,
  wizard_expand_if_incomplete: false,
  chapter_inline_edit: false,
  chapter_full_preview: false,
  logic_check_inline_issues: false,
  logic_check_p0_only: false,
  deviation_chapter_jump: false,
  chapter_save_p0_recheck: false,
  batch_highlight_alert_volumes: false,
  volume_pulse_summary_generate: false,
  batch_auto_open_summary: false,
  batch_deviation_prompt: false,
  chapter_recheck_inline: false,
  chapter_outline_inline_edit: false,
  recheck_issue_paragraph_jump: false,
  batch_clear_pulse_no_alert: false,
  recheck_issue_highlight: false,
  batch_scroll_deviation_list: false,
  chapter_outline_read_preview: false,
  logic_check_issue_highlight: false,
  deviation_list_highlight: false,
  batch_open_first_deviation: false,
  deviation_click_highlight: false,
  batch_deviation_inline_summary: false,
  batch_deviation_inline_dismiss: false,
  batch_deviation_summary_link: false,
  issue_keyboard_navigation: false,
  issue_paragraph_highlight_unified: false,
  volume_plan_diff_preview: false,
  volume_plan_diff_save_confirm: false,
  volume_plan_diff_expand_detail: false,
  batch_history_panel: false,
  batch_history_replay_range: false,
  batch_history_status_filter: false,
  volume_plan_diff_outline_side_by_side: false,
  batch_history_export: false,
  volume_plan_diff_outline_row_highlight: false,
  batch_history_date_group: false,
  volume_plan_diff_jump_outline_edit: false,
  batch_history_status_color: false,
  volume_plan_diff_refresh_on_save: false,
  batch_history_running_pulse: false,
  volume_plan_diff_auto_collapse: false,
  batch_history_failed_retry: false,
  volume_plan_diff_change_count: false,
  batch_history_budget_hint: false,
  volume_plan_diff_type_filter: false,
  batch_history_duration: false,
  volume_plan_diff_export: false,
  batch_history_success_rate: false,
  volume_plan_diff_volume_filter: false,
  batch_history_avg_duration: false,
  volume_plan_diff_export_outline: false,
  volume_plan_diff_export_highlight: false,
  batch_history_failure_trend: false,
  batch_history_weekly_summary: false,
  batch_history_monthly_summary: false,
  volume_plan_diff_export_markdown: false,
  volume_plan_diff_export_email_share: false,
  volume_plan_diff_export_pdf: false,
  batch_history_success_rate_chart: false,
  batch_history_failure_reason_label: false,
  volume_plan_diff_export_print_preview: false,
  batch_history_status_stack_chart: false,
  volume_plan_diff_export_zip: false,
  batch_history_duration_distribution: false,
  volume_plan_diff_export_share_link: false,
  batch_history_concurrency_chart: false,
  volume_plan_diff_share_link_preview: false,
  batch_history_queue_depth_chart: false,
  volume_plan_diff_share_link_apply: false,
  batch_history_throughput_chart: false,
  volume_plan_diff_share_link_apply_confirm: false,
  batch_history_cost_efficiency_chart: false,
  creation_mode_switch_reduced_motion: false,
  volume_plan_diff_share_token_validation: false,
  batch_history_retry_rate_stack: false,
  creation_mode_switch_aria_live: false,
  volume_plan_diff_share_link_merge: false,
  batch_history_chapter_failure_heatmap: false,
  creation_mode_preview_pinned_sidebar: false,
  volume_plan_diff_share_link_e2e: false,
  batch_history_ops_summary: false,
  volume_plan_diff_share_collab_v2: false,
  creation_mode_accessibility_checklist: false,
  creation_mode_switch_confirm_dialog: false,
  creation_mode_switch_history: false,
  creation_mode_switch_undo_hint: false,
  creation_mode_switch_hotkey: false,
  creation_mode_switch_speech: false,
  creation_mode_switch_haptic: false,
  creation_mode_badge_hint: false,
  creation_mode_capability_matrix: false,
  creation_mode_switch_guide_animation: false,
  creation_mode_onboarding_step_link: false,
  studio_creation_mode_badge_hint: false,
  studio_creation_mode_badge_tint: false,
  companion_creation_mode_badge_tint: false,
  advance_creation_mode_badge_tint: false,
  creation_mode_badge_legend: false,
  creation_mode_switch_preview: false,
  creation_mode_yaml_snippet: false,
  creation_mode_switch_doc_open: false,
  creation_mode_switch_hint: false,
  creation_mode_switch_doc_link: false,
  studio_creation_entry_hint: false,
  studio_wizard_collapse_memory: false,
  deviation_min_severity: null,
  primary_action: 'studio_quality',
  creator_workspace_tabs: false,
  creator_mode_guide_default_collapsed: false,
  creator_simplified_mode_ops: false,
};

const uiProfile = computed(() => overview.value?.ui_profile || defaultUiProfile);

const {
  activeTab: workspaceActiveTab,
  tabsEnabled: workspaceTabsEnabled,
  workspaceTabs,
  isColumnVisible: isWorkspaceColumnVisible,
  setWorkspaceTab,
} = useCreatorWorkspace(uiProfile, overview);


function onDeviationBadgeClick() {
  if (workspaceTabsEnabled.value) {
    setWorkspaceTab('pulse');
    setCreatorWorkspace('pulse');
  }
}

watch(workspaceActiveTab, (tab) => {
  if (workspaceTabsEnabled.value) {
    setCreatorWorkspace(tab);
  }
});

watch(
  () => [focusCreatorWorkspace.value, workspaceTabsEnabled.value, overview.value],
  () => {
    if (!workspaceTabsEnabled.value || !focusCreatorWorkspace.value) return;
    setWorkspaceTab(focusCreatorWorkspace.value);
  },
  { immediate: true },
);



const deviationHighlightEnabled = computed(
  () => Boolean(
    uiProfile.value.deviation_list_highlight || uiProfile.value.deviation_click_highlight,
  ),
);

const visibleDeviations = computed(() => overview.value?.deviations || []);

const {
  modeLabel,
  creationModeBadgeHintText,
  modeBadgeHintEnabled,
  displayDeviationBadge,
  displayDeviationCount,
  showCreationModeBadgeHint,
} = useCreatorPageHeader({ uiProfile, overview, saveMessage });

const workspaceTabBadges = computed(() => {
  if (!displayDeviationCount.value) return null;
  return { pulse: displayDeviationCount.value };
});

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

.creator-grid--tabbed {
  grid-template-columns: 1fr;
}

.creator-workspace-tabs {
  padding: 0 var(--space-md);
}





.creator-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
  align-items: start;
}

@media (max-width: 960px) {
  .creator-grid {
    grid-template-columns: 1fr;
  }
}

.creator-column {
  padding: var(--space-md);
  min-height: 280px;
}

.column-title {
  font-size: var(--text-lg);
  margin-bottom: var(--space-sm);
  color: var(--color-accent);
  font-family: 'Press Start 2P', monospace;
}

.column-hint {
  font-size: var(--text-sm);
  opacity: 0.7;
  margin-bottom: var(--space-md);
}











.issue-line--active {
  animation: issue-line-flash 1.2s ease-out;
  background: rgba(255, 220, 100, 0.35);
  box-shadow: inset 0 0 0 1px rgba(200, 180, 80, 0.65);
}







.volume-plan-diff-count {
  margin-left: var(--space-xs);
  padding: 1px 4px;
  border-radius: 2px;
  color: #a60;
  background: rgba(255, 200, 80, 0.35);
  font-family: 'Press Start 2P', monospace;
  font-size: 6px;
}









































































.volume-plan-diff-collab-panel {
  margin: var(--space-xs) 0;
  padding: var(--space-sm);
}

.volume-plan-diff-collab-row {
  display: block;
  margin: var(--space-xs) 0;
  font-size: var(--text-md);
}

.volume-plan-diff-collab-input {
  display: block;
  width: 100%;
  margin-top: 2px;
}

.volume-plan-diff-volume-filter {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
  margin-left: var(--space-sm);
}





.volume-plan-diff-type-filter {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
}



.volume-plan-diff-summary {
  cursor: pointer;
  font-family: 'Press Start 2P', monospace;
  font-size: var(--text-xs);
}


.volume-plan-outline-lines {
  list-style: none;
  padding: 0;
  margin: var(--space-xs) 0;
  font-size: var(--text-xs);
  line-height: 1.5;
  max-height: 220px;
  overflow: auto;
}

.volume-plan-outline-line {
  padding: 2px 0;
  white-space: pre-wrap;
}

.volume-plan-outline-line--highlight {
  background: rgba(255, 220, 100, 0.35);
  box-shadow: inset 0 0 0 1px rgba(200, 180, 80, 0.65);
}








.volume-plan-diff-panel {
  margin-top: var(--space-sm);
  padding: var(--space-xs);
  background: rgba(200, 160, 80, 0.1);
}

.volume-plan-diff-side-by-side {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--space-sm);
  align-items: start;
}

.volume-plan-diff-outline-col {
  padding: var(--space-xs);
  background: rgba(100, 140, 200, 0.08);
  max-height: 220px;
  overflow: auto;
}

.volume-plan-outline-excerpt {
  margin: var(--space-xs) 0;
  white-space: pre-wrap;
  font-size: var(--text-xs);
  line-height: 1.5;
}


.volume-plan-diff-list {
  list-style: none;
  padding: 0;
  margin: var(--space-xs) 0 0;
  font-size: var(--text-sm);
}

.volume-plan-diff-item .diff-type {
  font-family: 'Press Start 2P', monospace;
  font-size: var(--text-xs);
  margin-right: var(--space-xs);
  text-transform: uppercase;
}

.volume-plan-diff-details summary {
  cursor: pointer;
  list-style: none;
}

.volume-plan-diff-details summary::-webkit-details-marker {
  display: none;
}

.volume-plan-diff-detail-list {
  list-style: none;
  padding: var(--space-xs) 0 0 var(--space-sm);
  margin: 0;
  font-size: var(--text-xs);
  opacity: 0.9;
}










.volume-plan-save-confirm {
  margin-top: var(--space-xs);
  padding: var(--space-xs);
  background: rgba(200, 120, 80, 0.1);
}


@keyframes issue-line-flash {
  0% { background: rgba(255, 220, 100, 0.55); }
  100% { background: rgba(255, 220, 100, 0.35); }
}












.issue-severity {
  display: inline-block;
  min-width: 2.5em;
  margin-right: var(--space-xs);
  font-weight: bold;
}

.link-btn {
  background: none;
  border: none;
  padding: 0;
  color: inherit;
  text-decoration: underline;
  cursor: pointer;
  font: inherit;
}



.preview-text {
  font-size: var(--text-sm);
  white-space: pre-wrap;
  margin: var(--space-xs) 0;
}



.progress-bar {
  height: 12px;
  margin-top: var(--space-sm);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-accent);
  transition: width 0.2s;
}

.subsection-title {
  font-size: var(--text-sm);
  margin: var(--space-md) 0 var(--space-xs);
}

.volume-plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.volume-edit-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 6px;
  margin-bottom: 6px;
  font-size: var(--text-sm);
}

.volume-edit-row--locked {
  border-color: var(--color-accent);
  background: rgba(100, 140, 200, 0.08);
}

.volume-edit-row--dragging {
  opacity: 0.55;
}

.volume-reorder {
  display: flex;
  flex-direction: column;
  gap: 2px;
  align-items: center;
}

.drag-handle {
  cursor: grab;
  font-size: var(--text-sm);
  opacity: 0.6;
  user-select: none;
}

.vol-input {
  font-size: var(--text-sm);
  padding: 2px 4px;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--color-text);
}

.vol-label { width: 3em; }
.vol-num { width: 3em; }
.vol-conflict { flex: 1; min-width: 80px; }
.vol-range { display: flex; align-items: center; gap: 2px; }

.mini-btn,
.save-btn {
  font-size: var(--text-xs);
  padding: 2px 6px;
  cursor: pointer;
}

.save-btn {
  margin-top: var(--space-xs);
}

.deviation-list {
  list-style: none;
  padding: 0;
  margin: var(--space-sm) 0 0;
  font-size: var(--text-sm);
}

.deviation-warn { color: #886600; }
.deviation-alert { color: #c44; }

.deviation-item--clickable {
  cursor: pointer;
}

.deviation-item--clickable:hover {
  text-decoration: underline;
}

.deviation-item--active {
  animation: deviation-item-flash 1.2s ease-out;
  box-shadow: inset 0 0 0 2px rgba(200, 80, 80, 0.55);
}

@keyframes deviation-item-flash {
  0% { background: rgba(255, 200, 120, 0.45); }
  100% { background: transparent; }
}

.deviation-chapter {
  display: inline-block;
  min-width: 3.5em;
  margin-right: var(--space-xs);
  font-weight: bold;
}





.path-line,


.meta-line {
  font-size: var(--text-sm);
  opacity: 0.75;
}

.refresh-btn {
  font-size: var(--text-sm);
  padding: var(--space-xs) var(--space-sm);
  cursor: pointer;
}

.error-banner {
  padding: var(--space-sm);
  color: #c44;
  font-size: var(--text-sm);
}

.save-banner {
  padding: var(--space-sm);
  color: #484;
  font-size: var(--text-sm);
}

.conflict-banner {
  padding: var(--space-sm);
  color: #a60;
  font-size: var(--text-sm);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}




.mini-btn--danger {
  color: #c44;
}





























.volume-template-panel {
  margin-bottom: var(--space-sm);
  padding: var(--space-sm);
}

.pulse-empty-guide {
  margin-bottom: var(--space-sm);
  padding: var(--space-md);
}

.pulse-empty-guide .meta-line {
  margin: var(--space-xs) 0 var(--space-sm);
}



.volume-merge-panel {
  margin-top: var(--space-sm);
  padding: var(--space-sm);
}

.volume-split-panel {
  margin-top: var(--space-sm);
  padding: var(--space-sm);
}





</style>
