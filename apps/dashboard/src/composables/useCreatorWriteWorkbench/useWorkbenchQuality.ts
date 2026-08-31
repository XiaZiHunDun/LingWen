/**
 * useWorkbenchQuality — 校验/质量/冲突/意图/生成（Phase 60.3）
 *
 * 从 useCreatorWriteWorkbench.js 拆出：
 * - intent: intentText/Genre/Mood/Type/Theme + intentHistory + save/load/clear
 * - validation: lightValidationIssues/Summary/Running + runNow/schedule + syncFromLight
 * - quality hints: 通过 selectionQualityHints deps 共享（不持有）
 * - conflicts: inlineConflictMarkers (computed) + focusInlineConflict/focusLightValidationIssue/clearFocus/pulseHighlight
 * - generation: generateIntensity/Running + startQuickWrite/stopGenerate
 *
 * Agent 调用通过 deps 注入 getAgent callback（避免子模块 import useCreatorAgent）。
 * selectionQualityHints 是外部 ref（来自 useWorkbenchSelection），通过 deps 共享写入。
 */
import { computed, onUnmounted, ref, watch } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import {
  runLightValidation,
  summarizeLightValidation,
} from '../../utils/creatorLightValidationUtils.js';
import { buildInlineConflictMarkers } from '../../utils/creatorInlineConflictUtils.js';

type QualityLevel = 'ok' | 'info' | 'warn';

interface QualityHint {
  level: QualityLevel;
  text: string;
  source?: string;
  markerId?: string;
}

interface IntentEntry {
  id: string;
  text: string;
  mood: string;
  type: string;
  theme: string;
  timestamp: string;
}

interface LightValidationIssue {
  id: string;
  kind?: string;
  level: 'warn' | 'info';
  label: string;
  paragraph?: number | null;
  rule?: string;
  fixHint?: string;
}

interface LogicCheckIssue {
  title?: string;
  message?: string;
  severity?: string;
  chapter?: number;
}

interface LogicCheckResult {
  passed: boolean;
  p0_count?: number;
  issues?: LogicCheckIssue[];
}

interface Deviation {
  chapter?: number;
  severity?: string;
  message?: string;
  paragraph?: number;
}

interface InlineConflictMarker {
  id: string;
  kind?: string;
  level?: string;
  label?: string;
  paragraph?: number | null;
  fixHint?: string | null;
}

interface AgentLike {
  runPlan: (mode: string, label: string) => Promise<unknown>;
  generating: Ref<boolean>;
  statusLine: Ref<string>;
  candidates: Ref<unknown[]>;
  directorAdvice: Ref<unknown[]>;
}

interface OverviewLike {
  slug?: string;
  name?: string;
  creation_mode?: string;
  deviations?: Deviation[];
}

export interface WorkbenchQualityDeps {
  selectedChapter: Ref<number | null>;
  chapterBodyDraft: Ref<string>;
  visibleDeviations?: ComputedRef<Deviation[]>;
  logicCheckResult?: Ref<LogicCheckResult | null>;
  selectionQualityHints: Ref<QualityHint[]>;
  overview?: Ref<OverviewLike | null>;
  isPanelVisible: (panelId: string) => boolean;
  getAgent: () => AgentLike;
  focusParagraphByIndex?: (paragraph: number, source?: string) => void;
}

export interface WorkbenchQualityReturn {
  // Intent
  intentText: Ref<string>;
  intentGenre: Ref<string>;
  intentMood: Ref<string>;
  intentType: Ref<string>;
  intentTheme: Ref<string>;
  intentHistory: Ref<IntentEntry[]>;
  saveIntentToHistory: () => void;
  loadIntentFromHistory: (intent: IntentEntry) => void;
  clearIntentHistory: () => void;

  // Quality hints (writes to shared selectionQualityHints ref via deps)
  dismissQualityHint: (index: number) => void;
  syncQualityFromLightValidation: (issues: LightValidationIssue[]) => void;
  syncQualityFromLogicCheck: (result: LogicCheckResult | null) => void;

  // Light validation
  lightValidationIssues: Ref<LightValidationIssue[]>;
  lightValidationSummary: ComputedRef<ReturnType<typeof summarizeLightValidation>>;
  lightValidationRunning: Ref<boolean>;
  runLightValidationNow: () => void;
  scheduleLightValidation: () => void;

  // Inline conflicts
  inlineConflictMarkers: ComputedRef<InlineConflictMarker[]>;
  activeInlineConflictId: Ref<string | null>;
  chapterBodyConflictHighlightActive: Ref<boolean>;
  focusInlineConflict: (marker: InlineConflictMarker | null) => void;
  focusLightValidationIssue: (issue: { id: string; paragraph?: number }) => void;
  clearInlineConflictFocus: () => void;

