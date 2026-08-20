/**
 * useCreatorSettings 子模块聚合入口 — Phase 19 Task 3
 *
 * 把 useCreatorSettings.js 711 行 monolithic 实现拆为 3 个 .ts 子模块：
 * - useSettingsHistory   (设定历史快照 + 恢复)
 * - useMergePresets      (合并预设 + 工厂库 + 冲突修复)
 * - useSettingsDocs      (设定文档编辑 + 3-way diff + 保存)
 *
 * 上游 useCreatorSettings.js facade 通过本文件聚合各子模块的
 * state/actions，最终合并为 settingsContext 返回给调用方（保持下游零修改）。
 *
 * 注意：本文件仅做 re-export，具体实现见各子模块 .ts。
 */
export { useSettingsHistory } from './useSettingsHistory';
export { useMergePresets } from './useMergePresets';
export { useSettingsDocs } from './useSettingsDocs';
