/**
 * useCreatorProductTools 子模块聚合入口 — Phase 19 Task 1
 *
 * 把 useCreatorProductTools.js 788 行 monolithic 实现拆为 4 个 .ts 子模块：
 * - useProductPreferences  (创作偏好/模型同步)
 * - useProductMemory       (记忆资产/搜索/标注)
 * - useProductExport       (导出向导 + Markdown/EPUB/DOCX)
 * - useProductPublish      (发布向导 + 历史 + 平台)
 *
 * 上游 useCreatorProductTools.js facade 通过本文件聚合各子模块的
 * state/actions，最终合并为 panelContext 返回给调用方（保持下游零修改）。
 *
 * 注意：本文件仅做 re-export，具体实现见各子模块 .ts。
 */
export { useProductPreferences } from './useProductPreferences';
export { useProductMemory } from './useProductMemory';
export { useProductExport } from './useProductExport';
export { useProductPublish } from './useProductPublish';