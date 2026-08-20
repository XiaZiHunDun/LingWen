/**
 * useProductMemory — 记忆资产、搜索、标注、导航动作
 *
 * Phase 19 Task 1.5：从 useCreatorProductTools.js 拆出，最终接入。
 * 负责: memory assets 列表/过滤 + 搜索 + 标注 + 结构图 + 介入导航 action。
 *
 * 依赖 (deps):
 * - overview, editableVolumes, visibleDeviations, batchJob, batchRunning, logicCheckResult
 * - pillarsText, globalOutlineText
 * - error, saveMessage
 * - memoryRagTopK (Ref<number>): 来自 preferences 的 top_k 搜索参数
 * - memoryRagEnabled (ComputedRef<boolean>): 主 hook 组合（payload ?? preferences）
 * - settingsHasUnsavedChanges（可选）
 * - setWorkspaceTab, jumpToChapter, navigateTo（导航动作）
 *
 * 注: 不计算 memoryRagEnabled 和 interventionItems（循环依赖）—— 这两个
 * computed 在主 hook 中组合计算。
 */
import { computed, ref } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import {
  fetchCreatorMemoryAssets,
  saveCreatorMemoryAnnotation,
  queryCreatorMemory,
} from '../../api/index.js';
import { buildMemoryAssetItems } from '../../utils/creatorMemoryAssetsUtils.js';
import { buildStructureGraph } from '../../utils/creatorStructureGraphUtils.js';

interface MemoryAssetItem {
  id?: string;
  kind?: string;
  pinned?: boolean;
  placeholder?: boolean;
  chapter?: number;
}

interface MemoryAssetsPayload {
  items?: MemoryAssetItem[];
  memory_available?: boolean;
  memory_rag_enabled?: boolean;
}

export interface MemoryDeps {
  overview: Ref<Record<string, unknown> | null>;
  editableVolumes: Ref<Array<Record<string, unknown>>>;
  visibleDeviations: ComputedRef<Array<Record<string, unknown>>>;
  pillarsText: Ref<string>;
  globalOutlineText: Ref<string>;
  error: Ref<string | null>;
  saveMessage: Ref<string>;
  memoryRagTopK: Ref<number | undefined>;
  setWorkspaceTab: (tab: string) => void;
  jumpToChapter: (chapter: number) => Promise<void>;
  navigateTo: (page: string, opts?: Record<string, unknown>) => void;
}

export interface ProductMemoryReturn {
  memoryAssetsPayload: Ref<MemoryAssetsPayload | null>;
  memoryAssetsLoading: Ref<boolean>;
  memoryAssetsLoadedOnce: Ref<boolean>;
  memoryFilter: Ref<string>;
  memoryFocusAssetId: Ref<string | null>;
  memoryAssets: ComputedRef<MemoryAssetItem[]>;
  memoryAssetsFiltered: ComputedRef<MemoryAssetItem[]>;
  memoryAvailable: ComputedRef<boolean>;
  memoryAnnotationSaving: Ref<string | null>;
  memorySearchQuery: Ref<string>;
  memorySearchScope: Ref<string>;
  memorySearchResults: Ref<Array<Record<string, unknown>>>;
  memorySearchBusy: Ref<boolean>;
  memorySearchRan: Ref<boolean>;
  memorySearchUsedFallback: Ref<boolean>;
  structureGraph: ComputedRef<unknown>;
  structureGraphView: Ref<string>;
  loadMemoryAssets: () => Promise<void>;
  runMemorySearch: () => Promise<void>;
  saveMemoryAnnotation: (assetId: string, patch: Record<string, unknown>) => Promise<void>;
  toggleMemoryPin: (item: MemoryAssetItem) => Promise<void>;
  saveMemoryNote: (item: MemoryAssetItem, note: string) => Promise<void>;
  handleInterventionAction: (item: { action?: string; chapter?: number } | null) => Promise<void>;
  goToSettingsForAsset: (item: { editable?: boolean } | null) => void;
  focusMemoryEntity: (entity: { id?: string; kind?: string; name?: string } | null) => void;
}

