/**
 * useWriteTools — 写作工具（format/label/class/highlight/batch inline summary）
 *
 * Phase 19 Task 5：从 useCreatorWrite.js 拆出（完整实现）。
 * 负责: formatBodySaveTime + chapterRowClass + chapterVolumeLabel + chapterRowTitle +
 *       pulseChapterBodyHighlight + focusIssueParagraph +
 *       batchDeviationsInRange + scrollToBatchDeviationList +
 *       openFirstBatchDeviationChapter + updateBatchDeviationInlineSummary +
 *       linkBatchDeviationInlineSummary + dismissBatchDeviationInlineSummary +
 *       navigateIssueList。
 */
import { ref } from 'vue';
import type { ComputedRef, Ref } from 'vue';

export interface WriteToolsDeps {
  uiProfile: ComputedRef<Record<string, unknown>>;
  chapterBodyDraft: Ref<string>;
  chapterBodyTextareaRef: Ref<unknown>;
  chapterBodyHighlightActiveRef: Ref<boolean>;
  chapterBodyHighlightTimerRef: Ref<ReturnType<typeof setTimeout> | null>;
  batchDeviationInlineSummary: Ref<unknown>;
  visibleDeviations: ComputedRef<Array<Record<string, unknown>>>;
  overview: Ref<Record<string, unknown> | null>;
  setWorkspaceTab?: (tab: string) => void;
  jumpToChapter: (chapter: number) => Promise<void>;
  openVolumeSummaryForRange: (start: number, end: number) => void;
}

export interface WriteToolsReturn {
  formatBodySaveTime: (date: Date | null) => string;
  chapterRowClass: (chapter: number | Record<string, unknown>) => string;
  chapterVolumeLabel: (chapter: number | Record<string, unknown>) => string;
  chapterRowTitle: (chapter: number | Record<string, unknown>) => string;
  pulseChapterBodyHighlight: (issueIdx: number, source?: string) => void;
  focusIssueParagraph: (issue: Record<string, unknown>, issueIdx: number, source?: string) => void;
  batchDeviationsInRange: (start: number, end: number) => Array<Record<string, unknown>>;
  scrollToBatchDeviationList: (start: number, end: number) => Promise<void>;
  openFirstBatchDeviationChapter: (start: number, end: number) => Promise<void>;
  updateBatchDeviationInlineSummary: (start: number, end: number) => void;
  linkBatchDeviationInlineSummary: (start: number, end: number) => Promise<void>;
  dismissBatchDeviationInlineSummary: () => void;
  navigateIssueList: (
    event: KeyboardEvent,
    issues: Array<Record<string, unknown>>,
    currentIdx: number,
    onSelect: (issue: Record<string, unknown>, idx: number) => void,
    testIdPrefix: string,
  ) => void;
}

