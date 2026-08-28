/**
 * useWorkbenchLayout — 工作台可见性 / 面板状态 / creation mode（Phase 60.4）
 *
 * 从 useCreatorWriteWorkbench.js 拆出：
 * - workbenchEnabled / humanFirstDesk
 * - goalCardLines / consistencyItems / consistencyPanelOpen
 * - isPanelVisible / isPanelCollapsed / isLeftRailPanelVisible
 * - chapterEntities
 * - creationMode + updateCreationMode
 *
 * 通过 useEffectiveCreationMode 包装 creationMode 派生（保持原 hook 行为）。
 */
import { computed, ref } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import {
  isWriteWorkbenchLayoutEnabled,
  isWriteWorkbenchPanelVisible,
  isHumanFirstDeskMode,
  isPanelDefaultCollapsed,
  CREATOR_WRITE_WORKBENCH_MATRIX,
} from '../../config/creatorPanelMatrix.js';
import { resolveChapterEntities } from '../../utils/creatorChapterEntityUtils.js';
import { useEffectiveCreationMode } from '../useEffectiveCreationMode.js';
import { updateCreatorCreationMode } from '@/api/content';

type CreationMode = 'companion' | 'advance' | 'studio';
const VALID_CREATION_MODES: ReadonlyArray<CreationMode> = ['companion', 'advance', 'studio'];

interface Deviation {
  chapter?: number;
  severity?: string;
  message?: string;
}

interface LogicIssue {
  title?: string;
  message?: string;
  severity?: string;
  chapter?: number;
}

interface OverviewLike {
  slug?: string;
  name?: string;
  creation_mode?: CreationMode | string;
  deviations?: Deviation[];
}

interface MemoryAsset {
  id: string;
  name: string;
  [k: string]: unknown;
}

interface ConsistencyItem {
  id: string;
  level: 'warn' | 'info' | 'ok';
  text: string;
  kind: 'deviation' | 'logic' | 'memory';
}

interface GoalCardLines {
  line1: string;
  line2: string;
  line3: string;
}

export interface WorkbenchLayoutDeps {
  uiProfile: ComputedRef<Record<string, unknown>>;
  overview: Ref<OverviewLike | null>;
  selectedChapter: Ref<number | null>;
  chapterBodyDraft: Ref<string>;
  memoryAssets?: Ref<MemoryAsset[]>;
  getMemoryAssets?: () => MemoryAsset[];
  logicCheckResult?: Ref<{ issues?: LogicIssue[] } | null>;
  visibleDeviations?: ComputedRef<Deviation[]>;
}

export interface WorkbenchLayoutReturn {
  workbenchEnabled: ComputedRef<boolean>;
  humanFirstDesk: ComputedRef<boolean>;
  goalCardLines: ComputedRef<GoalCardLines>;
  consistencyItems: ComputedRef<ConsistencyItem[]>;
  consistencyPanelOpen: ComputedRef<boolean>;
  chapterEntities: ComputedRef<ReturnType<typeof resolveChapterEntities>>;
  leftPanelCollapsed: Ref<boolean>;
  isPanelVisible: (panelId: string) => boolean;
  isPanelCollapsed: (panelId: string) => boolean;
  isLeftRailPanelVisible: (panelId: string) => boolean;
  creationMode: ComputedRef<CreationMode | string>;
  updateCreationMode: (mode: CreationMode) => Promise<unknown>;
}

const MAX_CONSISTENCY_ITEMS = 3;
const PANEL_INLINE_CONFLICT_GUTTER = 'inlineConflictGutter';
const PANEL_CHAPTER_ENTITY_RAIL = 'chapterEntityRail';
const PANEL_CONSISTENCY_RAIL = 'consistencyRail';
const COMPANION_LINE2 = '陪写本章，你来定稿';
const COMPANION_LINE3 = '选一条路径 → 预览 → 确认落字';
const ADVANCE_LINE2 = '按卷纲推进，一章一章写';
const ADVANCE_LINE3 = '你定方向，系统辅助产章与校对';
const STUDIO_LINE2 = '工厂模式';
const STUDIO_LINE3 = '产线调度';
const FALLBACK_PROJECT_NAME = '当前项目';
const SEVERITY_ALERT = 'alert';
const SEVERITY_P0 = 'P0';

