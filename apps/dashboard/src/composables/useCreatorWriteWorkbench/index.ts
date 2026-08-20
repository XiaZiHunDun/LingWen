/**
 * useCreatorWriteWorkbench 子模块聚合入口 — Phase 60
 *
 * 把 529L monolithic 实现拆为 4 个 .ts 子模块：
 * - useWorkbenchLayout      （面板/可见性/目标卡/一致性/creationMode）
 * - useWorkbenchSelection   （选区/锁/控制参数）
 * - useWorkbenchCheckpoints （检查点 + diff 视图）
 * - useWorkbenchQuality     （意图/校验/质量/冲突/生成控制）
 *
 * 上游 useCreatorWriteWorkbench.js facade 通过本文件聚合各子模块的
 * state/actions，最终合并为 workbenchContext 返回给调用方（保持下游零修改）。
 */
export { useWorkbenchLayout } from './useWorkbenchLayout';
export { useWorkbenchSelection } from './useWorkbenchSelection';
export { useWorkbenchCheckpoints } from './useWorkbenchCheckpoints';
export { useWorkbenchQuality } from './useWorkbenchQuality';
