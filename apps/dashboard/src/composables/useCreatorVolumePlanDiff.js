/**
 * useCreatorVolumePlanDiff — 卷纲 diff 预览、导出、分享与协作批注
 *
 * Phase 20 Task：抽出全部 2 个 .ts 子模块，本主 hook 改为组合 facade。
 * 下游 API（return shape）保持完全兼容。
 *
 * 子模块：
 * - useVolumePlanDiff     (卷纲 diff 预览 + 导出 + 打印 + 邮件 + collab notes)
 * - useVolumePlanDiffShare (分享链接解析/应用/合并冲突)
 *
 * 共享 ref（主 hook 编排）：
 * - volumePlanDiffPreview/filteredVolumePlanDiffChanges/diffCollabNotes:
 *   useVolumePlanDiff 拥有 → 通过 deps 共享给 useVolumePlanDiffShare
 */
import { ref } from 'vue';
import {
  useVolumePlanDiff,
  useVolumePlanDiffShare,
} from './useCreatorVolumePlanDiff/index.ts';

/**
 * @param {
 *   uiProfile: import('vue').ComputedRef<object>,
 *   saveMessage: import('vue').Ref<string>,
 *   wizardEmailTo: import('vue').Ref<string>,
 *   globalOutlineEditorRef: import('vue').Ref<HTMLElement|null>,
 *   editableVolumes: import('vue').Ref<object[]>,
 *   saving: import('vue').Ref<boolean>,
 * }} deps
 */
export function useCreatorVolumePlanDiff(deps) {
  const {
    uiProfile,
    saveMessage,
    wizardEmailTo,
    globalOutlineEditorRef,
    editableVolumes,
    saving,
  } = deps;

  // --- 1) Diff 子模块（提供 diffPreview/filteredChanges/collabNotes）---
  const diff = useVolumePlanDiff({
    uiProfile,
    saveMessage,
    wizardEmailTo,
    globalOutlineEditorRef,
    editableVolumes,
    saving,
  });

  // --- 2) Share 子模块（依赖 diff 提供物）---
  const share = useVolumePlanDiffShare({
    uiProfile,
    saveMessage,
    editableVolumes,
    saving,
    volumePlanDiffPreview: diff.volumePlanDiffPreview,
    filteredVolumePlanDiffChanges: diff.filteredVolumePlanDiffChanges,
    diffCollabNotes: diff.diffCollabNotes,
    loadDiffCollabNotes: diff.loadDiffCollabNotes,
    mergeIncomingDiffCollabNotes: diff.mergeIncomingDiffCollabNotes,
  });

  return {
    showVolumePlanDiffPrintPreview: diff.showVolumePlanDiffPrintPreview,
    volumePlanDiffShareLinkPreview: share.volumePlanDiffShareLinkPreview,
    pendingShareApply: share.pendingShareApply,
    pendingShareMerge: share.pendingShareMerge,
    shareE2eApplyDone: share.shareE2eApplyDone,
    diffCollabNotes: diff.diffCollabNotes,
    volumePlanDiffPrintPreviewText: diff.volumePlanDiffPrintPreviewText,
    volumePlanSaveConfirmOpen: share.volumePlanSaveConfirmOpen,
    volumePlanDiffPreview: diff.volumePlanDiffPreview,
    volumePlanDiffExpanded: diff.volumePlanDiffExpanded,
    volumePlanDiffTypeFilter: diff.volumePlanDiffTypeFilter,
    volumePlanDiffVolumeFilter: diff.volumePlanDiffVolumeFilter,
    volumePlanDiffChangeCount: diff.volumePlanDiffChangeCount,
    volumePlanDiffTypeOptions: diff.volumePlanDiffTypeOptions,
    volumePlanDiffVolumeOptions: diff.volumePlanDiffVolumeOptions,
    filteredVolumePlanDiffChanges: diff.filteredVolumePlanDiffChanges,
    refreshVolumePlanDiffPreview: diff.refreshVolumePlanDiffPreview,
    onVolumePlanDiffToggle: diff.onVolumePlanDiffToggle,
    jumpToGlobalOutlineEdit: diff.jumpToGlobalOutlineEdit,
    exportVolumePlanDiff: diff.exportVolumePlanDiff,
    shareVolumePlanDiffEmail: diff.shareVolumePlanDiffEmail,
    tryLoadVolumePlanDiffShareLinkPreview: share.tryLoadVolumePlanDiffShareLinkPreview,
    dismissVolumePlanDiffShareLinkPreview: share.dismissVolumePlanDiffShareLinkPreview,
    requestApplyVolumePlanDiffShareLink: share.requestApplyVolumePlanDiffShareLink,
    confirmApplyVolumePlanDiffShareLink: share.confirmApplyVolumePlanDiffShareLink,
    cancelApplyVolumePlanDiffShareLink: share.cancelApplyVolumePlanDiffShareLink,
    confirmShareMergeUseShare: share.confirmShareMergeUseShare,
    cancelShareMerge: share.cancelShareMerge,
    applyVolumePlanDiffShareLink: share.applyVolumePlanDiffShareLink,
    setDiffCollabNote: diff.setDiffCollabNote,
    loadDiffCollabNotes: diff.loadDiffCollabNotes,
    shareVolumePlanDiffLink: share.shareVolumePlanDiffLink,
    exportVolumePlanDiffMarkdown: diff.exportVolumePlanDiffMarkdown,
    exportVolumePlanDiffPdf: diff.exportVolumePlanDiffPdf,
    openVolumePlanDiffPrintPreview: diff.openVolumePlanDiffPrintPreview,
    closeVolumePlanDiffPrintPreview: diff.closeVolumePlanDiffPrintPreview,
    printVolumePlanDiffPrintPreview: diff.printVolumePlanDiffPrintPreview,
    exportVolumePlanDiffZip: diff.exportVolumePlanDiffZip,
    saving,
  };
}
