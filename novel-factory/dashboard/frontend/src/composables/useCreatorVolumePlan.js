/**
 * useCreatorVolumePlan — 卷纲编辑、模板库、diff 导出与审批逻辑（从 CreatorPage 抽出）
 */
import { ref } from 'vue';
import {
  fetchCreatorVolumePlan,
  saveCreatorVolumePlan,
  mergeCreatorVolumePlan,
  splitCreatorVolumePlan,
} from '../api/index.js';
import { useCreatorVolumePlanDiff } from './useCreatorVolumePlanDiff.js';
import { useCreatorVolumePlanTemplates } from './useCreatorVolumePlanTemplates.js';

/**
 * @param {
 *   uiProfile: import('vue').ComputedRef<object>,
 *   overview: import('vue').Ref<object|null>,
 *   saving: import('vue').Ref<boolean>,
 *   error: import('vue').Ref<string|null>,
 *   saveMessage: import('vue').Ref<string>,
 *   conflictMessage: import('vue').Ref<string>,
 *   globalOutlineEditorRef: import('vue').Ref<HTMLElement|null>,
 *   globalOutlineText: import('vue').Ref<string>,
 *   batchStart: import('vue').Ref<number>,
 *   batchEnd: import('vue').Ref<number>,
 *   wizardEmailTo: import('vue').Ref<string>,
 *   handleSaveError: (err: unknown) => void,
 *   onAfterVolumePlanSave: () => Promise<void>,
 * } deps
 */
