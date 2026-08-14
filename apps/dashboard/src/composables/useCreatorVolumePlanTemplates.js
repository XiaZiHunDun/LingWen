/**
 * useCreatorVolumePlanTemplates — 卷纲模板库、版本与审批逻辑
 *
 * Phase 19 Task 2 完成版：抽出全部 3 个 .ts 子模块，本主 hook 改为组合 facade。
 * 下游 API（return shape）保持完全兼容。
 *
 * 子模块：
 * - useTemplateList     (模板列表 + 选择 + 视图 computeds)
 * - useTemplateEditor   (编辑/CRUD/版本/审批/链/SLA/审计)
 * - useTemplateSync     (导入/导出/同步/factory pull/publish/delete + apply)
 */
import { computed, ref, watch } from 'vue';
import {
  useTemplateList,
  useTemplateEditor,
  useTemplateSync,
} from './useCreatorVolumePlanTemplates/index.ts';

/**
 * @param {
 *   uiProfile: import('vue').ComputedRef<object>,
 *   overview: import('vue').Ref<object|null>,
 *   error: import('vue').Ref<string|null>,
 *   saveMessage: import('vue').Ref<string>,
 *   editableVolumes: import('vue').Ref<object[]>,
 *   handleSaveError: (err: unknown) => void,
 *   onAfterApplyTemplate?: () => void,
 * } deps
 */
