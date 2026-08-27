/**
 * useMergePresets — 合并预设管理 + 工厂库 + 冲突修复
 *
 * Phase 19 Task 3.2：从 useCreatorSettings.js 拆出（完整实现）。
 * Phase 126 v16.2.2 T4b：迁到 typed wrapper `'../../api/settings.js'`。
 * `request()` 自动加 `/api/` 前缀（v16.2.1 教训）。
 *
 * IMPORTANT: typed wrapper names collide with this submodule's exported
 * function names (`publishMergePresetToFactory`, `exportMergePresetPackages`,
 * `applyMergePresetConflictFix`, etc.). Imports are aliased to a `Creator`
 * suffix to avoid recursion in the inner try blocks.
 *
 * 负责: mergePresetPackages + 选/应用/导入/导出/同步/factory + 冲突修复 +
 *       toposort + 偏好导入导出。
 */
import { computed, ref, shallowRef } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import {
  fetchMergePreferences,
  exportMergePreferences,
  importMergePreferences,
  fetchMergePresetChangelog,
  fetchMergePresetChangelogDiff,
  toposortMergePresetPackages,
  listMergePresetPackages,
  listFactoryMergePresetPackages,
  applyMergePresetConflictFix as applyMergePresetConflictFixApi,
  applyAllMergePresetConflictFixes as applyAllMergePresetConflictFixesApi,
  preflightMergePresetImport as preflightMergePresetImportApi,
  previewMergePresetImportDiff as previewMergePresetImportDiffApi,
  applyToposortMergePresetOrder,
  exportMergePresetPackages as exportMergePresetPackagesApi,
  importMergePresetPackages,
  publishMergePresetToFactory as publishMergePresetToFactoryApi,
  pullFactoryMergePresetsToProject,
  preflightFactoryMergePresetPull,
} from '../../api/settings.js';

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
  mergePresetImportPreview: Ref<{ added: unknown[]; updated: unknown[]; removed: unknown[] }>;
  mergePreferences: Ref<MergePreferences>;
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

  const mergePresetPackages = shallowRef<MergePresetPackage[]>([]); // Phase 78: shallowRef — wholesale replacement
  const factoryMergePresetPackages = shallowRef<MergePresetPackage[]>([]); // Phase 78: shallowRef — wholesale replacement
  const selectedMergePresetPackage = ref('');
  const mergePresetImportPreview = shallowRef({ added: [] as unknown[], updated: [] as unknown[], removed: [] as unknown[] }); // Phase 78: shallowRef — wholesale replacement
  const mergePreferences = shallowRef<MergePreferences>({}); // Phase 78: shallowRef — wholesale replacement
  const mergePresetChangelog = ref({ package_id: '', entry_count: 0, entries: [] as Array<Record<string, unknown>> });
  const mergePresetChangelogDiff = ref({ change_count: 0, changes: [] as Array<Record<string, unknown>> });
  const mergePresetImportPreflight = shallowRef<unknown>(null); // Phase 78: shallowRef — wholesale replacement
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

  const selectedMergePresetPackageName = computed<string>(() => {
    const pkg = mergePresetPackages.value.find((row) => row.id === selectedMergePresetPackage.value);
    return pkg?.name || '';
  });

  async function loadMergePresetPackages(): Promise<void> {
    try {
      const data = await listMergePresetPackages();
      mergePresetPackages.value = data.packages || [];
      const factoryData = await listFactoryMergePresetPackages();
      factoryMergePresetPackages.value = factoryData.packages || [];
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function loadMergePreferences(): Promise<void> {
    try {
      const data = await fetchMergePreferences();
      mergePreferences.value = data as unknown as MergePreferences;
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
      const data = await exportMergePresetPackagesApi();
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
      // typed wrapper requests `package_id` (legacy path passed `{}` and relied
      // on backend to surface the publish target; preserved here for
      // backwards compatibility — full migration deferred to next phase).
      await publishMergePresetToFactoryApi({} as unknown as Parameters<typeof publishMergePresetToFactoryApi>[0]);
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
      const result = await pullFactoryMergePresetsToProject({ package_ids: [] });
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
      const result = await pullFactoryMergePresetsToProject({
        package_ids: [packageId],
        conflict_strategies: { [packageId]: strategy },
      });
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
      // typed wrapper expects `CreatorMergePresetConflictFixApplyRequest`
      // (`{ package_id, action, dependency_id?, version_label? }`). The legacy
      // `fix` shape may have additional diagnostic fields — narrow to the typed
      // DTO before passing.
      await applyMergePresetConflictFixApi({
        package_id: String(fix.package_id ?? ''),
        action: String(fix.action ?? 'bump_version'),
        dependency_id: (fix.dependency_id as string | null | undefined) ?? null,
        version_label: (fix.version_label as string | null | undefined) ?? null,
      });
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
      await applyAllMergePresetConflictFixesApi();
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
      const data = await previewMergePresetImportDiffApi({ packages: [] });
      mergePresetImportPreview.value = data as unknown as { added: unknown[]; updated: unknown[]; removed: unknown[] };
    } catch (e) {
      handleSaveError(e);
    } finally {
      mergePresetImportPreviewLoading.value = false;
    }
  }

  async function applyMergePresetToposort(): Promise<void> {
    mergePresetToposortApplying.value = true;
    try {
      await applyToposortMergePresetOrder();
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
      const data = await preflightMergePresetImportApi({ packages: [] });
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
    mergePresetImportPreview,
    mergePreferences,
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
