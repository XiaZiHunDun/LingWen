/**
 * useCreatorVolumePlanDiff 子模块聚合入口 — Phase 20
 *
 * 把 useCreatorVolumePlanDiff.js 474 行 monolithic 实现拆为 2 个 .ts 子模块：
 * - useVolumePlanDiff     (卷纲 diff 预览/导出/打印/邮件 + collab notes)
 * - useVolumePlanDiffShare (分享链接解析/应用/合并冲突)
 *
 * 上游 useCreatorVolumePlanDiff.js facade 通过本文件聚合各子模块的
 * state/actions，最终合并为返回对象（保持下游零修改）。
 *
 * 注意：本文件仅做 re-export，具体实现见各子模块 .ts。
 */
export { useVolumePlanDiff } from './useVolumePlanDiff';
export { useVolumePlanDiffShare } from './useVolumePlanDiffShare';