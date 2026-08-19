/**
 * useWorkbenchQuality 子模块独立测试（Phase 60.3）
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { defineComponent, ref, computed } from 'vue';
import { mount } from '@vue/test-utils';

const utilsMocks = vi.hoisted(() => ({
  runLightValidation: vi.fn(),
  summarizeLightValidation: vi.fn(),
  buildInlineConflictMarkers: vi.fn(),
}));

vi.mock('../../src/utils/creatorLightValidationUtils.js', () => ({
  runLightValidation: (...args: unknown[]) => utilsMocks.runLightValidation(...args),
  summarizeLightValidation: (...args: unknown[]) => utilsMocks.summarizeLightValidation(...args),
}));
vi.mock('../../src/utils/creatorInlineConflictUtils.js', () => ({
  buildInlineConflictMarkers: (...args: unknown[]) => utilsMocks.buildInlineConflictMarkers(...args),
}));

import { useWorkbenchQuality } from '../../src/composables/useCreatorWriteWorkbench/useWorkbenchQuality';

function mountQuality(opts: {
  body?: string;
  panelVisible?: boolean;
  agentStatus?: string;
} = {}) {
  const selectedChapter = ref<number | null>(1);
  const chapterBodyDraft = ref<string>(opts.body ?? '');
  const visibleDeviations = computed<unknown[]>(() => []);
  const logicCheckResult = ref<{ passed: boolean; p0_count: number; issues: unknown[] } | null>(null);
  const selectionQualityHints = ref<Array<Record<string, unknown>>>([]);
  const overview = ref<{ deviations: unknown[] } | null>(null);
  const isPanelVisible = vi.fn((id: string) => id === 'lightValidationBar' && (opts.panelVisible ?? true));
  const focusParagraphByIndex = vi.fn();
  const agentStatus = ref<string>(opts.agentStatus ?? 'idle');
  const candidates = ref<unknown[]>([]);
  const directorAdvice = ref<unknown[]>([]);
  const agent = {
    runPlan: vi.fn().mockResolvedValue(undefined),
    generating: ref(false),
    statusLine: agentStatus,
    candidates,
    directorAdvice,
  };
  const ctx = useWorkbenchQuality({
    selectedChapter,
    chapterBodyDraft,
    visibleDeviations,
    logicCheckResult,
    selectionQualityHints,
    overview,
    isPanelVisible,
    getAgent: () => agent,
    focusParagraphByIndex,
  } as unknown as Parameters<typeof useWorkbenchQuality>[0]);
  return { ...ctx, agent, isPanelVisible, focusParagraphByIndex, selectionQualityHints, logicCheckResult, chapterBodyDraft };
}

describe('useWorkbenchQuality', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    utilsMocks.summarizeLightValidation.mockReturnValue({ status: 'ok' });
    utilsMocks.runLightValidation.mockReturnValue([]);
  });

  describe('intent CRUD', () => {
    it('saveIntentToHistory appends entry with id+timestamp', () => {
      const q = mountQuality();
      q.intentText.value = 'try a heist';
      q.intentMood.value = 'tense';
      q.saveIntentToHistory();
      expect(q.intentHistory.value).toHaveLength(1);
      expect(q.intentHistory.value[0]).toMatchObject({ text: 'try a heist', mood: 'tense' });
      expect(q.intentHistory.value[0].id).toMatch(/^intent-/);
    });

    it('saveIntentToHistory caps at 10', () => {
      const q = mountQuality();
      for (let i = 0; i < 12; i++) {
        q.intentText.value = `i${i}`;
        q.saveIntentToHistory();
      }
      expect(q.intentHistory.value).toHaveLength(10);
    });

    it('saveIntentToHistory ignores empty text', () => {
      const q = mountQuality();
      q.saveIntentToHistory();
      expect(q.intentHistory.value).toHaveLength(0);
    });

    it('loadIntentFromHistory restores fields', () => {
      const q = mountQuality();
      q.intentText.value = 'old';
      q.saveIntentToHistory();
      q.intentText.value = '';
      q.loadIntentFromHistory(q.intentHistory.value[0]);
      expect(q.intentText.value).toBe('old');
    });

    it('loadIntentFromHistory restores intentMood + intentType + intentTheme', () => {
      const q = mountQuality();
      q.intentText.value = 'heist setup';
      q.intentMood.value = 'tense';
      q.intentType.value = 'plot-twist';
      q.intentTheme.value = 'betrayal';
      q.saveIntentToHistory();
      q.intentText.value = '';
      q.intentMood.value = '';
      q.intentType.value = '';
      q.intentTheme.value = '';
      q.loadIntentFromHistory(q.intentHistory.value[0]);
      expect(q.intentMood.value).toBe('tense');
      expect(q.intentType.value).toBe('plot-twist');
      expect(q.intentTheme.value).toBe('betrayal');
    });

    it('clearIntentHistory empties list', () => {
      const q = mountQuality();
      q.intentText.value = 'x';
      q.saveIntentToHistory();
      q.clearIntentHistory();
      expect(q.intentHistory.value).toEqual([]);
    });
  });

  describe('light validation', () => {
    it('runLightValidationNow updates issues', () => {
      utilsMocks.runLightValidation.mockReturnValueOnce([{ id: 'i1', level: 'warn', label: 'x' }]);
      const q = mountQuality();
      q.runLightValidationNow();
      expect(q.lightValidationIssues.value).toEqual([{ id: 'i1', level: 'warn', label: 'x' }]);
    });

    it('runLightValidationNow noop when panel hidden', () => {
      const q = mountQuality({ panelVisible: false });
      q.runLightValidationNow();
      expect(q.lightValidationIssues.value).toEqual([]);
      expect(utilsMocks.runLightValidation).not.toHaveBeenCalled();
    });

    it('scheduleLightValidation debounces', async () => {
      vi.useFakeTimers();
      const q = mountQuality();
      q.scheduleLightValidation();
      q.scheduleLightValidation();
      expect(utilsMocks.runLightValidation).not.toHaveBeenCalled();
      vi.advanceTimersByTime(1200);
      expect(utilsMocks.runLightValidation).toHaveBeenCalledTimes(1);
      vi.useRealTimers();
    });

    it('lightValidationSummary computed reflects summarizeLightValidation', () => {
      utilsMocks.summarizeLightValidation.mockReturnValue({ status: 'ok' });
      const q = mountQuality();
      expect(q.lightValidationSummary.value).toEqual({ status: 'ok' });
      utilsMocks.summarizeLightValidation.mockReturnValue({
        status: 'warn',
        count: 2,
      });
      q.lightValidationIssues.value = [
        { id: 'i1', level: 'warn', label: 'x' },
        { id: 'i2', level: 'warn', label: 'y' },
      ];
      expect(q.lightValidationSummary.value).toEqual({ status: 'warn', count: 2 });
      expect(utilsMocks.summarizeLightValidation).toHaveBeenCalled();
    });

    it('watch(chapterBodyDraft) triggers scheduleLightValidation', async () => {
      vi.useFakeTimers();
      const q = mountQuality({ body: 'first' });
      q.chapterBodyDraft.value = 'second draft';
      // flush Vue's async watch microtask without firing setTimeout callbacks
      await Promise.resolve();
      expect(utilsMocks.runLightValidation).not.toHaveBeenCalled();
      vi.advanceTimersByTime(1200);
      expect(utilsMocks.runLightValidation).toHaveBeenCalledTimes(1);
      vi.useRealTimers();
    });
  });

  describe('quality hints', () => {
    it('dismissQualityHint removes by index', () => {
      const q = mountQuality();
      q.selectionQualityHints.value = [{ level: 'warn', text: 'a' }, { level: 'warn', text: 'b' }];
      q.dismissQualityHint(0);
      expect(q.selectionQualityHints.value).toEqual([{ level: 'warn', text: 'b' }]);
    });

    it('syncQualityFromLogicCheck ok sets passed hint', () => {
      const q = mountQuality();
      q.syncQualityFromLogicCheck({ passed: true, p0_count: 0, issues: [] });
      expect(q.selectionQualityHints.value[0]).toMatchObject({ level: 'ok', text: '逻辑审查通过' });
    });

    it('syncQualityFromLogicCheck warn shows p0 count', () => {
      const q = mountQuality();
      q.syncQualityFromLogicCheck({ passed: false, p0_count: 3, issues: [{ title: 'P0-1' }] });
      expect(q.selectionQualityHints.value[0]).toMatchObject({ level: 'warn', text: 'P0 问题 3 条' });
    });

    it('syncQualityFromLogicCheck null keeps light hints', () => {
      const q = mountQuality();
      q.selectionQualityHints.value = [{ level: 'warn', text: 'light-x', source: 'light' }];
      q.syncQualityFromLogicCheck(null);
      expect(q.selectionQualityHints.value).toEqual([{ level: 'warn', text: 'light-x', source: 'light' }]);
    });

    it('syncQualityFromLightValidation ok state replaces hint with light-ok', () => {
      utilsMocks.summarizeLightValidation.mockReturnValue({ status: 'ok' });
      const q = mountQuality();
      q.selectionQualityHints.value = [{ level: 'warn', text: 'stale', source: 'logic' }];
      q.syncQualityFromLightValidation([]);
      expect(q.selectionQualityHints.value).toEqual([
        { level: 'ok', text: '轻量校验通过', source: 'light' },
        { level: 'warn', text: 'stale', source: 'logic' },
      ]);
    });

    it('syncQualityFromLightValidation warn state appends hints', () => {
      utilsMocks.summarizeLightValidation.mockReturnValue({ status: 'warn', count: 2 });
      const q = mountQuality();
      q.selectionQualityHints.value = [{ level: 'info', text: 'kept', source: 'logic' }];
      q.syncQualityFromLightValidation([
        { id: 'i1', level: 'warn', label: 'A' },
        { id: 'i2', level: 'info', label: 'B' },
      ]);
      expect(q.selectionQualityHints.value).toHaveLength(3);
      expect(q.selectionQualityHints.value[0]).toMatchObject({
        level: 'warn',
        text: 'A',
        source: 'light',
        markerId: 'i1',
      });
      expect(q.selectionQualityHints.value[1]).toMatchObject({
        level: 'info',
        text: 'B',
        source: 'light',
        markerId: 'i2',
      });
      expect(q.selectionQualityHints.value[2]).toMatchObject({
        level: 'info',
        text: 'kept',
        source: 'logic',
      });
    });
  });

  describe('inline conflicts', () => {
    it('focusInlineConflict sets activeId + paragraph', () => {
      const q = mountQuality();
      q.focusInlineConflict({ id: 'm1', paragraph: 3 } as never);
      expect(q.activeInlineConflictId.value).toBe('m1');
      expect(q.focusParagraphByIndex).toHaveBeenCalledWith(3, 'inline');
      expect(q.chapterBodyConflictHighlightActive.value).toBe(true);
    });

    it('focusInlineConflict with no paragraph skips highlight', () => {
      const q = mountQuality();
      q.focusInlineConflict({ id: 'm1' } as never);
      expect(q.activeInlineConflictId.value).toBe('m1');
      expect(q.focusParagraphByIndex).not.toHaveBeenCalled();
    });

    it('clearInlineConflictFocus resets activeId', () => {
      const q = mountQuality();
      q.activeInlineConflictId.value = 'x';
      q.clearInlineConflictFocus();
      expect(q.activeInlineConflictId.value).toBeNull();
    });

    it('focusLightValidationIssue finds marker in inlineConflictMarkers', () => {
      utilsMocks.buildInlineConflictMarkers.mockReturnValue([
        { id: 'm1', paragraph: 5 },
      ]);
      const q = mountQuality();
      q.focusLightValidationIssue({ id: 'm1', paragraph: 5 });
      expect(q.activeInlineConflictId.value).toBe('m1');
      expect(q.focusParagraphByIndex).toHaveBeenCalledWith(5, 'inline');
      expect(q.chapterBodyConflictHighlightActive.value).toBe(true);
    });

    it('focusLightValidationIssue falls back to paragraph focus when no marker', () => {
      utilsMocks.buildInlineConflictMarkers.mockReturnValue([]);
      const q = mountQuality();
      q.focusLightValidationIssue({ id: 'unknown', paragraph: 7 });
      expect(q.activeInlineConflictId.value).toBeNull();
      expect(q.focusParagraphByIndex).toHaveBeenCalledWith(7, 'inline');
      expect(q.chapterBodyConflictHighlightActive.value).toBe(true);
    });

    it('pulseInlineConflictHighlight sets+clears highlight after 1400ms', () => {
      vi.useFakeTimers();
      const q = mountQuality();
      q.focusInlineConflict({ id: 'm1', paragraph: 1 } as never);
      expect(q.chapterBodyConflictHighlightActive.value).toBe(true);
      vi.advanceTimersByTime(1399);
      expect(q.chapterBodyConflictHighlightActive.value).toBe(true);
      vi.advanceTimersByTime(2);
      expect(q.chapterBodyConflictHighlightActive.value).toBe(false);
      vi.useRealTimers();
    });
  });

  describe('generation control', () => {
    it('startQuickWrite with empty intent yields warn hint', async () => {
      const q = mountQuality();
      await q.startQuickWrite();
      expect(q.selectionQualityHints.value[0]).toMatchObject({ level: 'warn' });
      expect(q.agent.runPlan).not.toHaveBeenCalled();
    });

    it('startQuickWrite runs agent.runPlan', async () => {
      const q = mountQuality();
      q.intentText.value = 'go';
      await q.startQuickWrite('custom-label');
      expect(q.agent.runPlan).toHaveBeenCalledWith('quick-write', 'custom-label');
    });

    it('stopGenerate resets state + statusLine', () => {
      const q = mountQuality({ agentStatus: 'running' });
      q.generateRunning.value = true;
      q.stopGenerate();
      expect(q.generateRunning.value).toBe(false);
      expect(q.agent.statusLine.value).toBe('已停止');
    });
  });

  describe('inlineConflictMarkers computed delegates to buildInlineConflictMarkers', () => {
    it('passes selectedChapter + deviations + issues + lightIssues', () => {
      const q = mountQuality();
      utilsMocks.buildInlineConflictMarkers.mockReturnValueOnce([{ id: 'mk', paragraph: 2 }]);
      expect(q.inlineConflictMarkers.value).toEqual([{ id: 'mk', paragraph: 2 }]);
      expect(utilsMocks.buildInlineConflictMarkers).toHaveBeenCalledWith(
        expect.objectContaining({ chapter: 1, lightIssues: [] }),
      );
    });
  });

  describe('lifecycle', () => {
    it('onUnmounted clears both timers', () => {
      vi.useFakeTimers();
      const selectedChapter = ref<number | null>(1);
      const chapterBodyDraft = ref<string>('');
      const selectionQualityHints = ref<Array<Record<string, unknown>>>([]);
      const logicCheckResult = ref<{ passed: boolean; p0_count: number; issues: unknown[] } | null>(null);
      const isPanelVisible = vi.fn((id: string) => id === 'lightValidationBar');
      const agent = {
        runPlan: vi.fn().mockResolvedValue(undefined),
        generating: ref(false),
        statusLine: ref('idle'),
        candidates: ref<unknown[]>([]),
        directorAdvice: ref<unknown[]>([]),
      };
      let api!: ReturnType<typeof useWorkbenchQuality>;
      const Comp = defineComponent({
        setup() {
          api = useWorkbenchQuality({
            selectedChapter,
            chapterBodyDraft,
            logicCheckResult,
            selectionQualityHints,
            isPanelVisible,
            getAgent: () => agent,
            focusParagraphByIndex: vi.fn(),
          } as unknown as Parameters<typeof useWorkbenchQuality>[0]);
          return () => null;
        },
      });
      const wrapper = mount(Comp);
      api.scheduleLightValidation();
      api.focusInlineConflict({ id: 'm1', paragraph: 1 } as never);
      expect(vi.getTimerCount()).toBeGreaterThanOrEqual(2);
      wrapper.unmount();
      expect(vi.getTimerCount()).toBe(0);
      vi.useRealTimers();
    });
  });
});