  // Generation
  generateIntensity: Ref<string>;
  generateRunning: Ref<boolean>;
  startQuickWrite: (actionLabel?: string | null) => Promise<void>;
  stopGenerate: () => void;
}

const MAX_INTENT_HISTORY = 10;
const LIGHT_VALIDATION_DEBOUNCE_MS = 1200;
const HIGHLIGHT_PULSE_MS = 1400;
const MAX_QUALITY_HINTS_LIGHT = 3;
const MAX_QUALITY_HINTS_LOGIC = 4;

export function useWorkbenchQuality(
  deps: WorkbenchQualityDeps,
): WorkbenchQualityReturn {
  const {
    selectedChapter,
    chapterBodyDraft,
    visibleDeviations,
    logicCheckResult,
    selectionQualityHints,
    overview,
    isPanelVisible,
    getAgent,
    focusParagraphByIndex,
  } = deps;

  // ── Intent ──
  const intentText = ref('');
  const intentGenre = ref('');
  const intentMood = ref('');
  const intentType = ref('');
  const intentTheme = ref('');
  const intentHistory = ref<IntentEntry[]>([]);

  function saveIntentToHistory(): void {
    if (!intentText.value.trim()) return;
    const intent: IntentEntry = {
      id: `intent-${Date.now()}`,
      text: intentText.value,
      mood: intentMood.value,
      type: intentType.value,
      theme: intentTheme.value,
      timestamp: new Date().toISOString(),
    };
    intentHistory.value = [intent, ...intentHistory.value].slice(0, MAX_INTENT_HISTORY);
  }

  function loadIntentFromHistory(intent: IntentEntry): void {
    intentText.value = intent.text;
    intentMood.value = intent.mood || '';
    intentType.value = intent.type || '';
    intentTheme.value = intent.theme || '';
  }

  function clearIntentHistory(): void {
    intentHistory.value = [];
  }

  // ── Light validation ──
  const lightValidationIssues = ref<LightValidationIssue[]>([]);
  const lightValidationRunning = ref(false);
  let lightValidationTimer: ReturnType<typeof setTimeout> | null = null;

  const lightValidationSummary = computed(() =>
    summarizeLightValidation(lightValidationIssues.value),
  );

  function syncQualityFromLightValidation(issues: LightValidationIssue[]): void {
    if (!isPanelVisible('lightValidationBar')) return;
    const summary = summarizeLightValidation(issues);
    const base = selectionQualityHints.value.filter((h) => h.source !== 'light');
    if (summary.status === 'ok') {
      const okHint: QualityHint = { level: 'ok', text: '轻量校验通过', source: 'light' };
      selectionQualityHints.value = [okHint, ...base].slice(0, MAX_QUALITY_HINTS_LIGHT);
      return;
    }
    const hints: QualityHint[] = issues.slice(0, 2).map((issue) => ({
      level: issue.level === 'warn' ? 'warn' : 'info',
      text: issue.label,
      source: 'light',
      markerId: issue.id,
    }));
    selectionQualityHints.value = [...hints, ...base].slice(0, MAX_QUALITY_HINTS_LIGHT);
  }

  function runLightValidationNow(): void {
    if (!isPanelVisible('lightValidationBar')) {
      lightValidationIssues.value = [];
      return;
    }
    lightValidationRunning.value = true;
    const issues = runLightValidation({
      body: chapterBodyDraft.value,
      chapter: selectedChapter.value,
    });
    lightValidationIssues.value = issues;
    syncQualityFromLightValidation(issues);
    lightValidationRunning.value = false;
  }

  function scheduleLightValidation(): void {
    if (!isPanelVisible('lightValidationBar')) return;
    if (lightValidationTimer) clearTimeout(lightValidationTimer);
    lightValidationTimer = setTimeout(() => {
      runLightValidationNow();
      lightValidationTimer = null;
    }, LIGHT_VALIDATION_DEBOUNCE_MS);
  }

  // ── Quality hints ──
  function dismissQualityHint(index: number): void {
    selectionQualityHints.value = selectionQualityHints.value.filter((_, i) => i !== index);
  }

  function syncQualityFromLogicCheck(result: LogicCheckResult | null): void {
    const lightKept = selectionQualityHints.value.filter((h) => h.source === 'light');
    if (!result) {
      selectionQualityHints.value = lightKept;
      return;
    }
    const hints: QualityHint[] = [];
    if (result.passed) {
      hints.push({ level: 'ok', text: '逻辑审查通过', source: 'logic' });
    } else {
      hints.push({ level: 'warn', text: `P0 问题 ${result.p0_count ?? 0} 条`, source: 'logic' });
    }
    const issues = (result.issues || []).slice(0, 2);
    for (const issue of issues) {
      hints.push({ level: 'info', text: issue.title || issue.message || '', source: 'logic' });
    }
    selectionQualityHints.value = [...hints, ...lightKept].slice(0, MAX_QUALITY_HINTS_LOGIC);
  }

  // ── Inline conflicts ──
  const activeInlineConflictId = ref<string | null>(null);
  const chapterBodyConflictHighlightActive = ref(false);
  let inlineConflictHighlightTimer: ReturnType<typeof setTimeout> | null = null;

  const inlineConflictMarkers = computed(() =>
    buildInlineConflictMarkers({
      chapter: selectedChapter.value,
      deviations: visibleDeviations?.value || (overview?.value?.deviations as Deviation[] | undefined) || [],
      logicIssues: (logicCheckResult?.value?.issues as LogicCheckIssue[] | undefined) || [],
      lightIssues: lightValidationIssues.value,
    }),
  );

  function pulseInlineConflictHighlight(): void {
    chapterBodyConflictHighlightActive.value = true;
    if (inlineConflictHighlightTimer) clearTimeout(inlineConflictHighlightTimer);
    inlineConflictHighlightTimer = setTimeout(() => {
      chapterBodyConflictHighlightActive.value = false;
      inlineConflictHighlightTimer = null;
    }, HIGHLIGHT_PULSE_MS);
  }

  function focusInlineConflict(marker: InlineConflictMarker | null): void {
    if (!marker) return;
    activeInlineConflictId.value = marker.id;
    if (marker.paragraph && focusParagraphByIndex) {
      focusParagraphByIndex(marker.paragraph, 'inline');
      pulseInlineConflictHighlight();
    }
  }

  function focusLightValidationIssue(issue: { id: string; paragraph?: number }): void {
    if (!issue) return;
    const marker = inlineConflictMarkers.value.find((m) => m.id === issue.id);
    if (marker) {
      focusInlineConflict(marker);
      return;
    }
    if (issue.paragraph && focusParagraphByIndex) {
      focusParagraphByIndex(issue.paragraph, 'inline');
      pulseInlineConflictHighlight();
    }
  }

  function clearInlineConflictFocus(): void {
    activeInlineConflictId.value = null;
  }

  // ── Generation ──
  const generateIntensity = ref('balanced');
  const generateRunning = ref(false);

  async function startQuickWrite(actionLabel: string | null = null): Promise<void> {
    if (!intentText.value.trim()) {
      selectionQualityHints.value = [
        { level: 'warn', text: '可先输入一句话意图，或直接在正文区开写' },
        ...selectionQualityHints.value,
      ];
      return;
    }
    generateRunning.value = true;
    try {
      const agent = getAgent();
      const label = actionLabel || `一键开写：${intentText.value.trim()}`;
      await agent.runPlan('quick-write', label);
      if (!agent.candidates.value.length && !agent.directorAdvice.value.length) {
        return;
      }
      selectionQualityHints.value = [
        { level: 'info', text: '从左侧或下方选择候选，确认后写入正文' },
        ...selectionQualityHints.value,
      ];
    } finally {
      generateRunning.value = false;
    }
  }

  function stopGenerate(): void {
    generateRunning.value = false;
    const agent = getAgent();
    agent.generating.value = false;
    agent.statusLine.value = '已停止';
  }

  // ── Watchers + lifecycle ──
  watch(chapterBodyDraft, () => {
    scheduleLightValidation();
  });

  watch(selectedChapter, () => {
    runLightValidationNow();
  });

  onUnmounted(() => {
    if (lightValidationTimer) {
      clearTimeout(lightValidationTimer);
      lightValidationTimer = null;
    }
    if (inlineConflictHighlightTimer) {
      clearTimeout(inlineConflictHighlightTimer);
      inlineConflictHighlightTimer = null;
    }
  });

  return {
    intentText, intentGenre, intentMood, intentType, intentTheme,
    intentHistory, saveIntentToHistory, loadIntentFromHistory, clearIntentHistory,
    dismissQualityHint,
    syncQualityFromLightValidation, syncQualityFromLogicCheck,
    lightValidationIssues, lightValidationSummary, lightValidationRunning,
    runLightValidationNow, scheduleLightValidation,
    inlineConflictMarkers, activeInlineConflictId, chapterBodyConflictHighlightActive,
    focusInlineConflict, focusLightValidationIssue, clearInlineConflictFocus,
    generateIntensity, generateRunning, startQuickWrite, stopGenerate,
  };
}