export function useWorkbenchLayout(deps: WorkbenchLayoutDeps): WorkbenchLayoutReturn {
  const {
    uiProfile,
    overview,
    selectedChapter,
    chapterBodyDraft,
    memoryAssets,
    getMemoryAssets,
    logicCheckResult,
    visibleDeviations,
  } = deps;

  const leftPanelCollapsed = ref(true);

  const creationMode = useEffectiveCreationMode(
    computed(() => (overview.value?.creation_mode as CreationMode) ?? 'companion'),
    computed(() =>
      overview.value
        ? { slug: overview.value.slug ?? '', name: overview.value.name ?? '' }
        : null,
    ),
  );

  const workbenchEnabled = computed(() =>
    isWriteWorkbenchLayoutEnabled(creationMode.value, uiProfile.value),
  );

  const humanFirstDesk = computed(() => isHumanFirstDeskMode(creationMode.value));

  function isPanelVisible(panelId: string): boolean {
    if (panelId === PANEL_INLINE_CONFLICT_GUTTER && uiProfile.value.write_inline_conflict_gutter === false) {
      return false;
    }
    if (panelId === PANEL_CHAPTER_ENTITY_RAIL && uiProfile.value.write_chapter_entity_rail === false) {
      return false;
    }
    return isWriteWorkbenchPanelVisible(creationMode.value, panelId);
  }

  function isPanelCollapsed(panelId: string): boolean {
    return isPanelDefaultCollapsed(CREATOR_WRITE_WORKBENCH_MATRIX, creationMode.value, panelId);
  }

  function isLeftRailPanelVisible(panelId: string): boolean {
    if (humanFirstDesk.value) return false;
    return isPanelVisible(panelId);
  }

  const goalCardLines = computed<GoalCardLines>(() => {
    const ov = overview.value;
    const mode = creationMode.value;
    const name = ov?.name || FALLBACK_PROJECT_NAME;
    if (mode === 'companion') {
      return { line1: name, line2: COMPANION_LINE2, line3: COMPANION_LINE3 };
    }
    if (mode === 'advance') {
      return { line1: name, line2: ADVANCE_LINE2, line3: ADVANCE_LINE3 };
    }
    return { line1: name, line2: STUDIO_LINE2, line3: STUDIO_LINE3 };
  });

  const chapterEntities = computed(() => {
    const assets: MemoryAsset[] = (memoryAssets?.value as MemoryAsset[] | undefined)
      ?? (getMemoryAssets ? getMemoryAssets() : []);
    return resolveChapterEntities({
      memoryAssets: assets as unknown as Parameters<typeof resolveChapterEntities>[0]['memoryAssets'],
      chapter: selectedChapter.value,
      bodyText: chapterBodyDraft.value,
    });
  });

  const consistencyItems = computed<ConsistencyItem[]>(() => {
    const ch = selectedChapter.value;
    const items: ConsistencyItem[] = [];
    const visibleList = visibleDeviations?.value;
    const deviationsSource: Deviation[] = (Array.isArray(visibleList) && visibleList.length > 0)
      ? visibleList
      : (overview.value?.deviations as Deviation[] | undefined)
      || [];
    const deviations = deviationsSource
      .filter((d) => !ch || d.chapter === ch)
      .slice(0, 2);
    for (const d of deviations) {
      items.push({
        id: `dev-${d.chapter}-${d.message}`,
        level: d.severity === SEVERITY_ALERT ? 'warn' : 'info',
        text: d.chapter ? `ch${String(d.chapter).padStart(3, '0')} · ${d.message}` : (d.message || ''),
        kind: 'deviation',
      });
    }
    const issues = logicCheckResult?.value?.issues || [];
    for (const issue of issues.slice(0, 2)) {
      if (ch && issue.chapter && issue.chapter !== ch) continue;
      items.push({
        id: `lc-${issue.title || issue.message}`,
        level: issue.severity === SEVERITY_P0 ? 'warn' : 'info',
        text: issue.title || issue.message || '',
        kind: 'logic',
      });
    }
    if (!items.length && ch && !humanFirstDesk.value) {
      items.push({
        id: 'mem-ok',
        level: 'ok',
        text: `ch${String(ch).padStart(3, '0')} 暂无冲突标记`,
        kind: 'memory',
      });
    }
    return items.slice(0, MAX_CONSISTENCY_ITEMS);
  });

  const consistencyPanelOpen = computed<boolean>(() => {
    if (humanFirstDesk.value) {
      return consistencyItems.value.some((i) => i.level === 'warn');
    }
    if (consistencyItems.value.some((i) => i.level === 'warn')) return true;
    return !isPanelCollapsed(PANEL_CONSISTENCY_RAIL);
  });

  async function updateCreationMode(newMode: CreationMode): Promise<unknown> {
    if (!VALID_CREATION_MODES.includes(newMode)) {
      throw new Error(`Invalid creation mode: ${newMode}`);
    }
    const result = await updateCreatorCreationMode(newMode);
    if (overview.value) {
      (overview.value as OverviewLike & { creation_mode?: CreationMode }).creation_mode = newMode;
    }
    return result;
  }

  return {
    workbenchEnabled,
    humanFirstDesk,
    goalCardLines,
    consistencyItems,
    consistencyPanelOpen,
    chapterEntities,
    leftPanelCollapsed,
    isPanelVisible,
    isPanelCollapsed,
    isLeftRailPanelVisible,
    creationMode,
    updateCreationMode,
  };
}
