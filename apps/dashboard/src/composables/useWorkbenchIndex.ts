/**
 * useWorkbenchIndex — Phase 18/19 聚合入口
 *
 * 4 个 useWorkbench*.ts 子模块的单一 re-export 点：
 * - useWorkbenchSelection  (写作选区管理)
 * - useWorkbenchCheckpoint (检查点与 diff)
 * - useWorkbenchValidation (轻量校验)
 * - useWorkbenchAgent      (Agent 控制与生成)
 *
 * 上游 useCreatorWriteWorkbench.js facade 通过本文件聚合。
 */
export { useWorkbenchSelection } from "./useWorkbenchSelection";
export { useWorkbenchCheckpoint } from "./useWorkbenchCheckpoint";
export { useWorkbenchValidation } from "./useWorkbenchValidation";
export { useWorkbenchAgent } from "./useWorkbenchAgent";