export function useProductMemory(deps: MemoryDeps): ProductMemoryReturn {
  const {
    overview,
    editableVolumes,
    visibleDeviations,
    pillarsText,
    globalOutlineText,
    error,
    saveMessage,
    memoryRagTopK,
    setWorkspaceTab,
    jumpToChapter,
    navigateTo,
  } = deps;

  const memoryAssetsPayload = ref<MemoryAssetsPayload | null>(null);
  const memoryAssetsLoading = ref(false);
  const memoryAssetsLoadedOnce = ref(false);
  const memoryFilter = ref('all');
  const memoryFocusAssetId = ref<string | null>(null);

  const memorySearchQuery = ref('');
  const memorySearchScope = ref('all');
  const memorySearchResults = ref<Array<Record<string, unknown>>>([]);
  const memorySearchBusy = ref(false);
  const memorySearchRan = ref(false);
  const memorySearchUsedFallback = ref(false);

  const memoryAnnotationSaving = ref<string | null>(null);

  const structureGraphView = ref('tree');

  const memoryAssets = computed<MemoryAssetItem[]>(() => {
    const payload = memoryAssetsPayload.value;
    if (payload?.items?.length) {
      return payload.items;
    }
    return buildMemoryAssetItems({
      overview: overview.value as Parameters<typeof buildMemoryAssetItems>[0]['overview'],
      pillarsText: pillarsText.value,
      outlineText: globalOutlineText.value,
    }) as MemoryAssetItem[];
  });

  const memoryAssetsFiltered = computed<MemoryAssetItem[]>(() => {
    const filter = memoryFilter.value;
    if (filter === 'all') return memoryAssets.value;
    return memoryAssets.value.filter((item) => item.kind === filter);
  });

  const memoryAvailable = computed<boolean>(() =>
    Boolean(memoryAssetsPayload.value?.memory_available),
  );

  const structureGraph = computed(() => buildStructureGraph({
    overview: overview.value as Parameters<typeof buildStructureGraph>[0]['overview'],
    volumes: editableVolumes.value as Parameters<typeof buildStructureGraph>[0]['volumes'],
    deviations: visibleDeviations.value as Parameters<typeof buildStructureGraph>[0]['deviations'],
  }));

  async function loadMemoryAssets(): Promise<void> {
    memoryAssetsLoading.value = true;
    try {
      memoryAssetsPayload.value = await fetchCreatorMemoryAssets() as MemoryAssetsPayload;
    } catch {
      memoryAssetsPayload.value = null;
    } finally {
      memoryAssetsLoading.value = false;
      memoryAssetsLoadedOnce.value = true;
    }
  }

  async function runMemorySearch(): Promise<void> {
    const q = memorySearchQuery.value.trim();
    if (!q) return;
    memorySearchBusy.value = true;
    memorySearchRan.value = false;
    try {
      const data = await queryCreatorMemory({
        query: q,
        scope: memorySearchScope.value,
        top_k: memoryRagTopK.value,
      });
      memorySearchResults.value = (data as { results?: Array<Record<string, unknown>> }).results || [];
      memorySearchUsedFallback.value = Boolean((data as { used_fallback?: boolean }).used_fallback);
      memorySearchRan.value = true;
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
      memorySearchResults.value = [];
      memorySearchRan.value = true;
    } finally {
      memorySearchBusy.value = false;
    }
  }

  async function saveMemoryAnnotation(assetId: string, patch: Record<string, unknown>): Promise<void> {
    memoryAnnotationSaving.value = assetId;
    try {
      await saveCreatorMemoryAnnotation(assetId, patch);
      await loadMemoryAssets();
      saveMessage.value = '记忆备注已保存';
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      memoryAnnotationSaving.value = null;
    }
  }

  async function toggleMemoryPin(item: MemoryAssetItem): Promise<void> {
    if (!item?.id || item.placeholder) return;
    await saveMemoryAnnotation(item.id, { pinned: !item.pinned });
  }

  async function saveMemoryNote(item: MemoryAssetItem, note: string): Promise<void> {
    if (!item?.id || item.placeholder) return;
    await saveMemoryAnnotation(item.id, { note });
  }

  async function handleInterventionAction(item: { action?: string; chapter?: number } | null): Promise<void> {
    if (!item) return;
    if (item.action === 'pulse') {
      setWorkspaceTab('pulse');
      if (item.chapter) await jumpToChapter(item.chapter);
      return;
    }
    if (item.action === 'write') {
      setWorkspaceTab('write');
      if (item.chapter) await jumpToChapter(item.chapter);
      return;
    }
    if (item.action === 'memory') {
      setWorkspaceTab('memory');
      return;
    }
    if (item.action === 'settings') {
      setWorkspaceTab('settings');
      return;
    }
    if (item.action === 'decisions') {
      navigateTo('decisions', { clearFocus: true });
    }
  }

  function goToSettingsForAsset(item: { editable?: boolean } | null): void {
    if (item?.editable) {
      setWorkspaceTab('settings');
    }
  }

  function focusMemoryEntity(entity: { id?: string; kind?: string; name?: string } | null): void {
    if (!entity) {
      memoryFocusAssetId.value = null;
      setWorkspaceTab('memory');
      return;
    }
    memoryFocusAssetId.value = entity.id || null;
    const kind = entity.kind;
    memoryFilter.value = kind === 'foreshadow' ? 'foreshadow' : kind === 'character' ? 'character' : 'all';
    memorySearchQuery.value = (entity.name || '').replace(/^伏笔：/, '').trim();
    setWorkspaceTab('memory');
  }

  return {
    memoryAssetsPayload,
    memoryAssetsLoading,
    memoryAssetsLoadedOnce,
    memoryFilter,
    memoryFocusAssetId,
    memoryAssets,
    memoryAssetsFiltered,
    memoryAvailable,
    memoryAnnotationSaving,
    memorySearchQuery,
    memorySearchScope,
    memorySearchResults,
    memorySearchBusy,
    memorySearchRan,
    memorySearchUsedFallback,
    structureGraph,
    structureGraphView,
    loadMemoryAssets,
    runMemorySearch,
    saveMemoryAnnotation,
    toggleMemoryPin,
    saveMemoryNote,
    handleInterventionAction,
    goToSettingsForAsset,
    focusMemoryEntity,
  };
}
