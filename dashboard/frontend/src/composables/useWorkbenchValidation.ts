/**
 * useWorkbenchValidation — 写作工作台轻量校验与冲突标记
 *
 * 从 useCreatorWriteWorkbench 拆出，独立管理轻量校验、质量提示、内联冲突标记。
 * 依赖: chapterBodyDraft, selectedChapter, uiProfile, creationMode, overview,
 *       logicCheckResult, visibleDeviations, focusParagraphByIndex (来自 deps)。
 *
 * @param {Object} deps
 * @param {import('vue').Ref<string>} deps.chapterBodyDraft
 * @param {import('vue').Ref<number|null>} deps.selectedChapter
 * @param {import('vue').ComputedRef<Record<string,unknown>>} deps.uiProfile
 * @param {import('vue').ComputedRef<string>} deps.creationMode
 * @param {import('vue').Ref<Record<string,unknown>|null>} deps.overview
 * @param {import('vue').Ref<{passed?:boolean,p0_count?:number,issues?:Array<{severity?:string,title?:string,message?:string,chapter?:number}>}|null>} deps.logicCheckResult
 * @param {import('vue').ComputedRef<Array<{chapter?:number,severity?:string,message?:string,paragraph?:number}>>} deps.visibleDeviations
 * @param {Function} [deps.focusParagraphByIndex]
 * @param {Function} deps.isPanelVisible
 * @returns {{
 *   qualityHints: import('vue').Ref<Array<{level:string,text:string,source?:string,markerId?:string}>>,
 *   lightValidationIssues: import('vue').Ref<Array<{id:string,kind:string,level:string,label:string,paragraph:number|null,rule:string,fixHint?:string}>>,
 *   lightValidationSummary: import('vue').ComputedRef<{status:string,label:string,warnCount:number,infoCount:number}>,
 *   lightValidationRunning: import('vue').Ref<boolean>,
 *   inlineConflictMarkers: import('vue').ComputedRef<Array<{id:string,kind:string,level:string,label:string,paragraph:number|null,fixHint?:string}>>,
 *   activeInlineConflictId: import('vue').Ref<string|null>,
 *   chapterBodyConflictHighlightActive: import('vue').Ref<boolean>,
 *   showInlineConflictGutter: import('vue').ComputedRef<boolean>,
 *   consistencyItems: import('vue').ComputedRef<Array<{id:string,level:string,text:string,kind:string}>>,
 *   consistencyPanelOpen: import('vue').ComputedRef<boolean>,
 *   focusInlineConflict: (marker: {id:string,kind:string,level:string,label:string,paragraph:number|null,fixHint?:string}) => void,
 *   focusLightValidationIssue: (issue: {id:string,kind:string,level:string,label:string,paragraph:number|null,rule:string,fixHint?:string}) => void,
 *   clearInlineConflictFocus: () => void,
 *   runLightValidationNow: () => void,
 *   scheduleLightValidation: () => void,
 *   dismissQualityHint: (index: number) => void,
 *   syncQualityFromLogicCheck: (result: {passed?:boolean,p0_count?:number,issues?:Array<{severity?:string,title?:string,message?:string,chapter?:number}>}|null) => void,
 * }}
 * 注意: 返回的 ref/computed 在 Pinia destructure 中不需要 .value
 */
import { computed, ref, watch, onUnmounted } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import { runLightValidation, summarizeLightValidation } from '../utils/creatorLightValidationUtils.js';
import { buildInlineConflictMarkers } from '../utils/creatorInlineConflictUtils.js';

interface QualityHint {
  level: string;
  text: string;
  source?: string;
  markerId?: string;
}

interface LightValidationIssue {
  id: string;
  kind: string;
  level: string;
  label: string;
  paragraph: number | null;
  rule: string;
  fixHint?: string;
}

interface LightValidationSummary {
  status: string;
  label: string;
  warnCount: number;
  infoCount: number;
}

interface InlineConflictMarker {
  id: string;
  kind: string;
  level: string;
  label: string;
  paragraph: number | null;
  fixHint?: string;
}

interface ConsistencyItem {
  id: string;
  level: string;
  text: string;
  kind: string;
}

interface DeviationItem {
  chapter?: number;
  severity?: string;
  message?: string;
  paragraph?: number;
}

interface LogicCheckIssue {
  severity?: string;
  title?: string;
  message?: string;
  chapter?: number;
}

interface LogicCheckResult {
  passed?: boolean;
  p0_count?: number;
  issues?: LogicCheckIssue[];
}

interface ValidationDeps {
  chapterBodyDraft: Ref<string>;
  selectedChapter: Ref<number | null>;
  uiProfile: ComputedRef<Record<string, unknown>>;
  creationMode: ComputedRef<string>;
  overview: Ref<Record<string, unknown> | null>;
  logicCheckResult: Ref<LogicCheckResult | null>;
  visibleDeviations: ComputedRef<DeviationItem[]>;
  focusParagraphByIndex?: (paragraph: number, source?: string) => void;
  isPanelVisible: (panelId: string) => boolean;
  humanFirstDesk: ComputedRef<boolean>;
}

