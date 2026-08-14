/**
 * useCreatorVolumePlanTemplates 子模块聚合入口 — Phase 19 Task 2
 *
 * 把 useCreatorVolumePlanTemplates.js 723 行 monolithic 实现拆为 3 个 .ts 子模块：
 * - useTemplateList     (模板列表 + 选择 + hint/project/factory computeds)
 * - useTemplateEditor   (编辑/CRUD/版本/审批/链/SLA/审计)
 * - useTemplateSync     (导入/导出/同步/factory pull/publish/delete)
 *
 * 上游 useCreatorVolumePlanTemplates.js facade 通过本文件聚合各子模块的
 * state/actions，最终合并为 templatesContext 返回给调用方（保持下游零修改）。
 *
 * 注意：本文件仅做 re-export，具体实现见各子模块 .ts。
 */
export { useTemplateList } from './useTemplateList';
export { useTemplateEditor } from './useTemplateEditor';
export { useTemplateSync } from './useTemplateSync';