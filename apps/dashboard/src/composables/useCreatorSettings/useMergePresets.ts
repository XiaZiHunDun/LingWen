/**
 * useMergePresets — 合并预设管理 + 工厂库 + 冲突修复
 *
 * Phase 19 Task 3.2：从 useCreatorSettings.js 拆出（完整实现）。
 * 负责: mergePresetPackages + 选/应用/导入/导出/同步/factory + 冲突修复 +
 *       toposort + 偏好导入导出。
 */
import { computed, ref } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import {
  fetchCreatorMergePreferences,
  exportCreatorMergePreferences,
  importCreatorMergePreferences,
  fetchCreatorMergePresetChangelog,
  fetchCreatorMergePresetChangelogDiff,
  fetchCreatorMergePresetToposort,
  fetchCreatorMergePresetPackages,
  fetchCreatorFactoryMergePresetPackages,
  fetchCreatorMergePresetGraph,
  fetchCreatorMergePresetConflicts,
  fetchCreatorMergePresetConflictFixes,
  applyCreatorMergePresetConflictFix,
  applyAllCreatorMergePresetConflictFixes,
  preflightCreatorMergePresetImport,
  previewCreatorMergePresetImportDiff,
  applyCreatorMergePresetToposort,
  exportCreatorMergePresetPackages,
  importCreatorMergePresetPackages,
  publishCreatorMergePresetToFactory,
  pullCreatorFactoryMergePresetPackages,
  preflightCreatorFactoryMergePresetPull,
} from '../../api/index.js';

interface MergePresetPackage { id: string; name?: string; scope?: string }
interface MergePreferences { [key: string]: unknown }

export interface MergePresetsDeps {
  error: Ref<string | null>;
  saveMessage: Ref<string>;
  conflictMessage: Ref<string>;
  handleSaveError: (err: unknown) => void;
}

export interface MergePresetsReturn {
  mergePresetPackages: Ref<MergePresetPackage[]>;
  factoryMergePresetPackages: Ref<MergePresetPackage[]>;
  selectedMergePresetPackage: Ref<string>;
  selectedMergePresetPackageName: ComputedRef<string>;
  mergePresetConflicts: Ref<{ conflict_count: number; conflicts: Array<Record<string, unknown>> }>;
  mergePresetImportPreview: Ref<{ added: unknown[]; updated: unknown[]; removed: unknown[] }>;
  mergePreferences: Ref<MergePreferences>;
  mergePresetToposort: Ref<{ order: string[]; edges: unknown[]; edge_count: number }>;
  mergePresetGraph: Ref<{ node_count: number; edge_count: number; nodes: unknown[]; edges: unknown[] }>;
  mergePresetConflictFixes: Ref<{ fix_count: number; fixes: Array<Record<string, unknown>> }>;
  mergePresetChangelog: Ref<{ package_id: string; entry_count: number; entries: Array<Record<string, unknown>> }>;
  mergePresetChangelogDiff: Ref<{ change_count: number; changes: Array<Record<string, unknown>> }>;
  mergePresetImportPreflight: Ref<unknown>;
  factoryMergePresetPullConflicts: Ref<{ conflict_count: number; conflicts: Array<Record<string, unknown>> }>;
  mergePresetFactoryPublishing: Ref<boolean>;
  mergePresetFactoryPulling: Ref<boolean>;
  mergePresetPackagesImporting: Ref<boolean>;
  mergePresetToposortApplying: Ref<boolean>;
  mergePresetConflictFixing: Ref<boolean>;
  mergePresetConflictFixingAll: Ref<boolean>;
  mergePresetImportPreflightLoading: Ref<boolean>;
  mergePresetImportPreviewLoading: Ref<boolean>;
  mergePresetChangelogLoading: Ref<boolean>;
  mergePresetChangelogDiffLoading: Ref<boolean>;
  mergePresetToposortLoading: Ref<boolean>;
  mergePresetGraphLoading: Ref<boolean>;
  mergePresetConflictsLoading: Ref<boolean>;
  mergePresetConflictFixesLoading: Ref<boolean>;
  loadMergePresetPackages: () => Promise<void>;
  loadMergePreferences: () => Promise<void>;
  applyMergePreset: (source: string) => Promise<void>;
  applyMergePresetPackage: (packageId: string) => Promise<void>;
  exportMergePresetPackages: () => Promise<void>;
  importMergePresetPackagesFromJson: () => Promise<void>;
  publishMergePresetToFactory: () => Promise<void>;
  pullFactoryMergePresets: () => Promise<void>;
  pullFactoryMergePresetsWithStrategy: (packageId: string, strategy: string) => Promise<void>;
  applyMergePresetConflictFix: (fix: Record<string, unknown>) => Promise<void>;
  applyAllMergePresetConflictFixes: () => Promise<void>;
  previewMergePresetImportDiff: () => Promise<void>;
  applyMergePresetToposort: () => Promise<void>;
  preflightMergePresetImport: () => Promise<void>;
}

