/**
 * useMergePresets — 合并预设管理 + 工厂库 + 冲突修复
 *
 * Phase 19 Task 3 占位：useCreatorSettings.js 711 行拆为 3 子模块之一。
 * 负责: mergePresetPackages + 选/应用/导入/导出/同步/factory + 冲突修复 +
 *       toposort + 偏好导入导出。
 *
 * 注: 本会话仅建立类型骨架（Task 8 同模式），实际提取在后续会话完成。
 */
import type { ComputedRef, Ref } from 'vue';

export interface MergePresetPackage {
  id: string;
  name?: string;
  scope?: 'project' | 'factory';
}

export interface MergePresetsDeps {
  // 暂未使用（待后续会话填充）
}

export interface MergePresetsReturn {
  mergePresetPackages: Ref<MergePresetPackage[]>;
  factoryMergePresetPackages: Ref<MergePresetPackage[]>;
  selectedMergePresetPackage: Ref<string>;
  selectedMergePresetPackageName: ComputedRef<string>;
  mergePresetConflicts: Ref<Array<Record<string, unknown>>>;
  mergePresetImportPreview: Ref<Array<Record<string, unknown>> | null>;
  mergePreferences: Ref<Record<string, unknown>>;
  loadMergePresetPackages: () => Promise<void>;
  loadMergePreferences: () => Promise<void>;
  applyMergePreset: (source: string) => Promise<void>;
  applyMergePresetPackage: (packageId: string) => Promise<void>;
  exportMergePresetPackages: () => Promise<void>;
  importMergePresetPackagesFromJson: () => Promise<void>;
  publishMergePresetToFactory: () => Promise<void>;
  pullFactoryMergePresets: () => Promise<void>;
  applyMergePresetConflictFix: (fix: Record<string, unknown>) => Promise<void>;
  applyAllMergePresetConflictFixes: () => Promise<void>;
}

// 占位实现 — 后续会话填充实际逻辑
export function useMergePresets(_deps: MergePresetsDeps): MergePresetsReturn {
  throw new Error('useMergePresets: not yet implemented (Phase 19 Task 3.2)');
}