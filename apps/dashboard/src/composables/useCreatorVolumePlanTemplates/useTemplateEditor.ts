/**
 * useTemplateEditor — 模板编辑 + 版本 + 审批
 *
 * Phase 19 Task 2 占位：useCreatorVolumePlanTemplates.js 723 行拆为 3 子模块之一。
 * 负责: CRUD（save/delete/rename）、版本标签/changelog/回滚、审批链配置、
 *       审批历史/SLA、批量批准/驳回/转交/快照 diff。
 *
 * 注: 本会话仅建立类型骨架（Task 8 同模式），实际提取在后续会话完成。
 */
import type { Ref } from 'vue';

export interface TemplateEditorDeps {
  // 暂未使用（待后续会话填充）
}

export interface TemplateEditorReturn {
  customTemplateName: Ref<string>;
  templateSaving: Ref<boolean>;
  templateDeleting: Ref<boolean>;
  templateRenaming: Ref<boolean>;
  renameTemplateName: Ref<string>;
  templateVersionLabel: Ref<string>;
  templateVersionSaving: Ref<boolean>;
  templateVersionChangelog: Ref<Array<Record<string, unknown>>>;
  expandedChangelogVisual: Ref<number | null>;
  templateRollbackSaving: Ref<boolean>;
  templateApprovalSubmitting: Ref<boolean>;
  saveCustomVolumeTemplate: () => Promise<void>;
  deleteSelectedVolumeTemplate: () => Promise<void>;
  renameSelectedVolumeTemplate: () => Promise<void>;
  saveTemplateVersionLabel: () => Promise<void>;
  loadTemplateVersionChangelog: () => Promise<void>;
  rollbackTemplateVersion: (entry: Record<string, unknown>, index: number) => Promise<void>;
  toggleChangelogVisual: (index: number) => void;
}

// 占位实现 — 后续会话填充实际逻辑
export function useTemplateEditor(_deps: TemplateEditorDeps): TemplateEditorReturn {
  throw new Error('useTemplateEditor: not yet implemented (Phase 19 Task 2.2)');
}