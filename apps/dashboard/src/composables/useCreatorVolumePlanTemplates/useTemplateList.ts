/**
 * useTemplateList — 模板列表 + 选择 + 视图 computeds
 *
 * Phase 19 Task 2 占位：useCreatorVolumePlanTemplates.js 723 行拆为 3 子模块之一。
 * 负责: 列表加载、当前选中、selectedTemplateHint/Project/Factory/Custom/factoryTemplateCount
 *       computeds + formatTemplateOption/formatHistoryTime/isSemverVersionLabel helpers。
 *
 * 注: 本会话仅建立类型骨架（Task 8 同模式），实际提取在后续会话完成。
 */
import type { Ref, ComputedRef } from 'vue';

export interface TemplateRow {
  id: string;
  name: string;
  scope?: 'project' | 'factory';
  description?: string;
  version_label?: string;
  version_semver_valid?: boolean;
  version_changelog?: Array<Record<string, unknown>>;
}

export interface TemplateListDeps {
  // 暂未使用（待后续会话填充）
}

export interface TemplateListReturn {
  volumeTemplates: Ref<TemplateRow[]>;
  selectedTemplateId: Ref<string>;
  selectedTemplateHint: ComputedRef<string>;
  selectedTemplateProject: ComputedRef<boolean>;
  selectedTemplateFactory: ComputedRef<boolean>;
  selectedTemplateCustom: ComputedRef<boolean>;
  factoryTemplateCount: ComputedRef<number>;
  formatTemplateOption: (template: TemplateRow) => string;
  isSemverVersionLabel: (label: string) => boolean;
  formatHistoryTime: (iso: string) => string;
  loadVolumeTemplates: () => Promise<void>;
}

// 占位实现 — 后续会话填充实际逻辑
export function useTemplateList(_deps: TemplateListDeps): TemplateListReturn {
  throw new Error('useTemplateList: not yet implemented (Phase 19 Task 2.1)');
}