export function useWorkbenchValidation(deps: ValidationDeps) {
  const {
    chapterBodyDraft,
    selectedChapter,
    overview,
    logicCheckResult,
    visibleDeviations,
    focusParagraphByIndex,
    isPanelVisible,
    humanFirstDesk,
  } = deps;

  const qualityHints = ref<QualityHint[]>([]);
  const lightValidationIssues = ref<LightValidationIssue[]>([]);
  const lightValidationRunning = ref<boolean>(false);
  let lightValidationTimer: ReturnType<typeof setTimeout> | null = null;

  const activeInlineConflictId = ref<string | null>(null);
  const chapterBodyConflictHighlightActive = ref<boolean>(false);
  let inlineConflictHighlightTimer: ReturnType<typeof setTimeout> | null = null;

  const inlineConflictMarkers = computed<InlineConflictMarker[]>(() =>
    buildInlineConflictMarkers({
      chapter: selectedChapter.value,
      deviations: visibleDeviations?.value || (overview.value?.deviations as DeviationItem[]) || [],
      logicIssues: logicCheckResult?.value?.issues || [],
      lightIssues: lightValidationIssues.value,
    }),
  );

  const lightValidationSummary = computed<LightValidationSummary>(() =>
    summarizeLightValidation(lightValidationIssues.value),
  );

  const showInlineConflictGutter = computed<boolean>(
    () => isPanelVisible('inlineConflictGutter') && inlineConflictMarkers.value.length > 0,
  );

  const consistencyItems = computed<ConsistencyItem[]>(() => {
    const ch = selectedChapter.value;
    const items: ConsistencyItem[] = [];
    const deviations = ((overview.value?.deviations as DeviationItem[]) || [])
      .filter((d) => !ch || d.chapter === ch)
      .slice(0, 2);
    for (const d of deviations) {
      items.push({
        id: `dev-${d.chapter}-${d.message}`,
        level: d.severity === 'alert' ? 'warn' : 'info',
        text: d.chapter
          ? `ch${String(d.chapter).padStart(3, '0')} · ${d.message}`
          : (d.message as string),
        kind: 'deviation',
      });
    }
    const issues = logicCheckResult?.value?.issues || [];
    for (const issue of issues.slice(0, 2)) {
      if (ch && issue.chapter && issue.chapter !== ch) continue;
      items.push({
        id: `lc-${issue.title || issue.message}`,
        level: issue.severity === 'P0' ? 'warn' : 'info',
        text: (issue.title || issue.message) as string,
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
    return items.slice(0, 3);
  });

  function syncQualityFromLightValidation(issues: LightValidationIssue[]): void {
    if (!isPanelVisible('lightValidationBar')) return;
    const summary = summarizeLightValidation(issues);
    if (summary.status === 'ok') {
      const kept = qualityHints.value.filter((h) => h.source !== 'light');
      qualityHints.value = [
        { level: 'ok', text: '轻量校验通过', source: 'light' },
        ...kept,
      ].slice(0, 3);
      return;
    }
    const hints = issues.slice(0, 2).map((issue) => ({
      level: issue.level === 'warn' ? 'warn' : 'info',
      text: issue.label,
      source: 'light' as const,
      markerId: issue.id,
    }));
    const kept = qualityHints.value.filter((h) => h.source !== 'light');
    qualityHints.value = [...hints, ...kept].slice(0, 3);
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
    }, 1200);
  }

  watch(chapterBodyDraft, () => {
    scheduleLightValidation();
  });

  watch(selectedChapter, () => {
    runLightValidationNow();
  });

  function dismissQualityHint(index: number): void {
    qualityHints.value = qualityHints.value.filter((_, i) => i !== index);
  }

  function syncQualityFromLogicCheck(result: LogicCheckResult | null): void {
    const lightKept = qualityHints.value.filter((h) => h.source === 'light');
    if (!result) {
      qualityHints.value = lightKept;
      return;
    }
    const hints: QualityHint[] = [];
    if (result.passed) hints.push({ level: 'ok', text: '逻辑审查通过', source: 'logic' });
    else hints.push({ level: 'warn', text: `P0 问题 ${result.p0_count} 条`, source: 'logic' });
    const issues = (result.issues || []).slice(0, 2);
    for (const issue of issues) {
      hints.push({
        level: 'info',
        text: (issue.title || issue.message) as string,
        source: 'logic',
      });
    }
    qualityHints.value = [...hints, ...lightKept].slice(0, 4);
  }

  function pulseInlineConflictHighlight(): void {
    chapterBodyConflictHighlightActive.value = true;
    if (inlineConflictHighlightTimer) clearTimeout(inlineConflictHighlightTimer);
    inlineConflictHighlightTimer = setTimeout(() => {
      chapterBodyConflictHighlightActive.value = false;
      inlineConflictHighlightTimer = null;
    }, 1400);
  }

  function focusInlineConflict(marker: InlineConflictMarker): void {
    if (!marker) return;
    activeInlineConflictId.value = marker.id;
    if (marker.paragraph && focusParagraphByIndex) {
      focusParagraphByIndex(marker.paragraph, 'inline');
      pulseInlineConflictHighlight();
    }
  }

  function focusLightValidationIssue(issue: LightValidationIssue): void {
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
    qualityHints,
    lightValidationIssues,
    lightValidationSummary,
    lightValidationRunning,
    inlineConflictMarkers,
    activeInlineConflictId,
    chapterBodyConflictHighlightActive,
    showInlineConflictGutter,
    consistencyItems,
    focusInlineConflict,
    focusLightValidationIssue,
    clearInlineConflictFocus,
    runLightValidationNow,
    scheduleLightValidation,
    dismissQualityHint,
    syncQualityFromLogicCheck,
    syncQualityFromLightValidation,
  };
}