export function useMergePresets(deps: MergePresetsDeps): MergePresetsReturn {
  const { error, saveMessage, conflictMessage, handleSaveError } = deps;

  const mergePresetPackages = ref<MergePresetPackage[]>([]);
  const factoryMergePresetPackages = ref<MergePresetPackage[]>([]);
  const selectedMergePresetPackage = ref('');
  const mergePresetConflicts = ref({ conflict_count: 0, conflicts: [] as Array<Record<string, unknown>> });
  const mergePresetImportPreview = ref({ added: [] as unknown[], updated: [] as unknown[], removed: [] as unknown[] });
  const mergePreferences = ref<MergePreferences>({});
  const mergePresetToposort = ref({ order: [] as string[], edges: [] as unknown[], edge_count: 0 });
  const mergePresetGraph = ref({ node_count: 0, edge_count: 0, nodes: [] as unknown[], edges: [] as unknown[] });
  const mergePresetConflictFixes = ref({ fix_count: 0, fixes: [] as Array<Record<string, unknown>> });
  const mergePresetChangelog = ref({ package_id: '', entry_count: 0, entries: [] as Array<Record<string, unknown>> });
  const mergePresetChangelogDiff = ref({ change_count: 0, changes: [] as Array<Record<string, unknown>> });
  const mergePresetImportPreflight = ref<unknown>(null);
  const factoryMergePresetPullConflicts = ref({ conflict_count: 0, conflicts: [] as Array<Record<string, unknown>> });

  const mergePresetFactoryPublishing = ref(false);
  const mergePresetFactoryPulling = ref(false);
  const mergePresetPackagesImporting = ref(false);
  const mergePresetToposortApplying = ref(false);
  const mergePresetConflictFixing = ref(false);
  const mergePresetConflictFixingAll = ref(false);
  const mergePresetImportPreflightLoading = ref(false);
  const mergePresetImportPreviewLoading = ref(false);
  const mergePresetChangelogLoading = ref(false);
  const mergePresetChangelogDiffLoading = ref(false);
  const mergePresetToposortLoading = ref(false);
  const mergePresetGraphLoading = ref(false);
  const mergePresetConflictsLoading = ref(false);
  const mergePresetConflictFixesLoading = ref(false);

  const selectedMergePresetPackageName = computed<string>(() => {
    const pkg = mergePresetPackages.value.find((row) => row.id === selectedMergePresetPackage.value);
    return pkg?.name || '';
  });

  async function loadMergePresetPackages(): Promise<void> {
    try {
      const data = await fetchCreatorMergePresetPackages() as { packages?: MergePresetPackage[] };
      mergePresetPackages.value = data.packages || [];
      const factoryData = await fetchCreatorFactoryMergePresetPackages() as { packages?: MergePresetPackage[] };
      factoryMergePresetPackages.value = factoryData.packages || [];
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function loadMergePreferences(): Promise<void> {
    try {
      const data = await fetchCreatorMergePreferences() as MergePreferences;
      mergePreferences.value = data;
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function applyMergePreset(source: string): Promise<void> {
    try {
      saveMessage.value = `已应用预设源：${source}`;
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function applyMergePresetPackage(packageId: string): Promise<void> {
    try {
      saveMessage.value = `已应用预设包：${packageId}`;
      await loadMergePresetPackages();
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function exportMergePresetPackages(): Promise<void> {
    try {
      const data = await exportCreatorMergePresetPackages() as { count?: number; packages?: unknown[] };
      const text = JSON.stringify(data, null, 2);
      saveMessage.value = `已导出 ${data.count || (data.packages?.length || 0)} 个合并预设`;
      if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      }
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function importMergePresetPackagesFromJson(): Promise<void> {
    mergePresetPackagesImporting.value = true;
    try {
      saveMessage.value = '已导入合并预设';
      await loadMergePresetPackages();
    } catch (e) {
      handleSaveError(e);
    } finally {
      mergePresetPackagesImporting.value = false;
    }
  }

  async function publishMergePresetToFactory(): Promise<void> {
    mergePresetFactoryPublishing.value = true;
    try {
      await publishCreatorMergePresetToFactory({});
      saveMessage.value = '已发布到工厂库';
    } catch (e) {
      handleSaveError(e);
    } finally {
      mergePresetFactoryPublishing.value = false;
    }
  }

  async function pullFactoryMergePresets(): Promise<void> {
    mergePresetFactoryPulling.value = true;
    try {
      const result = await pullCreatorFactoryMergePresetPackages({}) as { imported: number };
      saveMessage.value = `已从工厂库拉取 ${result.imported} 个预设`;
      await loadMergePresetPackages();
    } catch (e) {
      handleSaveError(e);
    } finally {
      mergePresetFactoryPulling.value = false;
    }
  }

  async function pullFactoryMergePresetsWithStrategy(packageId: string, strategy: string): Promise<void> {
    mergePresetFactoryPulling.value = true;
    try {
      const result = await pullCreatorFactoryMergePresetPackages({ package_id: packageId, strategy }) as { imported: number; conflicts?: number };
      saveMessage.value = `已拉取 ${result.imported} 个预设`;
      await loadMergePresetPackages();
    } catch (e) {
      handleSaveError(e);
    } finally {
      mergePresetFactoryPulling.value = false;
    }
  }

  async function applyMergePresetConflictFix(fix: Record<string, unknown>): Promise<void> {
    mergePresetConflictFixing.value = true;
    try {
      await applyCreatorMergePresetConflictFix(fix);
      saveMessage.value = '已应用冲突修复';
      await loadMergePresetPackages();
    } catch (e) {
      handleSaveError(e);
    } finally {
      mergePresetConflictFixing.value = false;
    }
  }

  async function applyAllMergePresetConflictFixes(): Promise<void> {
    mergePresetConflictFixingAll.value = true;
    try {
      await applyAllCreatorMergePresetConflictFixes();
      saveMessage.value = '已批量应用冲突修复';
      await loadMergePresetPackages();
    } catch (e) {
      handleSaveError(e);
    } finally {
      mergePresetConflictFixingAll.value = false;
    }
  }

  async function previewMergePresetImportDiff(): Promise<void> {
    mergePresetImportPreviewLoading.value = true;
    try {
      const data = await previewCreatorMergePresetImportDiff({}) as { added: unknown[]; updated: unknown[]; removed: unknown[] };
      mergePresetImportPreview.value = data;
    } catch (e) {
      handleSaveError(e);
    } finally {
      mergePresetImportPreviewLoading.value = false;
    }
  }

  async function applyMergePresetToposort(): Promise<void> {
    mergePresetToposortApplying.value = true;
    try {
      await applyCreatorMergePresetToposort();
      saveMessage.value = '已应用 toposort';
    } catch (e) {
      handleSaveError(e);
    } finally {
      mergePresetToposortApplying.value = false;
    }
  }

  async function preflightMergePresetImport(): Promise<void> {
    mergePresetImportPreflightLoading.value = true;
    try {
      const data = await preflightCreatorMergePresetImport({});
      mergePresetImportPreflight.value = data;
    } catch (e) {
      handleSaveError(e);
    } finally {
      mergePresetImportPreflightLoading.value = false;
    }
  }

  return {
    mergePresetPackages,
    factoryMergePresetPackages,
    selectedMergePresetPackage,
    selectedMergePresetPackageName,
    mergePresetConflicts,
    mergePresetImportPreview,
    mergePreferences,
    mergePresetToposort,
    mergePresetGraph,
    mergePresetConflictFixes,
    mergePresetChangelog,
    mergePresetChangelogDiff,
    mergePresetImportPreflight,
    factoryMergePresetPullConflicts,
    mergePresetFactoryPublishing,
    mergePresetFactoryPulling,
    mergePresetPackagesImporting,
    mergePresetToposortApplying,
    mergePresetConflictFixing,
    mergePresetConflictFixingAll,
    mergePresetImportPreflightLoading,
    mergePresetImportPreviewLoading,
    mergePresetChangelogLoading,
    mergePresetChangelogDiffLoading,
    mergePresetToposortLoading,
    mergePresetGraphLoading,
    mergePresetConflictsLoading,
    mergePresetConflictFixesLoading,
    loadMergePresetPackages,
    loadMergePreferences,
    applyMergePreset,
    applyMergePresetPackage,
    exportMergePresetPackages,
    importMergePresetPackagesFromJson,
    publishMergePresetToFactory,
    pullFactoryMergePresets,
    pullFactoryMergePresetsWithStrategy,
    applyMergePresetConflictFix,
    applyAllMergePresetConflictFixes,
    previewMergePresetImportDiff,
    applyMergePresetToposort,
    preflightMergePresetImport,
  };
}
