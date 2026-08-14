/**
 * useTemplateEditor — 模板编辑 + 版本 + 审批
 *
 * Phase 19 Task 2.2：从 useCreatorVolumePlanTemplates.js 拆出（完整实现）。
 * 负责: CRUD（save/delete/rename）+ 版本标签/changelog/回滚 +
 *       审批（提交/批准/批量/驳回/转交/快照 diff）+ 审批链配置 + SLA。
 */
import { ref } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import {
  saveCreatorVolumeTemplate,
  deleteCreatorVolumeTemplate,
  renameCreatorVolumeTemplate,
  setCreatorVolumeTemplateVersion,
  fetchCreatorVolumeTemplateChangelog,
  rollbackCreatorVolumeTemplate,
  submitCreatorTemplateVersionApproval,
  approveCreatorTemplateApproval,
  batchApproveCreatorTemplateApprovals,
  batchRejectCreatorTemplateApprovals,
  rejectCreatorTemplateApproval,
  transferCreatorTemplateApproval,
  fetchCreatorTemplateApprovalSnapshotDiff,
  fetchCreatorTemplateApprovalSnapshotDrift,
  fetchCreatorTemplateApprovals,
  fetchCreatorTemplateApprovalHistory,
  fetchCreatorTemplateApprovalChainConfig,
  saveCreatorTemplateApprovalChainConfig,
  fetchCreatorTemplateApprovalSlaConfig,
  saveCreatorTemplateApprovalSlaConfig,
  fetchCreatorTemplateApprovalOverdue,
} from '../../api/index.js';

interface TemplateRow {
  id: string;
  name: string;
  scope?: string;
  version_label?: string;
  version_changelog?: Array<Record<string, unknown>>;
}

interface ApprovalEntry {
  id: string;
  status?: string;
}

interface ApprovalChainConfig {
  required_steps?: number;
  step_assignees?: string[];
  step_assignee_groups?: string[][];
}

interface ApprovalSlaConfig {
  timeout_hours?: number;
  email_on_submit?: boolean;
  email_on_reject?: boolean;
  email_on_overdue?: boolean;
}

export interface TemplateEditorDeps {
  error: Ref<string | null>;
  saveMessage: Ref<string>;
  handleSaveError: (err: unknown) => void;
  // 共享 ref（由主 hook 拥有）
  volumeTemplates: Ref<TemplateRow[]>;
  selectedTemplateId: Ref<string>;
  selectedTemplateProject: ComputedRef<boolean>;
  selectedTemplateFactory: ComputedRef<boolean>;
  selectedTemplateCustom: ComputedRef<boolean>;
  // 编辑 state
  customTemplateName: Ref<string>;
  renameTemplateName: Ref<string>;
  templateVersionLabel: Ref<string>;
  templateVersionChangelog: Ref<Array<Record<string, unknown>>>;
  expandedChangelogVisual: Ref<number | null>;
  templateApprovalSnapshotDiff: Ref<unknown>;
  templateApprovalChainSteps: Ref<number>;
  templateApprovalStepAssignees: Ref<string>;
  templateApprovalOrGroups: Ref<string>;
  templateApprovalSlaHours: Ref<number>;
  templateApprovalEmailOnSubmit: Ref<boolean>;
  templateApprovalEmailOnReject: Ref<boolean>;
  templateApprovalEmailOnOverdue: Ref<boolean>;
  overdueTemplateApprovals: Ref<Array<Record<string, unknown>>>;
  templateApprovals: Ref<ApprovalEntry[]>;
  templateApprovalHistory: Ref<Array<Record<string, unknown>>>;
  pendingTemplateApprovals: ComputedRef<ApprovalEntry[]>;
  // 调用依赖
  editableVolumes: Ref<Array<Record<string, unknown>>>;
  overview: Ref<Record<string, unknown> | null>;
  isSemverVersionLabel: (label: string) => boolean;
  loadVolumeTemplates: () => Promise<void>;
  loadTemplateVersionChangelog: () => Promise<void>;
  loadTemplateApprovals: () => Promise<void>;
}

