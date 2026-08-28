/**
 * useWorkbenchLayout 子模块独立测试（Phase 60.4）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ref, computed } from 'vue';
import type { ComputedRef, Ref } from 'vue';

const matrixMocks = vi.hoisted(() => ({
  isWriteWorkbenchLayoutEnabled: vi.fn(),
  isWriteWorkbenchPanelVisible: vi.fn(),
  isHumanFirstDeskMode: vi.fn(),
  isPanelDefaultCollapsed: vi.fn(),
  CREATOR_WRITE_WORKBENCH_MATRIX: {},
}));

const entityUtilsMocks = vi.hoisted(() => ({
  resolveChapterEntities: vi.fn(),
}));

const apiMocks = vi.hoisted(() => ({
  updateCreatorCreationMode: vi.fn().mockResolvedValue({ ok: true }),
}));

const studioMocks = vi.hoisted(() => ({
  useStudioProject: vi.fn(() => ({
    activeSlug: null,
    projects: [],
    summary: null,
  })),
}));

vi.mock('../../src/config/creatorPanelMatrix.js', () => ({
  isWriteWorkbenchLayoutEnabled: (...args: unknown[]) => matrixMocks.isWriteWorkbenchLayoutEnabled(...args),
  isWriteWorkbenchPanelVisible: (...args: unknown[]) => matrixMocks.isWriteWorkbenchPanelVisible(...args),
  isHumanFirstDeskMode: (...args: unknown[]) => matrixMocks.isHumanFirstDeskMode(...args),
  isPanelDefaultCollapsed: (...args: unknown[]) => matrixMocks.isPanelDefaultCollapsed(...args),
  CREATOR_WRITE_WORKBENCH_MATRIX: matrixMocks.CREATOR_WRITE_WORKBENCH_MATRIX,
}));
vi.mock('../../src/utils/creatorChapterEntityUtils.js', () => ({
  resolveChapterEntities: (...args: unknown[]) => entityUtilsMocks.resolveChapterEntities(...args),
}));
// v16.2.7 T6.D: api/creator.js shim deleted; updateCreatorCreationMode moved to
// @/api/content typed wrapper. Both mocks kept for back-compat (shim deletion
// is the goal; remove this api/creator.js mock when shim is gone).
vi.mock('../../src/api/creator.js', () => ({
  updateCreatorCreationMode: (...args: unknown[]) => apiMocks.updateCreatorCreationMode(...args),
}));
vi.mock('../../src/api/content', () => ({
  updateCreatorCreationMode: (...args: unknown[]) => apiMocks.updateCreatorCreationMode(...args),
}));
vi.mock('../../src/composables/useStudioProject.js', () => ({
  useStudioProject: () => studioMocks.useStudioProject(),
}));

import { useWorkbenchLayout } from '../../src/composables/useCreatorWriteWorkbench/useWorkbenchLayout';

function mountLayout(opts: {
  uiProfile?: Record<string, unknown>;
  overview?: Record<string, unknown> | null;
  chapter?: number | null;
  body?: string;
  memoryAssets?: unknown[];
  logicIssues?: unknown[];
} = {}) {
  const uiProfile = computed(() => opts.uiProfile ?? {}) as unknown as ComputedRef<Record<string, unknown>>;
  const overview = ref<Record<string, unknown> | null>(opts.overview ?? null);
  const selectedChapter = ref<number | null>(opts.chapter ?? null);
  const chapterBodyDraft = ref<string>(opts.body ?? '');
  const memoryAssets = ref<unknown[]>(opts.memoryAssets ?? []);
  const logicCheckResult = ref<{ issues?: unknown[] } | null>(
    opts.logicIssues !== undefined ? { issues: opts.logicIssues } : null,
  );
  const visibleDeviations = computed(() => []);
  const ctx = useWorkbenchLayout({
    uiProfile,
    overview: overview as unknown as Ref<Record<string, unknown> | null>,
    selectedChapter,
    chapterBodyDraft,
    memoryAssets: memoryAssets as unknown as Ref<unknown[]>,
    logicCheckResult: logicCheckResult as unknown as Ref<{ issues?: unknown[] } | null>,
    visibleDeviations,
  } as unknown as Parameters<typeof useWorkbenchLayout>[0]);
  return { ...ctx, uiProfile, overview, selectedChapter, chapterBodyDraft };
}

describe('useWorkbenchLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    matrixMocks.isWriteWorkbenchLayoutEnabled.mockReturnValue(true);
    matrixMocks.isWriteWorkbenchPanelVisible.mockReturnValue(true);
    matrixMocks.isHumanFirstDeskMode.mockReturnValue(false);
    matrixMocks.isPanelDefaultCollapsed.mockReturnValue(false);
    studioMocks.useStudioProject.mockReturnValue({ activeSlug: null, projects: [], summary: null });
  });

  describe('panel visibility', () => {
    it('workbenchEnabled reads from isWriteWorkbenchLayoutEnabled', () => {
      matrixMocks.isWriteWorkbenchLayoutEnabled.mockReturnValueOnce(true);
      const l = mountLayout();
      expect(l.workbenchEnabled.value).toBe(true);
    });

    it('humanFirstDesk reads from isHumanFirstDeskMode', () => {
      matrixMocks.isHumanFirstDeskMode.mockReturnValueOnce(true);
      const l = mountLayout();
      expect(l.humanFirstDesk.value).toBe(true);
    });

    it('isPanelVisible returns false when uiProfile.write_inline_conflict_gutter=false', () => {
      const l = mountLayout({ uiProfile: { write_inline_conflict_gutter: false } });
      expect(l.isPanelVisible('inlineConflictGutter')).toBe(false);
    });

    it('isPanelVisible returns false when uiProfile.write_chapter_entity_rail=false', () => {
      const l = mountLayout({ uiProfile: { write_chapter_entity_rail: false } });
      expect(l.isPanelVisible('chapterEntityRail')).toBe(false);
    });

    it('isPanelVisible delegates to isWriteWorkbenchPanelVisible for other panels', () => {
      matrixMocks.isWriteWorkbenchPanelVisible.mockReturnValueOnce(false);
      const l = mountLayout();
      expect(l.isPanelVisible('someOtherPanel')).toBe(false);
    });

    it('isPanelCollapsed reads from isPanelDefaultCollapsed', () => {
      matrixMocks.isPanelDefaultCollapsed.mockReturnValueOnce(true);
      const l = mountLayout();
      expect(l.isPanelCollapsed('consistencyRail')).toBe(true);
    });

    it('isLeftRailPanelVisible returns false in humanFirstDesk mode', () => {
      matrixMocks.isHumanFirstDeskMode.mockReturnValue(true);
      const l = mountLayout();
      expect(l.isLeftRailPanelVisible('anyPanel')).toBe(false);
    });

    it('isLeftRailPanelVisible delegates to isPanelVisible in normal mode', () => {
      matrixMocks.isHumanFirstDeskMode.mockReturnValue(false);
      matrixMocks.isWriteWorkbenchPanelVisible.mockReturnValueOnce(true);
      const l = mountLayout();
      expect(l.isLeftRailPanelVisible('somePanel')).toBe(true);
    });
  });

  describe('goalCardLines', () => {
    it('returns companion mode 3-line block', () => {
      matrixMocks.isHumanFirstDeskMode.mockReturnValue(false);
      const l = mountLayout({ overview: { creation_mode: 'companion', name: 'Test' } });
      expect(l.goalCardLines.value).toEqual({
        line1: 'Test',
        line2: '陪写本章，你来定稿',
        line3: '选一条路径 → 预览 → 确认落字',
      });
    });

    it('returns advance mode 3-line block', () => {
      matrixMocks.isHumanFirstDeskMode.mockReturnValue(false);
      const l = mountLayout({ overview: { creation_mode: 'advance', name: 'Test' } });
      expect(l.goalCardLines.value.line2).toBe('按卷纲推进，一章一章写');
    });

    it('returns studio mode fallback', () => {
      matrixMocks.isHumanFirstDeskMode.mockReturnValue(false);
      const l = mountLayout({ overview: { creation_mode: 'studio', name: 'Test' } });
      expect(l.goalCardLines.value).toEqual({
        line1: 'Test',
        line2: '工厂模式',
        line3: '产线调度',
      });
    });

    it('uses overview.name when available', () => {
      matrixMocks.isHumanFirstDeskMode.mockReturnValue(false);
      const l = mountLayout({ overview: { creation_mode: 'companion', name: 'MyNovel' } });
      expect(l.goalCardLines.value.line1).toBe('MyNovel');
    });

    it('falls back to "当前项目" when overview is null', () => {
      matrixMocks.isHumanFirstDeskMode.mockReturnValue(false);
      const l = mountLayout({ overview: null });
      expect(l.goalCardLines.value.line1).toBe('当前项目');
    });
  });

  describe('consistencyItems', () => {
    it('aggregates deviations filtered by chapter', () => {
      const l = mountLayout({
        chapter: 5,
        logicIssues: [],
        overview: { deviations: [
          { chapter: 5, severity: 'info', message: 'dev-a' },
          { chapter: 6, severity: 'info', message: 'dev-b-other' },
        ] },
      });
      expect(l.consistencyItems.value.length).toBeGreaterThanOrEqual(1);
      expect(l.consistencyItems.value[0]).toMatchObject({ kind: 'deviation' });
    });

    it('aggregates logic issues filtered by chapter', () => {
      matrixMocks.isHumanFirstDeskMode.mockReturnValue(false);
      const l = mountLayout({
        chapter: 5,
        logicIssues: [
          { chapter: 5, severity: 'P0', title: 'issue-a' },
          { chapter: 6, severity: 'P0', title: 'issue-b-other' },
        ],
        overview: { deviations: [] },
      });
      const logicItems = l.consistencyItems.value.filter((i: { kind: string }) => i.kind === 'logic');
      expect(logicItems).toHaveLength(1);
      expect(logicItems[0]).toMatchObject({ kind: 'logic' });
    });

    it('caps items at 3', () => {
      matrixMocks.isHumanFirstDeskMode.mockReturnValue(false);
      const l = mountLayout({
        chapter: 1,
        logicIssues: [
          { chapter: 1, title: 'a' },
          { chapter: 1, title: 'b' },
          { chapter: 1, title: 'c' },
          { chapter: 1, title: 'd' },
        ],
        overview: { deviations: [] },
      });
      expect(l.consistencyItems.value.length).toBeLessThanOrEqual(3);
    });

    it('falls back to ok memory item when no items and not humanFirstDesk', () => {
      matrixMocks.isHumanFirstDeskMode.mockReturnValue(false);
      const l = mountLayout({ chapter: 1, overview: { deviations: [] } });
      const memItem = l.consistencyItems.value.find((i: { kind: string }) => i.kind === 'memory');
      expect(memItem).toBeDefined();
    });

    it('no fallback when humanFirstDesk', () => {
      matrixMocks.isHumanFirstDeskMode.mockReturnValue(true);
      const l = mountLayout({ chapter: 1, overview: { deviations: [] } });
      expect(l.consistencyItems.value).toHaveLength(0);
    });
  });

  describe('consistencyPanelOpen', () => {
    it('humanFirstDesk: open when any warn', () => {
      matrixMocks.isHumanFirstDeskMode.mockReturnValue(true);
      const l = mountLayout({
        chapter: 1,
        overview: { deviations: [{ chapter: 1, severity: 'alert', message: 'dev' }] },
      });
      expect(l.consistencyPanelOpen.value).toBe(true);
    });

    it('non-humanFirstDesk: open when panel not collapsed and no warn', () => {
      matrixMocks.isHumanFirstDeskMode.mockReturnValue(false);
      matrixMocks.isPanelDefaultCollapsed.mockReturnValue(false);
      const l = mountLayout({ chapter: 1, overview: { deviations: [] } });
      expect(l.consistencyPanelOpen.value).toBe(true);
    });

    it('non-humanFirstDesk: closed when panel collapsed and no warn', () => {
      matrixMocks.isHumanFirstDeskMode.mockReturnValue(false);
      matrixMocks.isPanelDefaultCollapsed.mockReturnValue(true);
      const l = mountLayout({ chapter: 1, overview: { deviations: [] } });
      expect(l.consistencyPanelOpen.value).toBe(false);
    });
  });

  describe('chapterEntities', () => {
    it('delegates to resolveChapterEntities with memory assets', () => {
      const entities = [{ id: 'e1', name: 'X' }];
      entityUtilsMocks.resolveChapterEntities.mockReturnValueOnce(entities);
      const l = mountLayout({ chapter: 1, memoryAssets: [{ id: 'm1', name: 'asset' }] });
      expect(l.chapterEntities.value).toBe(entities);
      expect(entityUtilsMocks.resolveChapterEntities).toHaveBeenCalledWith(
        expect.objectContaining({ chapter: 1 }),
      );
    });

    it('uses getMemoryAssets fallback when memoryAssets ref is undefined', () => {
      entityUtilsMocks.resolveChapterEntities.mockReturnValueOnce([]);
      const ctx = useWorkbenchLayout({
        uiProfile: computed(() => ({})) as unknown as ComputedRef<Record<string, unknown>>,
        overview: ref(null) as unknown as Ref<Record<string, unknown> | null>,
        selectedChapter: ref<number | null>(null),
        chapterBodyDraft: ref(''),
        getMemoryAssets: () => [{ id: 'a', name: 'A' }],
      } as unknown as Parameters<typeof useWorkbenchLayout>[0]);
      expect(ctx.chapterEntities.value).toEqual([]);
      expect(entityUtilsMocks.resolveChapterEntities).toHaveBeenCalledWith(
        expect.objectContaining({ memoryAssets: [{ id: 'a', name: 'A' }] }),
      );
    });
  });

  describe('updateCreationMode', () => {
    it('rejects invalid mode', async () => {
      const l = mountLayout();
      await expect(l.updateCreationMode('invalid' as never)).rejects.toThrow(/Invalid creation mode/);
    });

    it('calls updateCreatorCreationMode API for valid mode', async () => {
      const l = mountLayout();
      await l.updateCreationMode('advance');
      expect(apiMocks.updateCreatorCreationMode).toHaveBeenCalledWith('advance');
    });

    it('mutates overview.value.creation_mode', async () => {
      const l = mountLayout({ overview: { creation_mode: 'companion' } });
      await l.updateCreationMode('advance');
      expect((l.overview.value as Record<string, unknown>).creation_mode).toBe('advance');
    });
  });
});