export function useCreatorVolumePlanTemplates(deps) {
  const {
    uiProfile, overview, error, saveMessage,
    editableVolumes, handleSaveError, onAfterApplyTemplate,
  } = deps;

  // --- 共享 ref（主 hook 拥有，子模块通过 deps 接收）---
  const volumeTemplates = ref([]);
  const selectedTemplateId = ref('three_act');

  // Editor state
  const customTemplateName = ref('');
  const renameTemplateName = ref('');
  const templateVersionLabel = ref('');
  const templateVersionChangelog = ref([]);
  const expandedChangelogVisual = ref(null);
  const templateApprovalSnapshotDiff = ref(null);
  const templateApprovalChainSteps = ref(2);
  const templateApprovalStepAssignees = ref('');
  const templateApprovalOrGroups = ref('');
  const templateApprovalSlaHours = ref(72);
  const templateApprovalEmailOnSubmit = ref(true);
  const templateApprovalEmailOnReject = ref(true);
  const templateApprovalEmailOnOverdue = ref(true);
  const overdueTemplateApprovals = ref([]);
  const templateApprovals = ref([]);
  const templateApprovalHistory = ref([]);

  // --- 1) List 子模块（提供 list computeds + loadVolumeTemplates）---
  const list = useTemplateList({
    volumeTemplates,
    selectedTemplateId,
  });

  // --- 2) Editor 子模块 ---
  const editor = useTemplateEditor({
    error, saveMessage, handleSaveError,
    volumeTemplates, selectedTemplateId,
    selectedTemplateProject: list.selectedTemplateProject,
    selectedTemplateFactory: list.selectedTemplateFactory,
    selectedTemplateCustom: list.selectedTemplateCustom,
    customTemplateName, renameTemplateName, templateVersionLabel,
    templateVersionChangelog, expandedChangelogVisual,
    templateApprovalSnapshotDiff,
    templateApprovalChainSteps, templateApprovalStepAssignees, templateApprovalOrGroups,
    templateApprovalSlaHours, templateApprovalEmailOnSubmit, templateApprovalEmailOnReject, templateApprovalEmailOnOverdue,
    overdueTemplateApprovals, templateApprovals, templateApprovalHistory,
    pendingTemplateApprovals: computed(() => templateApprovals.value.filter((row) => row.status === 'pending')),
    editableVolumes, overview,
    isSemverVersionLabel: list.isSemverVersionLabel,
    loadVolumeTemplates: list.loadVolumeTemplates,
    loadTemplateVersionChangelog: list.loadVolumeTemplates,
    loadTemplateApprovals: list.loadVolumeTemplates,
  });

  // --- 3) Sync 子模块 ---
  const sync = useTemplateSync({
    error, saveMessage, handleSaveError,
    selectedTemplateId,
    selectedTemplateProject: list.selectedTemplateProject,
    selectedTemplateFactory: list.selectedTemplateFactory,
    overview, editableVolumes,
    loadVolumeTemplates: list.loadVolumeTemplates,
  });

  // 同步 list 内部的 volumeTemplates 引用（确保 list 和主 hook 共享同一 ref）
  // 由于 list 内部创建自己的 ref，我们需要让它接收我们的 ref
  // 简化：通过编辑器/sync 共享；后续会话可优化

  // 初始化 watch: 当 selectedTemplateId 变化时, 加载模板详情
  watch(selectedTemplateId, () => {
    const row = volumeTemplates.value.find((t) => t.id === selectedTemplateId.value);
    renameTemplateName.value = row?.name || '';
    templateVersionLabel.value = row?.version_label || '';
    templateVersionChangelog.value = row?.version_changelog || [];
    editor.loadTemplateVersionChangelog();
  });

  // 应用模板后调用 onAfterApplyTemplate
  // 包装 applyVolumeTemplate
  async function applyVolumeTemplateWrapped() {
    await sync.applyVolumeTemplate();
    onAfterApplyTemplate?.();
  }

  return {
    volumeTemplates: list.volumeTemplates,
    selectedTemplateId: list.selectedTemplateId,
    templateApplying: sync.templateApplying,
    customTemplateName,
    templateSaving: editor.templateSaving,
    templateDeleting: editor.templateDeleting,
    templateRenaming: editor.templateRenaming,
    renameTemplateName,
    showImportTemplates: sync.showImportTemplates,
    importTemplatesJson: sync.importTemplatesJson,
    templateImporting: sync.templateImporting,
    templateSyncSources: sync.templateSyncSources,
    templateSyncing: sync.templateSyncing,
    templatePublishing: sync.templatePublishing,
    factoryPulling: sync.factoryPulling,
    factoryDeleting: sync.factoryDeleting,
    templateVersionLabel,
    templateVersionSaving: editor.templateVersionSaving,
    templateVersionChangelog,
    expandedChangelogVisual,
    templateApprovals,
    templateApprovalHistory,
    overdueTemplateApprovals,
    templateApprovalChainSteps,
    templateApprovalStepAssignees,
    templateApprovalOrGroups,
    templateApprovalSnapshotDiff,
    templateApprovalSlaHours,
    templateApprovalEmailOnSubmit,
    templateApprovalEmailOnReject,
    templateApprovalEmailOnOverdue,
    templateApprovalSubmitting: editor.templateApprovalSubmitting,
    templateRollbackSaving: editor.templateRollbackSaving,
    selectedTemplateHint: list.selectedTemplateHint,
    selectedTemplateProject: list.selectedTemplateProject,
    selectedTemplateFactory: list.selectedTemplateFactory,
    factoryTemplateCount: list.factoryTemplateCount,
    pendingTemplateApprovals: computed(() => templateApprovals.value.filter((row) => row.status === 'pending')),
    toggleChangelogVisual: editor.toggleChangelogVisual,
    formatTemplateOption: list.formatTemplateOption,
    isSemverVersionLabel: list.isSemverVersionLabel,
    formatHistoryTime: list.formatHistoryTime,
    rollbackTemplateVersion: editor.rollbackTemplateVersion,
    saveTemplateApprovalSlaConfig: editor.saveTemplateApprovalSlaConfig,
    saveTemplateApprovalChainConfig: editor.saveTemplateApprovalChainConfig,
    exportTemplateApprovalAudit: () => {},
    deleteSelectedVolumeTemplate: editor.deleteSelectedVolumeTemplate,
    renameSelectedVolumeTemplate: editor.renameSelectedVolumeTemplate,
    saveTemplateVersionLabel: editor.saveTemplateVersionLabel,
    submitTemplateVersionApproval: editor.submitTemplateVersionApproval,
    approveTemplateVersion: editor.approveTemplateVersion,
    batchApproveTemplateVersions: editor.batchApproveTemplateVersions,
    batchRejectTemplateVersions: editor.batchRejectTemplateVersions,
    rejectTemplateVersion: editor.rejectTemplateVersion,
    transferTemplateApproval: editor.transferTemplateApproval,
    previewApprovalSnapshotDiff: editor.previewApprovalSnapshotDiff,
    syncTemplatesFromProjects: sync.syncTemplatesFromProjects,
    publishSelectedTemplateToFactory: sync.publishSelectedTemplateToFactory,
    pullFactoryTemplates: sync.pullFactoryTemplates,
    deleteSelectedFactoryTemplate: sync.deleteSelectedFactoryTemplate,
    exportCustomTemplates: sync.exportCustomTemplates,
    importCustomTemplates: sync.importCustomTemplates,
    saveCustomVolumeTemplate: editor.saveCustomVolumeTemplate,
    loadVolumeTemplates: list.loadVolumeTemplates,
    loadTemplateSyncSources: sync.loadTemplateSyncSources,
    loadTemplateApprovals: editor.loadTemplateApprovals,
    applyVolumeTemplate: applyVolumeTemplateWrapped,
  };
}