export interface TemplateEditorReturn {
  templateSaving: Ref<boolean>;
  templateDeleting: Ref<boolean>;
  templateRenaming: Ref<boolean>;
  templateVersionSaving: Ref<boolean>;
  templateRollbackSaving: Ref<boolean>;
  templateApprovalSubmitting: Ref<boolean>;
  saveCustomVolumeTemplate: () => Promise<void>;
  deleteSelectedVolumeTemplate: () => Promise<void>;
  renameSelectedVolumeTemplate: () => Promise<void>;
  saveTemplateVersionLabel: () => Promise<void>;
  loadTemplateVersionChangelog: () => Promise<void>;
  rollbackTemplateVersion: (entry: Record<string, unknown>, index: number) => Promise<void>;
  toggleChangelogVisual: (index: number) => void;
  submitTemplateVersionApproval: () => Promise<void>;
  approveTemplateVersion: (approvalId: string) => Promise<void>;
  batchApproveTemplateVersions: () => Promise<void>;
  batchRejectTemplateVersions: () => Promise<void>;
  rejectTemplateVersion: (approvalId: string) => Promise<void>;
  transferTemplateApproval: (approvalId: string) => Promise<void>;
  previewApprovalSnapshotDiff: (approvalId: string) => Promise<void>;
  loadTemplateApprovals: () => Promise<void>;
  loadTemplateApprovalChainConfig: () => Promise<void>;
  saveTemplateApprovalChainConfig: () => Promise<void>;
  saveTemplateApprovalSlaConfig: () => Promise<void>;
}