export function useCreatorVolumePlan(deps) {
  const {
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
    onAfterVolumePlanSave,
  } = deps;

  const editableVolumes = ref([]);

  const savedVolumeSnapshot = ref([]);

  const dragVolumeIndex = ref(null);

  const volumePlanRevision = ref('');

  const mergeStartIdx = ref(0);

  const mergeEndIdx = ref(1);

  const mergeLabel = ref('');

  const mergePreview = ref(null);

  const mergeApplying = ref(false);

  const splitVolumeIdx = ref(0);

  const splitAtChapter = ref(2);

  const splitPreview = ref(null);

  const splitApplying = ref(false);

  function syncSplitChapterFromVolume() {
    const vol = editableVolumes.value[splitVolumeIdx.value];
    if (!vol) return;
    const mid = vol.start_chapter + Math.floor((vol.end_chapter - vol.start_chapter) / 2);
    splitAtChapter.value = Math.min(vol.end_chapter, Math.max(vol.start_chapter + 1, mid));
  }

  const diffHub = useCreatorVolumePlanDiff({
    uiProfile,
    saveMessage,
    wizardEmailTo,
    globalOutlineEditorRef,
    editableVolumes,
    saving,
  });

  const templatesHub = useCreatorVolumePlanTemplates({
    uiProfile,
    overview,
    error,
    saveMessage,
    editableVolumes,
    handleSaveError,
    onAfterApplyTemplate: () => {
      mergePreview.value = null;
      splitPreview.value = null;
      syncSplitChapterFromVolume();
    },
  });

  function syncBatchRangeFromVolumes() {
    const locked = editableVolumes.value.filter((v) => v.locked);
    if (!locked.length) return;
    const vol = locked[0];
    batchStart.value = vol.start_chapter;
    batchEnd.value = Math.min(vol.end_chapter, overview.value?.max_chapter || vol.end_chapter);
  }

  function addVolume() {
    const nextStart = editableVolumes.value.length
      ? editableVolumes.value[editableVolumes.value.length - 1].end_chapter + 1
      : 1;
    editableVolumes.value.push({
      label: `卷${editableVolumes.value.length + 1}`,
      start_chapter: nextStart,
      end_chapter: Math.min(nextStart + 9, overview.value?.max_chapter || nextStart + 9),
      core_conflict: '',
      locked: false,
    });
  }

  function toggleLock(idx) {
    editableVolumes.value[idx].locked = !editableVolumes.value[idx].locked;
  }

  function moveVolume(from, to) {
    if (from === to || to < 0 || to >= editableVolumes.value.length) return;
    const items = [...editableVolumes.value];
    const [item] = items.splice(from, 1);
    items.splice(to, 0, item);
    editableVolumes.value = items;
  }

  function onVolumeDragStart(idx, event) {
    dragVolumeIndex.value = idx;
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/plain', String(idx));
    }
  }

  function onVolumeDrop(idx) {
    if (dragVolumeIndex.value === null || dragVolumeIndex.value === idx) {
      dragVolumeIndex.value = null;
      return;
    }
    moveVolume(dragVolumeIndex.value, idx);
    dragVolumeIndex.value = null;
  }

  async function loadVolumePlan() {
    const plan = await fetchCreatorVolumePlan();
    editableVolumes.value = (plan.volumes || []).map((v) => ({ ...v }));
    savedVolumeSnapshot.value = JSON.parse(JSON.stringify(editableVolumes.value));
    volumePlanRevision.value = plan.revision || '';
    mergeStartIdx.value = 0;
    mergeEndIdx.value = Math.min(1, Math.max(0, editableVolumes.value.length - 1));
    mergePreview.value = null;
    splitVolumeIdx.value = 0;
    splitPreview.value = null;
    syncSplitChapterFromVolume();
    syncBatchRangeFromVolumes();
  }

  async function applyVolumeSplit() {
    splitApplying.value = true;
    error.value = null;
    try {
      const result = await splitCreatorVolumePlan({
        volumes: editableVolumes.value,
        volume_index: splitVolumeIdx.value,
        split_at_chapter: splitAtChapter.value,
      });
      editableVolumes.value = (result.volumes || []).map((v) => ({ ...v }));
      splitPreview.value = {
        first_label: result.first_label,
        second_label: result.second_label,
        first_range: result.first_range,
        second_range: result.second_range,
      };
      mergePreview.value = null;
      saveMessage.value = `已拆为「${result.first_label}」与「${result.second_label}」，请保存卷纲`;
      syncSplitChapterFromVolume();
    } catch (e) {
      handleSaveError(e);
    } finally {
      splitApplying.value = false;
    }
  }

  async function applyVolumeMerge() {
    if (mergeStartIdx.value > mergeEndIdx.value) return;
    mergeApplying.value = true;
    error.value = null;
    try {
      const result = await mergeCreatorVolumePlan({
        volumes: editableVolumes.value,
        start_index: mergeStartIdx.value,
        end_index: mergeEndIdx.value,
        label: mergeLabel.value.trim() || undefined,
      });
      editableVolumes.value = (result.volumes || []).map((v) => ({ ...v }));
      mergePreview.value = {
        merged_label: result.merged_label,
        merged_range: result.merged_range,
      };
      mergeStartIdx.value = 0;
      mergeEndIdx.value = Math.min(1, Math.max(0, editableVolumes.value.length - 1));
      mergeLabel.value = '';
      saveMessage.value = `已合并为「${result.merged_label}」，请保存卷纲`;
    } catch (e) {
      handleSaveError(e);
    } finally {
      mergeApplying.value = false;
    }
  }

  function requestSaveVolumePlan() {
    if (
      uiProfile.value.volume_plan_diff_save_confirm
      && diffHub.volumePlanDiffPreview.value?.has_changes
    ) {
      diffHub.volumePlanSaveConfirmOpen.value = true;
      return;
    }
    saveVolumePlan();
  }

  function cancelVolumePlanSave() {
    diffHub.volumePlanSaveConfirmOpen.value = false;
  }

  async function confirmSaveVolumePlan() {
    await saveVolumePlan();
  }

  async function saveVolumePlan() {
    saving.value = true;
    saveMessage.value = '';
    error.value = null;
    try {
      await saveCreatorVolumePlan(editableVolumes.value, volumePlanRevision.value);
      if (uiProfile.value.volume_plan_diff_refresh_on_save) {
        savedVolumeSnapshot.value = JSON.parse(JSON.stringify(editableVolumes.value));
        await diffHub.refreshVolumePlanDiffPreview();
      }
      saveMessage.value = uiProfile.value.volume_plan_diff_refresh_on_save
        ? '卷纲已保存并同步到全局大纲 · diff 已刷新'
        : '卷纲已保存并同步到全局大纲';
      conflictMessage.value = '';
      diffHub.volumePlanSaveConfirmOpen.value = false;
      if (uiProfile.value.volume_plan_diff_share_link_e2e && diffHub.volumePlanDiffShareLinkPreview.value) {
        diffHub.dismissVolumePlanDiffShareLinkPreview();
      }
      await onAfterVolumePlanSave();
    } catch (e) {
      handleSaveError(e);
    } finally {
      saving.value = false;
    }
  }

  const panelContext = {
    addVolume,
    applyVolumeMerge,
    applyVolumeSplit,
    applyVolumeTemplate: templatesHub.applyVolumeTemplate,
    approveTemplateVersion: templatesHub.approveTemplateVersion,
    batchApproveTemplateVersions: templatesHub.batchApproveTemplateVersions,
    batchRejectTemplateVersions: templatesHub.batchRejectTemplateVersions,
    cancelVolumePlanSave,
    confirmSaveVolumePlan,
    customTemplateName: templatesHub.customTemplateName,
    deleteSelectedFactoryTemplate: templatesHub.deleteSelectedFactoryTemplate,
    deleteSelectedVolumeTemplate: templatesHub.deleteSelectedVolumeTemplate,
    diffCollabNotes: diffHub.diffCollabNotes,
    dragVolumeIndex,
    editableVolumes,
    expandedChangelogVisual: templatesHub.expandedChangelogVisual,
    exportCustomTemplates: templatesHub.exportCustomTemplates,
    exportTemplateApprovalAudit: templatesHub.exportTemplateApprovalAudit,
    exportVolumePlanDiff: diffHub.exportVolumePlanDiff,
    exportVolumePlanDiffMarkdown: diffHub.exportVolumePlanDiffMarkdown,
    exportVolumePlanDiffPdf: diffHub.exportVolumePlanDiffPdf,
    exportVolumePlanDiffZip: diffHub.exportVolumePlanDiffZip,
    factoryDeleting: templatesHub.factoryDeleting,
    factoryPulling: templatesHub.factoryPulling,
    factoryTemplateCount: templatesHub.factoryTemplateCount,
    filteredVolumePlanDiffChanges: diffHub.filteredVolumePlanDiffChanges,
    formatHistoryTime: templatesHub.formatHistoryTime,
    formatTemplateOption: templatesHub.formatTemplateOption,
    importCustomTemplates: templatesHub.importCustomTemplates,
    importTemplatesJson: templatesHub.importTemplatesJson,
    isSemverVersionLabel: templatesHub.isSemverVersionLabel,
    jumpToGlobalOutlineEdit: diffHub.jumpToGlobalOutlineEdit,
    mergeApplying,
    mergeEndIdx,
    mergeLabel,
    mergePreview,
    mergeStartIdx,
    moveVolume,
    onVolumeDragStart,
    onVolumeDrop,
    onVolumePlanDiffToggle: diffHub.onVolumePlanDiffToggle,
    openVolumePlanDiffPrintPreview: diffHub.openVolumePlanDiffPrintPreview,
    overdueTemplateApprovals: templatesHub.overdueTemplateApprovals,
    pendingTemplateApprovals: templatesHub.pendingTemplateApprovals,
    previewApprovalSnapshotDiff: templatesHub.previewApprovalSnapshotDiff,
    publishSelectedTemplateToFactory: templatesHub.publishSelectedTemplateToFactory,
    pullFactoryTemplates: templatesHub.pullFactoryTemplates,
    rejectTemplateVersion: templatesHub.rejectTemplateVersion,
    renameSelectedVolumeTemplate: templatesHub.renameSelectedVolumeTemplate,
    renameTemplateName: templatesHub.renameTemplateName,
    requestSaveVolumePlan,
    rollbackTemplateVersion: templatesHub.rollbackTemplateVersion,
    saveCustomVolumeTemplate: templatesHub.saveCustomVolumeTemplate,
    saveTemplateApprovalChainConfig: templatesHub.saveTemplateApprovalChainConfig,
    saveTemplateApprovalSlaConfig: templatesHub.saveTemplateApprovalSlaConfig,
    saveTemplateVersionLabel: templatesHub.saveTemplateVersionLabel,
    saving,
    selectedTemplateFactory: templatesHub.selectedTemplateFactory,
    selectedTemplateHint: templatesHub.selectedTemplateHint,
    selectedTemplateId: templatesHub.selectedTemplateId,
    selectedTemplateProject: templatesHub.selectedTemplateProject,
    setDiffCollabNote: diffHub.setDiffCollabNote,
    shareVolumePlanDiffEmail: diffHub.shareVolumePlanDiffEmail,
    shareVolumePlanDiffLink: diffHub.shareVolumePlanDiffLink,
    showImportTemplates: templatesHub.showImportTemplates,
    splitApplying,
    splitAtChapter,
    splitPreview,
    splitVolumeIdx,
    submitTemplateVersionApproval: templatesHub.submitTemplateVersionApproval,
    syncTemplatesFromProjects: templatesHub.syncTemplatesFromProjects,
    templateApplying: templatesHub.templateApplying,
    templateApprovalEmailOnOverdue: templatesHub.templateApprovalEmailOnOverdue,
    templateApprovalEmailOnReject: templatesHub.templateApprovalEmailOnReject,
    templateApprovalEmailOnSubmit: templatesHub.templateApprovalEmailOnSubmit,
    templateApprovalHistory: templatesHub.templateApprovalHistory,
    templateApprovalOrGroups: templatesHub.templateApprovalOrGroups,
    templateApprovalSlaHours: templatesHub.templateApprovalSlaHours,
    templateApprovalStepAssignees: templatesHub.templateApprovalStepAssignees,
    templateApprovalSubmitting: templatesHub.templateApprovalSubmitting,
    templateDeleting: templatesHub.templateDeleting,
    templateImporting: templatesHub.templateImporting,
    templatePublishing: templatesHub.templatePublishing,
    templateRenaming: templatesHub.templateRenaming,
    templateRollbackSaving: templatesHub.templateRollbackSaving,
    templateSaving: templatesHub.templateSaving,
    templateSyncSources: templatesHub.templateSyncSources,
    templateSyncing: templatesHub.templateSyncing,
    templateVersionChangelog: templatesHub.templateVersionChangelog,
    templateVersionLabel: templatesHub.templateVersionLabel,
    templateVersionSaving: templatesHub.templateVersionSaving,
    toggleChangelogVisual: templatesHub.toggleChangelogVisual,
    toggleLock,
    transferTemplateApproval: templatesHub.transferTemplateApproval,
    uiProfile,
    volumePlanDiffChangeCount: diffHub.volumePlanDiffChangeCount,
    volumePlanDiffCollabRows: diffHub.volumePlanDiffCollabRows,
    volumePlanDiffExpanded: diffHub.volumePlanDiffExpanded,
    volumePlanDiffPreview: diffHub.volumePlanDiffPreview,
    volumePlanDiffShareLinkPreview: diffHub.volumePlanDiffShareLinkPreview,
    shareE2eApplyDone: diffHub.shareE2eApplyDone,
    pendingShareApply: diffHub.pendingShareApply,
    pendingShareMerge: diffHub.pendingShareMerge,
    showVolumePlanDiffPrintPreview: diffHub.showVolumePlanDiffPrintPreview,
    volumePlanDiffPrintPreviewText: diffHub.volumePlanDiffPrintPreviewText,
    dismissVolumePlanDiffShareLinkPreview: diffHub.dismissVolumePlanDiffShareLinkPreview,
    requestApplyVolumePlanDiffShareLink: diffHub.requestApplyVolumePlanDiffShareLink,
    confirmApplyVolumePlanDiffShareLink: diffHub.confirmApplyVolumePlanDiffShareLink,
    cancelApplyVolumePlanDiffShareLink: diffHub.cancelApplyVolumePlanDiffShareLink,
    confirmShareMergeUseShare: diffHub.confirmShareMergeUseShare,
    cancelShareMerge: diffHub.cancelShareMerge,
    printVolumePlanDiffPrintPreview: diffHub.printVolumePlanDiffPrintPreview,
    closeVolumePlanDiffPrintPreview: diffHub.closeVolumePlanDiffPrintPreview,
    volumePlanDiffTypeFilter: diffHub.volumePlanDiffTypeFilter,
    volumePlanDiffTypeOptions: diffHub.volumePlanDiffTypeOptions,
    volumePlanDiffVolumeFilter: diffHub.volumePlanDiffVolumeFilter,
    volumePlanDiffVolumeOptions: diffHub.volumePlanDiffVolumeOptions,
    volumePlanSaveConfirmOpen: diffHub.volumePlanSaveConfirmOpen,
    volumeTemplates: templatesHub.volumeTemplates,
  };

  return {
    panelContext,
    editableVolumes,
    showVolumePlanDiffPrintPreview: diffHub.showVolumePlanDiffPrintPreview,
    volumePlanDiffShareLinkPreview: diffHub.volumePlanDiffShareLinkPreview,
    pendingShareApply: diffHub.pendingShareApply,
    pendingShareMerge: diffHub.pendingShareMerge,
    shareE2eApplyDone: diffHub.shareE2eApplyDone,
    volumePlanDiffPrintPreviewText: diffHub.volumePlanDiffPrintPreviewText,
    loadVolumePlan,
    loadVolumeTemplates: templatesHub.loadVolumeTemplates,
    loadTemplateSyncSources: templatesHub.loadTemplateSyncSources,
    loadTemplateApprovals: templatesHub.loadTemplateApprovals,
    loadDiffCollabNotes: diffHub.loadDiffCollabNotes,
    refreshVolumePlanDiffPreview: diffHub.refreshVolumePlanDiffPreview,
    tryLoadVolumePlanDiffShareLinkPreview: diffHub.tryLoadVolumePlanDiffShareLinkPreview,
    dismissVolumePlanDiffShareLinkPreview: diffHub.dismissVolumePlanDiffShareLinkPreview,
    requestApplyVolumePlanDiffShareLink: diffHub.requestApplyVolumePlanDiffShareLink,
    confirmApplyVolumePlanDiffShareLink: diffHub.confirmApplyVolumePlanDiffShareLink,
    cancelApplyVolumePlanDiffShareLink: diffHub.cancelApplyVolumePlanDiffShareLink,
    confirmShareMergeUseShare: diffHub.confirmShareMergeUseShare,
    cancelShareMerge: diffHub.cancelShareMerge,
    closeVolumePlanDiffPrintPreview: diffHub.closeVolumePlanDiffPrintPreview,
    printVolumePlanDiffPrintPreview: diffHub.printVolumePlanDiffPrintPreview,
    applyVolumePlanDiffShareLink: diffHub.applyVolumePlanDiffShareLink,
    formatHistoryTime: templatesHub.formatHistoryTime,
  };
}
