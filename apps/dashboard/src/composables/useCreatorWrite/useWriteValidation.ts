/**
 * useWriteValidation — 写作验证（P0 复检/逻辑检查点击/偏离点击）
 *
 * Phase 19 Task 5：从 useCreatorWrite.js 拆出（完整实现）。
 * 负责: recheckChapterP0 + handleLogicCheckIssueClick + handleDeviationClick +
 *       onRecheckIssueKeydown + onLogicCheckIssueKeydown +
 *       pulseLogicCheckIssueHighlight + pulseDeviationHighlight +
 *       activeRecheckIssueIdx/activeLogicCheckIssueIdx 状态。
 *
 * 注: 主 hook 拥有 timers（chapterBodyHighlightTimer 等），子模块通过 deps 接收。
 */
import { ref } from 'vue';
import type { Ref } from 'vue';

export interface WriteValidationDeps {
  selectedChapter: Ref<number | null>;
  chapterRecheckResult: Ref<Record<string, unknown> | null>;
  activeRecheckIssueIdxRef: Ref<number | null>;
  activeLogicCheckIssueIdxRef: Ref<number | null>;
  chapterBodyHighlightActiveRef: Ref<boolean>;
  chapterBodyHighlightTimerRef: Ref<ReturnType<typeof setTimeout> | null>;
  logicCheckIssueHighlightTimerRef: Ref<ReturnType<typeof setTimeout> | null>;
  deviationHighlightTimerRef: Ref<ReturnType<typeof setTimeout> | null>;
  uiProfile: import('vue').ComputedRef<Record<string, unknown>>;
  visibleDeviations: import('vue').ComputedRef<Array<Record<string, unknown>>>;
  deviationHighlightEnabled: import('vue').ComputedRef<boolean>;
  highlightedDeviationChapter: Ref<number | null>;
  error: Ref<string | null>;
  handleSaveError: (err: unknown) => void;
  runCompanionLogicCheck: () => Promise<void>;
  setWorkspaceTab?: (tab: string) => void;
  focusIssueParagraph: (issue: Record<string, unknown>, issueIdx: number, source?: string) => void;
}

export interface WriteValidationReturn {
  activeRecheckIssueIdx: Ref<number | null>;
  activeLogicCheckIssueIdx: Ref<number | null>;
  recheckChapterP0: (chapter: number) => Promise<void>;
  handleLogicCheckIssueClick: (issue: Record<string, unknown>, idx: number) => Promise<void>;
  handleDeviationClick: (deviation: Record<string, unknown>) => Promise<void>;
  onRecheckIssueKeydown: (event: KeyboardEvent, issue: Record<string, unknown>, idx: number) => void;
  onLogicCheckIssueKeydown: (event: KeyboardEvent, issue: Record<string, unknown>, idx: number) => void;
  pulseLogicCheckIssueHighlight: (issueIdx: number) => void;
  pulseDeviationHighlight: (chapter: number) => void;
}

export function useWriteValidation(deps: WriteValidationDeps): WriteValidationReturn {
  const {
    selectedChapter,
    chapterRecheckResult,
    activeRecheckIssueIdxRef,
    activeLogicCheckIssueIdxRef,
    chapterBodyHighlightActiveRef,
    chapterBodyHighlightTimerRef,
    logicCheckIssueHighlightTimerRef,
    deviationHighlightTimerRef,
    visibleDeviations,
    deviationHighlightEnabled,
    highlightedDeviationChapter,
    error,
    handleSaveError,
    runCompanionLogicCheck,
    setWorkspaceTab,
    focusIssueParagraph,
  } = deps;

  async function recheckChapterP0(chapter: number): Promise<void> {
    try {
      const { runCreatorLogicCheck } = await import('../../api/index.js');
      const result = await runCreatorLogicCheck({ chapter, scope: 'p0' }) as Record<string, unknown>;
      chapterRecheckResult.value = result;
      activeRecheckIssueIdxRef.value = null;
    } catch (e) {
      handleSaveError(e);
    }
  }

  async function handleLogicCheckIssueClick(issue: Record<string, unknown>, idx: number): Promise<void> {
    activeLogicCheckIssueIdxRef.value = idx;
    if (selectedChapter.value != null) {
      await focusIssueParagraph(issue, idx, 'logic');
    }
    pulseLogicCheckIssueHighlight(idx);
  }

  async function handleDeviationClick(deviation: Record<string, unknown>): Promise<void> {
    const chapter = Number(deviation.chapter);
    if (Number.isFinite(chapter) && chapter > 0) {
      highlightedDeviationChapter.value = chapter;
      if (deviationHighlightEnabled.value) pulseDeviationHighlight(chapter);
    }
    if (setWorkspaceTab) setWorkspaceTab('pulse');
  }

  function onRecheckIssueKeydown(event: KeyboardEvent, issue: Record<string, unknown>, idx: number): void {
    const key = event.key;
    if (key === 'Enter' || key === ' ') {
      event.preventDefault();
      activeRecheckIssueIdxRef.value = idx;
      void focusIssueParagraph(issue, idx, 'recheck');
    }
  }

  function onLogicCheckIssueKeydown(event: KeyboardEvent, issue: Record<string, unknown>, idx: number): void {
    const key = event.key;
    if (key === 'Enter' || key === ' ') {
      event.preventDefault();
      void handleLogicCheckIssueClick(issue, idx);
    }
  }

  function pulseLogicCheckIssueHighlight(issueIdx: number): void {
    activeLogicCheckIssueIdxRef.value = issueIdx;
    if (logicCheckIssueHighlightTimerRef.value) clearTimeout(logicCheckIssueHighlightTimerRef.value);
    logicCheckIssueHighlightTimerRef.value = setTimeout(() => {
      activeLogicCheckIssueIdxRef.value = null;
    }, 1500);
  }

  function pulseDeviationHighlight(chapter: number): void {
    highlightedDeviationChapter.value = chapter;
    if (deviationHighlightTimerRef.value) clearTimeout(deviationHighlightTimerRef.value);
    deviationHighlightTimerRef.value = setTimeout(() => {
      highlightedDeviationChapter.value = null;
    }, 1500);
  }

  return {
    activeRecheckIssueIdx: activeRecheckIssueIdxRef,
    activeLogicCheckIssueIdx: activeLogicCheckIssueIdxRef,
    recheckChapterP0,
    handleLogicCheckIssueClick,
    handleDeviationClick,
    onRecheckIssueKeydown,
    onLogicCheckIssueKeydown,
    pulseLogicCheckIssueHighlight,
    pulseDeviationHighlight,
  };
}