/**
 * useCreatorVolumePlanTemplates — 卷纲模板库、版本与审批逻辑
 */
import { computed, ref, watch } from 'vue';
import {
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
} from '../api/index.js';
import { formatDisplayLabel, normalizeVolumePlanVolumes } from '../utils/displayProjectName.js';

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
    uiProfile,
    overview,
    error,
    saveMessage,
    editableVolumes,
    handleSaveError,
    onAfterApplyTemplate,
  } = deps;

  const volumeTemplates = ref([]);

  const selectedTemplateId = ref('three_act');

  const templateApplying = ref(false);

  const customTemplateName = ref('');

  const templateSaving = ref(false);

  const templateDeleting = ref(false);

  const templateRenaming = ref(false);

  const renameTemplateName = ref('');

  const showImportTemplates = ref(false);

  const importTemplatesJson = ref('');

  const templateImporting = ref(false);

  const templateSyncSources = ref([]);

  const templateSyncing = ref(false);

  const templatePublishing = ref(false);

  const factoryPulling = ref(false);

  const factoryDeleting = ref(false);

  const templateVersionLabel = ref('');

  const templateVersionSaving = ref(false);

  const templateVersionChangelog = ref([]);

  const expandedChangelogVisual = ref(null);

  const templateApprovals = ref([]);

  const templateApprovalHistory = ref([]);

  const overdueTemplateApprovals = ref([]);

  const templateApprovalChainSteps = ref(2);

  const templateApprovalStepAssignees = ref('');

  const templateApprovalOrGroups = ref('');

  const templateApprovalSnapshotDiff = ref(null);

  const templateApprovalSlaHours = ref(72);

  const templateApprovalEmailOnSubmit = ref(true);

  const templateApprovalEmailOnReject = ref(true);

  const templateApprovalEmailOnOverdue = ref(true);

  const templateApprovalSubmitting = ref(false);

  const templateRollbackSaving = ref(false);

  const versionSemverPattern = /^v?\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9][a-zA-Z0-9.-]*)?$/i;

  const selectedTemplateHint = computed(() => {
    const row = volumeTemplates.value.find((t) => t.id === selectedTemplateId.value);
    return row?.description || '';
  });

  const selectedTemplateProject = computed(() => {
    const row = volumeTemplates.value.find((t) => t.id === selectedTemplateId.value);
    return row?.scope === 'project';
  });

  const selectedTemplateFactory = computed(() => {
    const row = volumeTemplates.value.find((t) => t.id === selectedTemplateId.value);
    return row?.scope === 'factory';
  });

  const factoryTemplateCount = computed(() => volumeTemplates.value.filter((t) => t.scope === 'factory').length);

  const pendingTemplateApprovals = computed(() =>
    templateApprovals.value.filter((row) => row.status === 'pending'),
  );

  const selectedTemplateCustom = computed(() => selectedTemplateProject.value);

  watch(selectedTemplateId, () => {
    const row = volumeTemplates.value.find((t) => t.id === selectedTemplateId.value);
    renameTemplateName.value = row?.name || '';
    templateVersionLabel.value = row?.version_label || '';
    templateVersionChangelog.value = row?.version_changelog || [];
    loadTemplateVersionChangelog();
  });

  function toggleChangelogVisual(index) {
    expandedChangelogVisual.value = expandedChangelogVisual.value === index ? null : index;
  }

  function formatTemplateOption(template) {
    if (template.version_label) {
      const prefix = template.version_semver_valid === false ? '!' : '';
      return `${prefix}[${template.version_label}] ${template.name}`;
    }
    return template.name;
  }

  function isSemverVersionLabel(label) {
    return versionSemverPattern.test(String(label || '').trim());
  }

  function formatHistoryTime(iso) {
    if (!iso) return '';
    try {
      return new Date(iso).toLocaleString('zh-CN', { hour12: false });
    } catch {
      return iso;
    }
  }

  async function loadTemplateVersionChangelog() {
    if (!selectedTemplateProject.value && !selectedTemplateFactory.value) {
      templateVersionChangelog.value = [];
      return;
    }
    try {
      const data = await fetchCreatorVolumeTemplateChangelog(selectedTemplateId.value);
      templateVersionChangelog.value = data.entries || [];
    } catch {
      const row = volumeTemplates.value.find((t) => t.id === selectedTemplateId.value);
      templateVersionChangelog.value = row?.version_changelog || [];
    }
  }

  async function rollbackTemplateVersion(entry, changelogIndex) {
    if (!selectedTemplateId.value) return;
    templateRollbackSaving.value = true;
    error.value = null;
    try {
      await rollbackCreatorVolumeTemplate(selectedTemplateId.value, {
        version_label: entry.version_label || undefined,
        changelog_index: changelogIndex,
      });
      saveMessage.value = `已回滚到 ${entry.version_label || '选定版本'}`;
      await loadVolumeTemplates();
      await loadTemplateVersionChangelog();
    } catch (e) {
      handleSaveError(e);
    } finally {
      templateRollbackSaving.value = false;
    }
  }

  async function loadTemplateApprovalChainConfig() {
    try {
      const data = await fetchCreatorTemplateApprovalChainConfig();
      templateApprovalChainSteps.value = data.required_steps || 2;
      templateApprovalStepAssignees.value = (data.step_assignees || []).join(', ');
      if (data.step_assignee_groups?.length) {
        templateApprovalOrGroups.value = data.step_assignee_groups
          .map((group) => group.join('|'))
          .join(',');
      }
      const sla = await fetchCreatorTemplateApprovalSlaConfig();
      templateApprovalSlaHours.value = sla.timeout_hours || 72;
      templateApprovalEmailOnSubmit.value = Boolean(sla.email_on_submit);
      templateApprovalEmailOnReject.value = Boolean(sla.email_on_reject);
      templateApprovalEmailOnOverdue.value = Boolean(sla.email_on_overdue);
      const overdue = await fetchCreatorTemplateApprovalOverdue();
      overdueTemplateApprovals.value = overdue.approvals || [];
    } catch {
      templateApprovalChainSteps.value = 2;
      templateApprovalSlaHours.value = 72;
      overdueTemplateApprovals.value = [];
    }
  }

  async function saveTemplateApprovalSlaConfig() {
    try {
      await saveCreatorTemplateApprovalSlaConfig({
        timeout_hours: templateApprovalSlaHours.value,
        email_on_submit: templateApprovalEmailOnSubmit.value,
        email_on_reject: templateApprovalEmailOnReject.value,
        email_on_overdue: templateApprovalEmailOnOverdue.value,
      });
      saveMessage.value = `已保存审批 SLA（${templateApprovalSlaHours.value}h）`;
      await loadTemplateApprovalChainConfig();
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function saveTemplateApprovalChainConfig() {
    try {
      const assignees = templateApprovalStepAssignees.value
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
      const orGroups = templateApprovalOrGroups.value
        .split(',')
        .map((step) => step.split('|').map((s) => s.trim()).filter(Boolean))
        .filter((group) => group.length);
      const data = await saveCreatorTemplateApprovalChainConfig({
        required_steps: templateApprovalChainSteps.value,
        step_assignees: assignees,
        step_assignee_groups: orGroups.length ? orGroups : undefined,
      });
      templateApprovalChainSteps.value = data.required_steps || 2;
      templateApprovalStepAssignees.value = (data.step_assignees || []).join(', ');
      saveMessage.value = `已保存审批链（${templateApprovalChainSteps.value} 步）`;
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function loadTemplateApprovals() {
    try {
      const data = await fetchCreatorTemplateApprovals({ status: 'pending' });
      templateApprovals.value = data.approvals || [];
      const history = await fetchCreatorTemplateApprovalHistory();
      templateApprovalHistory.value = history.approvals || [];
      await loadTemplateApprovalChainConfig();
    } catch {
      templateApprovals.value = [];
      templateApprovalHistory.value = [];
    }
  }

  async function exportTemplateApprovalAudit() {
    try {
      const data = await exportCreatorTemplateApprovalAudit();
      const text = JSON.stringify(data, null, 2);
      if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
        saveMessage.value = `已导出 ${data.count} 条审批审计`;
      } else {
        saveMessage.value = `已导出 ${data.count} 条审批审计（无剪贴板）`;
      }
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function deleteSelectedVolumeTemplate() {
    if (!selectedTemplateCustom.value) return;
    templateDeleting.value = true;
    error.value = null;
    try {
      const deletedId = selectedTemplateId.value;
      await deleteCreatorVolumeTemplate(deletedId);
      saveMessage.value = '已删除自定义模板';
      await loadVolumeTemplates();
      if (!volumeTemplates.value.some((t) => t.id === deletedId)) {
        selectedTemplateId.value = volumeTemplates.value[0]?.id || 'three_act';
      }
    } catch (e) {
      handleSaveError(e);
    } finally {
      templateDeleting.value = false;
    }
  }

  async function renameSelectedVolumeTemplate() {
    if (!selectedTemplateCustom.value || !renameTemplateName.value.trim()) return;
    templateRenaming.value = true;
    error.value = null;
    try {
      const renamed = await renameCreatorVolumeTemplate(selectedTemplateId.value, {
        name: renameTemplateName.value.trim(),
      });
      saveMessage.value = `已重命名为「${renamed.name}」`;
      await loadVolumeTemplates();
      selectedTemplateId.value = renamed.id;
    } catch (e) {
      handleSaveError(e);
    } finally {
      templateRenaming.value = false;
    }
  }

  async function saveTemplateVersionLabel() {
    if (!selectedTemplateProject.value && !selectedTemplateFactory.value) return;
    if (templateVersionLabel.value.trim() && !isSemverVersionLabel(templateVersionLabel.value)) {
      saveMessage.value = '版本标签需符合 semver（如 v1.2.0）';
      return;
    }
    templateVersionSaving.value = true;
    error.value = null;
    try {
      await setCreatorVolumeTemplateVersion(selectedTemplateId.value, {
        version_label: templateVersionLabel.value.trim() || null,
      });
      saveMessage.value = '已更新版本标签';
      await loadVolumeTemplates();
      await loadTemplateVersionChangelog();
    } catch (e) {
      handleSaveError(e);
    } finally {
      templateVersionSaving.value = false;
    }
  }

  async function submitTemplateVersionApproval() {
    if (!selectedTemplateId.value) return;
    if (templateVersionLabel.value.trim() && !isSemverVersionLabel(templateVersionLabel.value)) {
      saveMessage.value = '版本标签需符合 semver（如 v1.2.0）';
      return;
    }
    templateApprovalSubmitting.value = true;
    error.value = null;
    try {
      await submitCreatorTemplateVersionApproval(selectedTemplateId.value, {
        version_label: templateVersionLabel.value.trim() || null,
      });
      saveMessage.value = '已提交版本变更审批';
      await loadTemplateApprovals();
    } catch (e) {
      handleSaveError(e);
    } finally {
      templateApprovalSubmitting.value = false;
    }
  }

  async function approveTemplateVersion(approvalId) {
    try {
      const drift = await fetchCreatorTemplateApprovalSnapshotDrift(approvalId);
      let force = false;
      if (drift.drifted) {
        const ok = window.confirm('审批快照与当前卷纲不一致，仍要批准？');
        if (!ok) {
          saveMessage.value = '已取消批准（快照漂移）';
          return;
        }
        force = true;
      }
      const result = await approveCreatorTemplateApproval(approvalId, { force });
      saveMessage.value = result.chain_advanced
        ? `审批链进度 ${result.chain_progress}`
        : '已批准版本变更';
      await loadTemplateApprovals();
      if (!result.chain_advanced) {
        await loadVolumeTemplates();
        await loadTemplateVersionChangelog();
      }
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function batchApproveTemplateVersions() {
    const ids = pendingTemplateApprovals.value.map((row) => row.id);
    if (!ids.length) return;
    try {
      const force = window.confirm('批量批准全部待审批项？若存在快照漂移将自动 force。');
      if (!force) return;
      const result = await batchApproveCreatorTemplateApprovals({
        approval_ids: ids,
        force: true,
      });
      saveMessage.value = `批量批准：${result.approved}/${result.total}`;
      await loadTemplateApprovals();
      await loadVolumeTemplates();
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function batchRejectTemplateVersions() {
    const ids = pendingTemplateApprovals.value.map((row) => row.id);
    if (!ids.length) return;
    try {
      const result = await batchRejectCreatorTemplateApprovals({
        approval_ids: ids,
        reason: '批量驳回',
      });
      saveMessage.value = `批量驳回：${result.rejected}/${result.total}`;
      await loadTemplateApprovals();
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function rejectTemplateVersion(approvalId) {
    try {
      await rejectCreatorTemplateApproval(approvalId, { reason: '驳回' });
      saveMessage.value = '已驳回版本变更';
      await loadTemplateApprovals();
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function transferTemplateApproval(approvalId) {
    const toAssignee = window.prompt('转交给（审批人 ID）');
    if (!toAssignee?.trim()) return;
    try {
      await transferCreatorTemplateApproval(approvalId, {
        to_assignee: toAssignee.trim(),
        note: '委派转交',
      });
      saveMessage.value = `已转交给 ${toAssignee.trim()}`;
      await loadTemplateApprovals();
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function previewApprovalSnapshotDiff(approvalId) {
    try {
      templateApprovalSnapshotDiff.value = await fetchCreatorTemplateApprovalSnapshotDiff(approvalId);
      const summary = templateApprovalSnapshotDiff.value?.diff_summary;
      saveMessage.value = summary?.changed
        ? `快照 diff：+${summary.lines_added} / -${summary.lines_removed}`
        : '快照与当前卷纲一致';
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function syncTemplatesFromProjects() {
    templateSyncing.value = true;
    error.value = null;
    try {
      if (!templateSyncSources.value.length) {
        await loadTemplateSyncSources();
      }
      const slugs = templateSyncSources.value.map((s) => s.slug);
      if (!slugs.length) {
        saveMessage.value = '没有其他项目的自定义模板';
        return;
      }
      const result = await syncCreatorVolumeTemplates({ source_slugs: slugs });
      saveMessage.value = `已从 ${result.sources.length} 个项目同步 ${result.imported} 个模板`;
      await loadVolumeTemplates();
      await loadTemplateSyncSources();
    } catch (e) {
      handleSaveError(e);
    } finally {
      templateSyncing.value = false;
    }
  }

  async function publishSelectedTemplateToFactory() {
    if (!selectedTemplateProject.value) return;
    templatePublishing.value = true;
    error.value = null;
    try {
      await publishCreatorVolumeTemplateToFactory({ template_id: selectedTemplateId.value });
      saveMessage.value = '已发布到工厂模板库';
      await loadVolumeTemplates();
    } catch (e) {
      handleSaveError(e);
    } finally {
      templatePublishing.value = false;
    }
  }

  async function pullFactoryTemplates() {
    const ids = volumeTemplates.value.filter((t) => t.scope === 'factory').map((t) => t.id);
    if (!ids.length) return;
    factoryPulling.value = true;
    error.value = null;
    try {
      const result = await pullCreatorFactoryVolumeTemplates({ template_ids: ids });
      saveMessage.value = `已从工厂库拉取 ${result.imported} 个模板`;
      await loadVolumeTemplates();
    } catch (e) {
      handleSaveError(e);
    } finally {
      factoryPulling.value = false;
    }
  }

  async function deleteSelectedFactoryTemplate() {
    if (!selectedTemplateFactory.value) return;
    factoryDeleting.value = true;
    error.value = null;
    try {
      await deleteCreatorFactoryVolumeTemplate(selectedTemplateId.value);
      saveMessage.value = '已从工厂库删除模板';
      await loadVolumeTemplates();
      selectedTemplateId.value = volumeTemplates.value[0]?.id || 'three_act';
    } catch (e) {
      handleSaveError(e);
    } finally {
      factoryDeleting.value = false;
    }
  }

  async function exportCustomTemplates() {
    error.value = null;
    try {
      const data = await exportCreatorVolumeTemplates();
      const text = JSON.stringify(data, null, 2);
      importTemplatesJson.value = text;
      if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
        saveMessage.value = `已导出 ${data.count} 个模板并复制到剪贴板`;
      } else {
        saveMessage.value = `已导出 ${data.count} 个模板（见导入框）`;
        showImportTemplates.value = true;
      }
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function importCustomTemplates() {
    templateImporting.value = true;
    error.value = null;
    try {
      const payload = JSON.parse(importTemplatesJson.value);
      const templates = payload.templates || payload;
      const result = await importCreatorVolumeTemplates({
        templates: Array.isArray(templates) ? templates : [],
        replace: false,
      });
      saveMessage.value = `已导入 ${result.imported} 个模板（共 ${result.total} 个）`;
      importTemplatesJson.value = '';
      showImportTemplates.value = false;
      await loadVolumeTemplates();
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      templateImporting.value = false;
    }
  }

  async function saveCustomVolumeTemplate() {
    if (!customTemplateName.value.trim() || !editableVolumes.value.length) return;
    templateSaving.value = true;
    error.value = null;
    try {
      const saved = await saveCreatorVolumeTemplate({
        name: customTemplateName.value.trim(),
        volumes: editableVolumes.value,
        max_chapter: overview.value?.max_chapter,
      });
      saveMessage.value = `已保存模板「${saved.name}」`;
      customTemplateName.value = '';
      await loadVolumeTemplates();
      selectedTemplateId.value = saved.id;
    } catch (e) {
      handleSaveError(e);
    } finally {
      templateSaving.value = false;
    }
  }

  async function loadVolumeTemplates() {
    try {
      const data = await fetchCreatorVolumeTemplates();
      volumeTemplates.value = data.templates || [];
      if (volumeTemplates.value.length && !volumeTemplates.value.some((t) => t.id === selectedTemplateId.value)) {
        selectedTemplateId.value = volumeTemplates.value[0].id;
      }
    } catch {
      volumeTemplates.value = [];
    }
  }

  async function loadTemplateSyncSources() {
    try {
      const data = await fetchCreatorVolumeTemplateSyncSources();
      templateSyncSources.value = data.sources || [];
    } catch {
      templateSyncSources.value = [];
    }
  }

  async function applyVolumeTemplate() {
    templateApplying.value = true;
    error.value = null;
    try {
      const result = await applyCreatorVolumeTemplate({
        template_id: selectedTemplateId.value,
        max_chapter: overview.value?.max_chapter,
      });
      editableVolumes.value = normalizeVolumePlanVolumes(result.volumes);
      onAfterApplyTemplate?.();
      saveMessage.value = `已套用模板「${result.template_name}」，请保存卷纲`;
    } catch (e) {
      handleSaveError(e);
    } finally {
      templateApplying.value = false;
    }
  }

  return {
    volumeTemplates,
    selectedTemplateId,
    templateApplying,
    customTemplateName,
    templateSaving,
    templateDeleting,
    templateRenaming,
    renameTemplateName,
    showImportTemplates,
    importTemplatesJson,
    templateImporting,
    templateSyncSources,
    templateSyncing,
    templatePublishing,
    factoryPulling,
    factoryDeleting,
    templateVersionLabel,
    templateVersionSaving,
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
    templateApprovalSubmitting,
    templateRollbackSaving,
    selectedTemplateHint,
    selectedTemplateProject,
    selectedTemplateFactory,
    factoryTemplateCount,
    pendingTemplateApprovals,
    toggleChangelogVisual,
    formatTemplateOption,
    isSemverVersionLabel,
    formatHistoryTime,
    rollbackTemplateVersion,
    saveTemplateApprovalSlaConfig,
    saveTemplateApprovalChainConfig,
    exportTemplateApprovalAudit,
    deleteSelectedVolumeTemplate,
    renameSelectedVolumeTemplate,
    saveTemplateVersionLabel,
    submitTemplateVersionApproval,
    approveTemplateVersion,
    batchApproveTemplateVersions,
    batchRejectTemplateVersions,
    rejectTemplateVersion,
    transferTemplateApproval,
    previewApprovalSnapshotDiff,
    syncTemplatesFromProjects,
    publishSelectedTemplateToFactory,
    pullFactoryTemplates,
    deleteSelectedFactoryTemplate,
    exportCustomTemplates,
    importCustomTemplates,
    saveCustomVolumeTemplate,
    loadVolumeTemplates,
    loadTemplateSyncSources,
    loadTemplateApprovals,
    applyVolumeTemplate,
  };
}
