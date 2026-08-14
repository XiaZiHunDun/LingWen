/**
 * useProductMemory — 记忆资产、搜索、标注、介入/结构图
 *
 * Phase 19 Task 1：从 useCreatorProductTools.js 拆出。
 * 负责: memory assets 列表/过滤 + 搜索 + 标注 + structureGraph + interventionItems。
 *
 * 依赖 (deps):
 * - overview, editableVolumes, visibleDeviations, batchJob, batchRunning, logicCheckResult
 * - pillarsText, globalOutlineText
 * - error, saveMessage
 * - preferences (用于读取 memoryRagTopK)
 * - settingsHasUnsavedChanges（可选）
 * - setWorkspaceTab, jumpToChapter, navigateTo（导航动作）
 */
import { computed, ref, watch } from 'vue';
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
  batchJob: Ref<Record<string, unknown> | null>;
  batchRunning: Ref<boolean>;
  logicCheckResult: Ref<Record<string, unknown> | null>;
  pillarsText: Ref<string>;
  globalOutlineText: Ref<string>;
  error: Ref<string | null>;
  saveMessage: Ref<string>;
  preferences: Ref<{ memoryRagTopK?: number; interventionRules?: Record<string, boolean>; memoryRagEnabled?: boolean }>;
  settingsHasUnsavedChanges?: ComputedRef<boolean>;
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
  memoryRagEnabled: ComputedRef<boolean>;
  memoryAnnotationSaving: Ref<string | null>;
  memorySearchQuery: Ref<string>;
  memorySearchScope: Ref<string>;
  memorySearchResults: Ref<Array<Record<string, unknown>>>;
  memorySearchBusy: Ref<boolean>;
  memorySearchRan: Ref<boolean>;
  memorySearchUsedFallback: Ref<boolean>;
  structureGraph: ComputedRef<unknown>;
  structureGraphView: Ref<string>;
  interventionItems: ComputedRef<Array<Record<string, unknown>>>;
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
    batchJob,
    batchRunning,
    logicCheckResult,
    pillarsText,
    globalOutlineText,
    error,
    saveMessage,
    preferences,
    settingsHasUnsavedChanges,
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
  const memoryRagEnabled = computed<boolean>(() => {
    const payload = memoryAssetsPayload.value;
    return payload?.memory_rag_enabled ?? Boolean(preferences.value.memoryRagEnabled);
  });

  const structureGraph = computed(() => buildStructureGraph({
    overview: overview.value as Parameters<typeof buildStructureGraph>[0]['overview'],
    volumes: editableVolumes.value as Parameters<typeof buildStructureGraph>[0]['volumes'],
    deviations: visibleDeviations.value as Parameters<typeof buildStructureGraph>[0]['deviations'],
  }));

  function interventionRuleEnabled(ruleId: string): boolean {
    const rules = preferences.value.interventionRules;
    return rules?.[ruleId] !== false;
  }

  const interventionItems = computed(() => {
    const items: Array<Record<string, unknown>> = [];
    const deviations = visibleDeviations.value;
    const alerts = deviations.filter((d) => (d as { severity?: string }).severity === 'alert') as Array<{ message?: string; chapter?: number }>;
    if (interventionRuleEnabled('deviationAlerts') && alerts.length) {
      items.push({
        id: 'deviation-alerts',
        kind: 'deviation',
        title: `${alerts.length} 处需关注偏离`,
        detail: alerts[0].message || '点击查看脉络详情',
        action: 'pulse',
        chapter: alerts[0].chapter,
      });
    }
    if (interventionRuleEnabled('batchProgress') && (batchRunning.value || (batchJob.value as { status?: string } | null)?.status === 'running')) {
      items.push({
        id: 'batch-running',
        kind: 'batch',
        title: '批量推进进行中',
        detail: (batchJob.value as { message?: string } | null)?.message || '可在脉络栏查看进度',
        action: 'pulse',
      });
    }
    const issues = ((logicCheckResult.value as { issues?: Array<{ severity?: string; priority?: string; message?: string }> } | null)?.issues) || [];
    const p0 = issues.filter((i) => i.severity === 'P0' || i.priority === 'P0');
    if (interventionRuleEnabled('logicP0') && p0.length) {
      items.push({
        id: 'logic-p0',
        kind: 'logic',
        title: `${p0.length} 条 P0 逻辑问题`,
        detail: p0[0].message || '请在写栏处理',
        action: 'write',
        chapter: (logicCheckResult.value as { chapter?: number } | null)?.chapter,
      });
    }
    if (interventionRuleEnabled('settingsUnsaved') && settingsHasUnsavedChanges?.value) {
      items.push({
        id: 'settings-unsaved',
        kind: 'settings',
        title: '设定尚未保存',
        detail: '支柱或全局大纲有未保存的修改',
        action: 'settings',
      });
    }
    if (interventionRuleEnabled('preferencesUnsaved') && (preferences.value as unknown as { _dirty?: boolean })._dirty !== false) {
      // placeholder hook for dirty state; main hook patches via watch
    }
    if (
      interventionRuleEnabled('memoryOffline')
      && memoryAssetsLoadedOnce.value
      && !memoryAssetsLoading.value
      && memoryRagEnabled.value
      && !memoryAvailable.value
    ) {
      items.push({
        id: 'memory-offline',
        kind: 'memory',
        title: '记忆系统离线',
        detail: 'RAG 已开启但记忆网关不可用，搜索将降级为本地匹配',
        action: 'memory',
      });
    }
    if (
      interventionRuleEnabled('emptyWriteHint')
      && !items.length
      && (overview.value as { chapters_written?: number; creation_mode?: string } | null)?.chapters_written === 0
      && (overview.value as { creation_mode?: string } | null)?.creation_mode !== 'companion'
      && (overview.value as { creation_mode?: string } | null)?.creation_mode !== 'advance'
    ) {
      items.push({
        id: 'onboarding-write',
        kind: 'hint',
        title: '尚未开始写作',
        detail: '从写栏选择章节或运行入门向导',
        action: 'write',
      });
    }
    return items;
  });

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
        top_k: preferences.value.memoryRagTopK,
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
    memoryRagEnabled,
    memoryAnnotationSaving,
    memorySearchQuery,
    memorySearchScope,
    memorySearchResults,
    memorySearchBusy,
    memorySearchRan,
    memorySearchUsedFallback,
    structureGraph,
    structureGraphView,
    interventionItems,
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