/**
 * useCreatorPulse — 脉络栏卷级脉络、偏离与卷摘要（从 CreatorPage 抽出）
 */
import { computed, nextTick, ref } from 'vue';
import { generateCreatorVolumeSummary } from '../api/index.js';
import { isPulseSubpanelVisible, isPanelDefaultCollapsed, CREATOR_PULSE_SUBPANEL_MATRIX } from '../config/creatorPanelMatrix.js';

/**
 * @param {{
 *   uiProfile: import('vue').ComputedRef<object>,
 *   overview: import('vue').Ref<object|null>,
 *   error: import('vue').Ref<string|null>,
 *   saveMessage: import('vue').Ref<string>,
 *   workspaceTabsEnabled: import('vue').ComputedRef<boolean>,
 *   isWorkspaceColumnVisible: (col: string) => boolean,
 *   isDeskDrawerColumn?: (col: string) => boolean,
 *   closeDeskDrawer?: () => void,
 *   setWorkspaceTab: (tab: string) => void,
 *   editableVolumes: import('vue').Ref<object[]>,
 *   visibleDeviations: import('vue').ComputedRef<object[]>,
 *   deviationHighlightEnabled: import('vue').ComputedRef<boolean>,
 *   highlightedDeviationChapter: import('vue').Ref<number|null>,
 *   handleDeviationClick: (deviation: object) => Promise<void>,
 *   jumpToChapter: (chapter: number) => Promise<void>,
 *   onAfterVolumeSummarySave: () => Promise<void>,
 *   batchJob?: import('vue').Ref<object|null>,
 * }} deps
 */
export function useCreatorPulse(deps) {
  const {
    uiProfile,
    overview,
    error,
    saveMessage,
    workspaceTabsEnabled,
    isWorkspaceColumnVisible,
    isDeskDrawerColumn = () => false,
    closeDeskDrawer = () => {},
    setWorkspaceTab,
    editableVolumes,
    visibleDeviations,
    deviationHighlightEnabled,
    highlightedDeviationChapter,
    handleDeviationClick,
    jumpToChapter,
    onAfterVolumeSummarySave,
    batchJob,
  } = deps;

  const batchSummaryPrompt = ref(null);
  const openVolumeSummaryName = ref(null);
  const highlightedVolumeLabel = ref(null);

  const showPulseCompanionEmpty = computed(() => {
    if (overview.value?.creation_mode !== 'companion') return false;
    if (!workspaceTabsEnabled.value) return false;
    if (editableVolumes.value.length > 0) return false;
    if (visibleDeviations.value.length > 0) return false;
    if (overview.value.volume_pulse?.volume_count) return false;
    return true;
  });

  async function jumpToVolume(row) {
    if (!row) return;
    highlightedVolumeLabel.value = row.label;
    await jumpToChapter(row.start_chapter);
  }

  function openVolumeSummaryByName(name) {
    if (!name) return;
    openVolumeSummaryName.value = name;
    nextTick(() => {
      try {
        document.querySelector(`[data-testid="volume-summary-block-${name}"]`)?.scrollIntoView?.({
          behavior: 'smooth',
          block: 'start',
        });
      } catch {
        /* jsdom */
      }
    });
  }

  function openVolumeSummaryForRange(start, end) {
    const pad = (n) => String(n).padStart(3, '0');
    const target = `volume-summary-ch${pad(start)}-${pad(end)}.md`;
    const match = overview.value?.volume_summaries?.find((vol) => vol.name === target);
    if (match) {
      openVolumeSummaryByName(match.name);
    }
  }

  function volumeOverlapsRange(row, start, end) {
    return row.start_chapter <= end && row.end_chapter >= start;
  }

  function collectBatchAlertVolumeLabels(start, end) {
    const rows = overview.value?.volume_pulse?.volumes || [];
    return rows
      .filter((row) => row.status === 'alert' && volumeOverlapsRange(row, start, end))
      .map((row) => row.label);
  }

  async function highlightBatchAlertVolumes(start, end) {
    if (!uiProfile.value.batch_highlight_alert_volumes && !uiProfile.value.batch_clear_pulse_no_alert) {
      return;
    }
    await nextTick();
    const rows = overview.value?.volume_pulse?.volumes || [];
    const alertRow = rows.find(
      (row) => row.status === 'alert' && volumeOverlapsRange(row, start, end),
    );
    if (alertRow) {
      highlightedVolumeLabel.value = alertRow.label;
      try {
        document.querySelector('[data-testid="volume-pulse-panel"]')?.scrollIntoView?.({
          behavior: 'smooth',
          block: 'start',
        });
      } catch {
        /* jsdom */
      }
      return;
    }
    if (uiProfile.value.batch_clear_pulse_no_alert) {
      highlightedVolumeLabel.value = null;
    }
  }

  async function generateVolumeSummaryForRow(row) {
    if (!row) return;
    try {
      await generateCreatorVolumeSummary({
        startChapter: row.start_chapter,
        endChapter: row.end_chapter,
      });
      saveMessage.value = `已生成「${row.label}」卷摘要`;
      await onAfterVolumeSummarySave();
      openVolumeSummaryForRange(row.start_chapter, row.end_chapter);
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    }
  }

  function dismissBatchSummaryPrompt() {
    batchSummaryPrompt.value = null;
  }

  function setBatchSummaryPrompt(prompt) {
    batchSummaryPrompt.value = prompt;
  }

  async function onBatchCompleted(start, end) {
    if (batchSummaryPrompt.value) {
      batchSummaryPrompt.value = {
        ...batchSummaryPrompt.value,
        alert_volume_labels: uiProfile.value.batch_deviation_prompt
          ? collectBatchAlertVolumeLabels(start, end)
          : [],
      };
    }
    if (uiProfile.value.batch_highlight_alert_volumes || uiProfile.value.batch_clear_pulse_no_alert) {
      await highlightBatchAlertVolumes(start, end);
    }
    if (uiProfile.value.batch_auto_open_summary && batchSummaryPrompt.value) {
      openVolumeSummaryForRange(start, end);
    }
  }

  function pulseSubpanelVisible(subpanelId) {
    return isPulseSubpanelVisible(overview.value?.creation_mode, subpanelId);
  }

  function pulseSubpanelCollapsed(subpanelId) {
    return isPanelDefaultCollapsed(
      CREATOR_PULSE_SUBPANEL_MATRIX,
      overview.value?.creation_mode,
      subpanelId,
    );
  }

  const panelContext = {
    overview,
    uiProfile,
    workspaceTabsEnabled,
    isWorkspaceColumnVisible,
    isDeskDrawerColumn,
    closeDeskDrawer,
    setWorkspaceTab,
    showPulseCompanionEmpty,
    highlightedVolumeLabel,
    openVolumeSummaryName,
    batchSummaryPrompt,
    visibleDeviations,
    deviationHighlightEnabled,
    highlightedDeviationChapter,
    handleDeviationClick,
    jumpToVolume,
    generateVolumeSummaryForRow,
    openVolumeSummaryByName,
    openVolumeSummaryForRange,
    dismissBatchSummaryPrompt,
    isPulseSubpanelVisible: pulseSubpanelVisible,
    isPulseSubpanelCollapsed: pulseSubpanelCollapsed,
    deskDrawerActive: () => isDeskDrawerColumn('pulse'),
    closeDeskDrawer,
    batchJob,
  };

  return {
    panelContext,
    batchSummaryPrompt,
    openVolumeSummaryForRange,
    onBatchCompleted,
    setBatchSummaryPrompt,
    highlightBatchAlertVolumes,
    collectBatchAlertVolumeLabels,
  };
}