export function useWriteTools(deps: WriteToolsDeps): WriteToolsReturn {
  const {
    uiProfile,
    chapterBodyDraft,
    chapterBodyTextareaRef,
    chapterBodyHighlightActiveRef,
    chapterBodyHighlightTimerRef,
    batchDeviationInlineSummary,
    visibleDeviations,
    setWorkspaceTab,
    jumpToChapter,
    openVolumeSummaryForRange,
  } = deps;

  function formatBodySaveTime(date: Date | null): string {
    if (!date) return '尚未保存';
    try {
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  }

  function chapterRowClass(chapter: number | Record<string, unknown>): string {
    const classes: string[] = [];
    const deviations = visibleDeviations.value;
    const chapterNum = typeof chapter === 'number' ? chapter : Number(chapter.chapter);
    const isAlert: boolean = deviations.some((d: Record<string, unknown>) => Number(d.chapter) === chapterNum && d.severity === 'alert');
    const hasDeviation: boolean = deviations.some((d: Record<string, unknown>) => Number(d.chapter) === chapterNum);
    if (isAlert) return 'chapter-row--alert';
    if (hasDeviation) return 'chapter-row--deviation';
    const hasBody = typeof chapter === 'number' ? false : Boolean(chapter.has_body);
    if (hasBody) classes.push('chapter-row--has-body');
    else classes.push('chapter-row--missing');
    return classes.join(' ');
  }

  function chapterVolumeLabel(chapter: number | Record<string, unknown>): string {
    const chapterNum = typeof chapter === 'number' ? chapter : Number(chapter.chapter);
    const hit = visibleDeviations.value.find((d) => Number(d.chapter) === chapterNum);
    return String(hit?.volume_label || '');
  }

  function chapterRowTitle(chapter: number | Record<string, unknown>): string {
    const chapterNum = typeof chapter === 'number' ? chapter : Number(chapter.chapter);
    const hit = visibleDeviations.value.find((d) => Number(d.chapter) === chapterNum);
    if (hit) return String(hit.message || hit.deviation || '存在偏离');
    if (typeof chapter !== 'number' && chapter.has_body) return '已写';
    return '尚未开始';
  }

  function pulseChapterBodyHighlight(issueIdx: number, source: string = 'recheck'): void {
    chapterBodyHighlightActiveRef.value = true;
    if (chapterBodyHighlightTimerRef.value) clearTimeout(chapterBodyHighlightTimerRef.value);
    chapterBodyHighlightTimerRef.value = setTimeout(() => {
      chapterBodyHighlightActiveRef.value = false;
    }, 1500);
    void issueIdx;
    void source;
  }

  function focusIssueParagraph(issue: Record<string, unknown>, issueIdx: number, source: string = 'recheck'): void {
    const textarea = chapterBodyTextareaRef.value as (HTMLTextAreaElement & { setSelectionRange?: (s: number, e: number) => void; focus?: () => void; scrollTop?: number }) | null;
    if (!textarea || typeof textarea.setSelectionRange !== 'function') return;
    const paragraphs = chapterBodyDraft.value.split(/\n\s*\n/);
    const idx = Math.max(0, Number(issue.paragraph) - 1);
    const target = paragraphs[idx] ?? '';
    const offset = chapterBodyDraft.value.indexOf(target);
    if (offset >= 0) {
      try {
        textarea.setSelectionRange(offset, offset + target.length);
        textarea.focus?.();
        if (typeof textarea.scrollTop === 'number') textarea.scrollTop = Math.max(0, offset / 10);
      } catch { /* jsdom */ }
    }
    pulseChapterBodyHighlight(issueIdx, source);
  }

  function batchDeviationsInRange(start: number, end: number): Array<Record<string, unknown>> {
    return visibleDeviations.value.filter((d) => {
      const ch = Number(d.chapter);
      return Number.isFinite(ch) && ch >= start && ch <= end;
    });
  }

  async function scrollToBatchDeviationList(start: number, end: number): Promise<void> {
    const list = batchDeviationsInRange(start, end);
    if (!list.length) return;
    if (setWorkspaceTab) setWorkspaceTab('pulse');
    await jumpToChapter(Number(list[0].chapter));
  }

  async function openFirstBatchDeviationChapter(start: number, end: number): Promise<void> {
    const list = batchDeviationsInRange(start, end);
    if (!list.length) return;
    await jumpToChapter(Number(list[0].chapter));
  }

  function updateBatchDeviationInlineSummary(start: number, end: number): void {
    const list = batchDeviationsInRange(start, end);
    batchDeviationInlineSummary.value = {
      start,
      end,
      count: list.length,
      sample: list.slice(0, 3),
      computedAt: new Date().toISOString(),
    };
  }

  async function linkBatchDeviationInlineSummary(start: number, end: number): Promise<void> {
    openVolumeSummaryForRange(start, end);
    await scrollToBatchDeviationList(start, end);
  }

  function dismissBatchDeviationInlineSummary(): void {
    batchDeviationInlineSummary.value = null;
  }

  function navigateIssueList(
    event: KeyboardEvent,
    issues: Array<Record<string, unknown>>,
    currentIdx: number,
    onSelect: (issue: Record<string, unknown>, idx: number) => void,
    testIdPrefix: string,
  ): void {
    const key = event.key;
    if (key === 'ArrowDown') {
      event.preventDefault();
      const next = Math.min(currentIdx + 1, issues.length - 1);
      onSelect(issues[next], next);
    } else if (key === 'ArrowUp') {
      event.preventDefault();
      const next = Math.max(currentIdx - 1, 0);
      onSelect(issues[next], next);
    } else if (key === 'Home') {
      event.preventDefault();
      onSelect(issues[0], 0);
    } else if (key === 'End') {
      event.preventDefault();
      onSelect(issues[issues.length - 1], issues.length - 1);
    }
    void testIdPrefix;
  }

  return {
    formatBodySaveTime,
    chapterRowClass,
    chapterVolumeLabel,
    chapterRowTitle,
    pulseChapterBodyHighlight,
    focusIssueParagraph,
    batchDeviationsInRange,
    scrollToBatchDeviationList,
    openFirstBatchDeviationChapter,
    updateBatchDeviationInlineSummary,
    linkBatchDeviationInlineSummary,
    dismissBatchDeviationInlineSummary,
    navigateIssueList,
  };
}