export function useTemplateEditor(deps: TemplateEditorDeps): TemplateEditorReturn {
  const {
    error, saveMessage, handleSaveError,
    volumeTemplates, selectedTemplateId, selectedTemplateProject, selectedTemplateFactory, selectedTemplateCustom,
    customTemplateName, renameTemplateName, templateVersionLabel, templateVersionChangelog,
    expandedChangelogVisual, templateApprovalSnapshotDiff,
    templateApprovalChainSteps, templateApprovalStepAssignees, templateApprovalOrGroups,
    templateApprovalSlaHours, templateApprovalEmailOnSubmit, templateApprovalEmailOnReject, templateApprovalEmailOnOverdue,
    overdueTemplateApprovals, templateApprovals, templateApprovalHistory, pendingTemplateApprovals,
    editableVolumes, overview, isSemverVersionLabel,
    loadVolumeTemplates, loadTemplateVersionChangelog, loadTemplateApprovals,
  } = deps;

  const templateSaving = ref(false);
  const templateDeleting = ref(false);
  const templateRenaming = ref(false);
  const templateVersionSaving = ref(false);
  const templateRollbackSaving = ref(false);
  const templateApprovalSubmitting = ref(false);

  async function saveCustomVolumeTemplate(): Promise<void> {
    if (!customTemplateName.value.trim() || !editableVolumes.value.length) return;
    templateSaving.value = true;
    error.value = null;
    try {
      const saved = await saveCreatorVolumeTemplate({
        name: customTemplateName.value.trim(),
        volumes: editableVolumes.value,
        max_chapter: (overview.value as { max_chapter?: number } | null)?.max_chapter,
      }) as { id: string; name: string };
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

  async function deleteSelectedVolumeTemplate(): Promise<void> {
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

  async function renameSelectedVolumeTemplate(): Promise<void> {
    if (!selectedTemplateCustom.value || !renameTemplateName.value.trim()) return;
    templateRenaming.value = true;
    error.value = null;
    try {
      const renamed = await renameCreatorVolumeTemplate(selectedTemplateId.value, {
        name: renameTemplateName.value.trim(),
      }) as { id: string; name: string };
      saveMessage.value = `已重命名为「${renamed.name}」`;
      await loadVolumeTemplates();
      selectedTemplateId.value = renamed.id;
    } catch (e) {
      handleSaveError(e);
    } finally {
      templateRenaming.value = false;
    }
  }

  async function saveTemplateVersionLabel(): Promise<void> {
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

  async function loadTemplateVersionChangelogFn(): Promise<void> {
    if (!selectedTemplateProject.value && !selectedTemplateFactory.value) {
      templateVersionChangelog.value = [];
      return;
    }
    try {
      const data = await fetchCreatorVolumeTemplateChangelog(selectedTemplateId.value) as { entries?: Array<Record<string, unknown>> };
      templateVersionChangelog.value = data.entries || [];
    } catch {
      const row = volumeTemplates.value.find((t) => t.id === selectedTemplateId.value);
      templateVersionChangelog.value = row?.version_changelog || [];
    }
  }

  async function rollbackTemplateVersion(entry: Record<string, unknown>, changelogIndex: number): Promise<void> {
    if (!selectedTemplateId.value) return;
    templateRollbackSaving.value = true;
    error.value = null;
    try {
      await rollbackCreatorVolumeTemplate(selectedTemplateId.value, {
        version_label: (entry.version_label as string) || undefined,
        changelog_index: changelogIndex,
      });
      saveMessage.value = `已回滚到 ${entry.version_label || '选定版本'}`;
      await loadVolumeTemplates();
      await loadTemplateVersionChangelogFn();
    } catch (e) {
      handleSaveError(e);
    } finally {
      templateRollbackSaving.value = false;
    }
  }

  function toggleChangelogVisual(index: number): void {
    expandedChangelogVisual.value = expandedChangelogVisual.value === index ? null : index;
  }

  async function submitTemplateVersionApproval(): Promise<void> {
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

  async function approveTemplateVersion(approvalId: string): Promise<void> {
    try {
      const drift = await fetchCreatorTemplateApprovalSnapshotDrift(approvalId) as { drifted?: boolean };
      let force = false;
      if (drift.drifted) {
        const ok = window.confirm('审批快照与当前卷纲不一致，仍要批准？');
        if (!ok) {
          saveMessage.value = '已取消批准（快照漂移）';
          return;
        }
        force = true;
      }
      const result = await approveCreatorTemplateApproval(approvalId, { force }) as { chain_advanced?: boolean; chain_progress?: string };
      saveMessage.value = result.chain_advanced
        ? `审批链进度 ${result.chain_progress}`
        : '已批准版本变更';
      await loadTemplateApprovals();
      if (!result.chain_advanced) {
        await loadVolumeTemplates();
        await loadTemplateVersionChangelogFn();
      }
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function batchApproveTemplateVersions(): Promise<void> {
    const ids = pendingTemplateApprovals.value.map((row) => row.id);
    if (!ids.length) return;
    try {
      const force = window.confirm('批量批准全部待审批项？若存在快照漂移将自动 force。');
      if (!force) return;
      const result = await batchApproveCreatorTemplateApprovals({
        approval_ids: ids,
        force: true,
      }) as { approved: number; total: number };
      saveMessage.value = `批量批准：${result.approved}/${result.total}`;
      await loadTemplateApprovals();
      await loadVolumeTemplates();
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function batchRejectTemplateVersions(): Promise<void> {
    const ids = pendingTemplateApprovals.value.map((row) => row.id);
    if (!ids.length) return;
    try {
      const result = await batchRejectCreatorTemplateApprovals({
        approval_ids: ids,
        reason: '批量驳回',
      }) as { rejected: number; total: number };
      saveMessage.value = `批量驳回：${result.rejected}/${result.total}`;
      await loadTemplateApprovals();
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function rejectTemplateVersion(approvalId: string): Promise<void> {
    try {
      await rejectCreatorTemplateApproval(approvalId, { reason: '驳回' });
      saveMessage.value = '已驳回版本变更';
      await loadTemplateApprovals();
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function transferTemplateApproval(approvalId: string): Promise<void> {
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

  async function previewApprovalSnapshotDiff(approvalId: string): Promise<void> {
    try {
      templateApprovalSnapshotDiff.value = await fetchCreatorTemplateApprovalSnapshotDiff(approvalId);
      const summary = (templateApprovalSnapshotDiff.value as { diff_summary?: { changed?: boolean; lines_added?: number; lines_removed?: number } } | null)?.diff_summary;
      saveMessage.value = summary?.changed
        ? `快照 diff：+${summary.lines_added} / -${summary.lines_removed}`
        : '快照与当前卷纲一致';
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function loadTemplateApprovalsFn(): Promise<void> {
    try {
      const data = await fetchCreatorTemplateApprovals({ status: 'pending' }) as { approvals?: ApprovalEntry[] };
      templateApprovals.value = data.approvals || [];
      const history = await fetchCreatorTemplateApprovalHistory() as { approvals?: Array<Record<string, unknown>> };
      templateApprovalHistory.value = history.approvals || [];
      await loadTemplateApprovalChainConfig();
    } catch {
      templateApprovals.value = [];
      templateApprovalHistory.value = [];
    }
  }

  async function loadTemplateApprovalChainConfig(): Promise<void> {
    try {
      const data = await fetchCreatorTemplateApprovalChainConfig() as ApprovalChainConfig;
      templateApprovalChainSteps.value = data.required_steps || 2;
      templateApprovalStepAssignees.value = (data.step_assignees || []).join(', ');
      if (data.step_assignee_groups?.length) {
        templateApprovalOrGroups.value = data.step_assignee_groups
          .map((group) => group.join('|'))
          .join(',');
      }
      const sla = await fetchCreatorTemplateApprovalSlaConfig() as ApprovalSlaConfig;
      templateApprovalSlaHours.value = sla.timeout_hours || 72;
      templateApprovalEmailOnSubmit.value = Boolean(sla.email_on_submit);
      templateApprovalEmailOnReject.value = Boolean(sla.email_on_reject);
      templateApprovalEmailOnOverdue.value = Boolean(sla.email_on_overdue);
      const overdue = await fetchCreatorTemplateApprovalOverdue() as { approvals?: Array<Record<string, unknown>> };
      overdueTemplateApprovals.value = overdue.approvals || [];
    } catch {
      templateApprovalChainSteps.value = 2;
      templateApprovalSlaHours.value = 72;
      overdueTemplateApprovals.value = [];
    }
  }

  async function saveTemplateApprovalSlaConfig(): Promise<void> {
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

  async function saveTemplateApprovalChainConfig(): Promise<void> {
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
      }) as ApprovalChainConfig;
      templateApprovalChainSteps.value = data.required_steps || 2;
      templateApprovalStepAssignees.value = (data.step_assignees || []).join(', ');
      saveMessage.value = `已保存审批链（${templateApprovalChainSteps.value} 步）`;
    } catch (e) {
      handleSaveError(e);
    }
  }

  return {
    templateSaving,
    templateDeleting,
    templateRenaming,
    templateVersionSaving,
    templateRollbackSaving,
    templateApprovalSubmitting,
    saveCustomVolumeTemplate,
    deleteSelectedVolumeTemplate,
    renameSelectedVolumeTemplate,
    saveTemplateVersionLabel,
    loadTemplateVersionChangelog: loadTemplateVersionChangelogFn,
    rollbackTemplateVersion,
    toggleChangelogVisual,
    submitTemplateVersionApproval,
    approveTemplateVersion,
    batchApproveTemplateVersions,
    batchRejectTemplateVersions,
    rejectTemplateVersion,
    transferTemplateApproval,
    previewApprovalSnapshotDiff,
    loadTemplateApprovals: loadTemplateApprovalsFn,
    loadTemplateApprovalChainConfig,
    saveTemplateApprovalChainConfig,
    saveTemplateApprovalSlaConfig,
  };
}