/**
 * useTemplateSync — 模板导入/导出/同步/factory pull/publish/delete
 *
 * Phase 19 Task 2 占位：useCreatorVolumePlanTemplates.js 723 行拆为 3 子模块之一。
 * 负责: exportCustomTemplates/importCustomTemplates 导入导出、
 *       syncTemplatesFromProjects 跨项目同步、publishSelectedTemplateToFactory 发到工厂库、
 *       pullFactoryTemplates/deleteSelectedFactoryTemplate 工厂库管理。
 *
 * 注: 本会话仅建立类型骨架（Task 8 同模式），实际提取在后续会话完成。
 */
import type { Ref } from 'vue';

export interface TemplateSyncDeps {
  // 暂未使用（待后续会话填充）
}

export interface TemplateSyncReturn {
  showImportTemplates: Ref<boolean>;
  importTemplatesJson: Ref<string>;
  templateImporting: Ref<boolean>;
  templateSyncSources: Ref<Array<{ slug: string; name?: string }>>;
  templateSyncing: Ref<boolean>;
  templatePublishing: Ref<boolean>;
  factoryPulling: Ref<boolean>;
  factoryDeleting: Ref<boolean>;
  templateApplying: Ref<boolean>;
  exportCustomTemplates: () => Promise<void>;
  importCustomTemplates: () => Promise<void>;
  loadTemplateSyncSources: () => Promise<void>;
  syncTemplatesFromProjects: () => Promise<void>;
  publishSelectedTemplateToFactory: () => Promise<void>;
  pullFactoryTemplates: () => Promise<void>;
  deleteSelectedFactoryTemplate: () => Promise<void>;
  applyVolumeTemplate: () => Promise<void>;
}

// 占位实现 — 后续会话填充实际逻辑
export function useTemplateSync(_deps: TemplateSyncDeps): TemplateSyncReturn {
  throw new Error('useTemplateSync: not yet implemented (Phase 19 Task 2.3)');
}