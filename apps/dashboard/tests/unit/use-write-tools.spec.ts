/**
 * useWriteTools 子模块独立测试
 *
 * Phase 32: 为 Phase 19.5 useWriteTools 子模块添加专门测试。
 * 重点测试：format/label/class/highlight + batch inline summary。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref, computed } from 'vue';

import { useWriteTools } from '../../src/composables/useCreatorWrite/useWriteTools';

function mountTools(overrides: Record<string, unknown> = {}) {
  const uiProfile = computed(() => ({
    batch_deviation_inline_summary: true,
    recheck_issue_highlight: true,
    issue_paragraph_highlight_unified: true,
    ...overrides,
  }));
  const chapterBodyDraft = ref('第一段\n\n第二段\n\n第三段');
  const chapterBodyTextareaRef = ref<unknown>(null);
  const chapterBodyHighlightActiveRef = ref(false);
  const chapterBodyHighlightTimerRef = ref<ReturnType<typeof setTimeout> | null>(null);
  const batchDeviationInlineSummary = ref<unknown>(null);
  const visibleDeviations = ref<Array<Record<string, unknown>>>([]);
  const overview = ref<Record<string, unknown> | null>(null);
  const activeRecheckIssueIdxRef = ref<number | null>(null);
  const openVolumeSummaryForRange = vi.fn();
  const jumpToChapter = vi.fn(async () => {});

  const ctx = useWriteTools({
    uiProfile,
    chapterBodyDraft,
    chapterBodyTextareaRef,
    chapterBodyHighlightActiveRef,
    chapterBodyHighlightTimerRef,
    batchDeviationInlineSummary,
    visibleDeviations,
    overview,
    activeRecheckIssueIdxRef,
    setWorkspaceTab: vi.fn(),
    jumpToChapter,
    openVolumeSummaryForRange,
  });
  return {
    ...ctx, chapterBodyDraft, batchDeviationInlineSummary, visibleDeviations,
    overview, chapterBodyTextareaRef, openVolumeSummaryForRange,
  };
}

describe('useWriteTools', () => {
  beforeEach(() => vi.clearAllMocks());

  it('formatBodySaveTime returns 尚未保存 for null', () => {
    const ctx = mountTools();
    expect(ctx.formatBodySaveTime(null)).toBe('尚未保存');
  });

  it('formatBodySaveTime returns formatted time for valid Date', () => {
    const ctx = mountTools();
    const result = ctx.formatBodySaveTime(new Date('2026-06-01T12:34:00Z'));
    expect(result).toMatch(/\d{2}:\d{2}/);
  });

  it('chapterRowClass returns alert for alert severity deviation', () => {
    const ctx = mountTools();
    ctx.visibleDeviations.value = [{ chapter: 5, severity: 'alert' }];
    expect(ctx.chapterRowClass(5)).toBe('chapter-row--alert');
  });

  it('chapterRowClass returns warn for non-alert deviation', () => {
    const ctx = mountTools();
    ctx.visibleDeviations.value = [{ chapter: 5, severity: 'info' }];
    expect(ctx.chapterRowClass(5)).toBe('chapter-row--warn');
  });

  it('chapterRowClass returns done for has_body chapter', () => {
    const ctx = mountTools();
    ctx.overview.value = {
      chapters: [{ chapter: 3, has_body: true }],
    };
    expect(ctx.chapterRowClass(3)).toBe('chapter-row--done');
  });

  it('chapterRowClass returns empty for missing chapter', () => {
    const ctx = mountTools();
    ctx.overview.value = { chapters: [] };
    expect(ctx.chapterRowClass(99)).toBe('');
  });

  it('chapterRowClass accepts chapter object with number chapter', () => {
    const ctx = mountTools();
    expect(ctx.chapterRowClass({ chapter: 7, has_body: false })).toBe('');
  });

  it('chapterVolumeLabel finds matching deviation label', () => {
    const ctx = mountTools();
    ctx.visibleDeviations.value = [{ chapter: 5, volume_label: '第一卷' }];
    expect(ctx.chapterVolumeLabel(5)).toBe('第一卷');
  });

  it('chapterVolumeLabel returns empty for no match', () => {
    const ctx = mountTools();
    expect(ctx.chapterVolumeLabel(99)).toBe('');
  });

  it('chapterRowTitle returns deviation message', () => {
    const ctx = mountTools();
    ctx.visibleDeviations.value = [{ chapter: 5, message: '需要修' }];
    expect(ctx.chapterRowTitle(5)).toBe('需要修');
  });

  it('chapterRowTitle returns 字数 for has_body', () => {
    const ctx = mountTools();
    ctx.overview.value = {
      chapters: [{ chapter: 3, has_body: true, word_count: 1500 }],
    };
    expect(ctx.chapterRowTitle(3)).toBe('已写 1500 字');
  });

  it('chapterRowTitle returns 仅有大纲 for has_outline', () => {
    const ctx = mountTools();
    ctx.overview.value = {
      chapters: [{ chapter: 3, has_outline: true }],
    };
    expect(ctx.chapterRowTitle(3)).toBe('仅有大纲');
  });

  it('chapterRowTitle returns 尚未开始 for new chapter', () => {
    const ctx = mountTools();
    ctx.overview.value = { chapters: [] };
    expect(ctx.chapterRowTitle(3)).toBe('尚未开始');
  });

  it('focusIssueParagraph selects target paragraph in textarea', () => {
    const ctx = mountTools();
    const textarea = {
      setSelectionRange: vi.fn(),
      focus: vi.fn(),
      scrollTop: 0,
    };
    ctx.chapterBodyTextareaRef.value = textarea;
    ctx.focusIssueParagraph({ paragraph: 2 }, 0, 'recheck');
    expect(textarea.setSelectionRange).toHaveBeenCalled();
    expect(textarea.focus).toHaveBeenCalled();
  });

  it('focusIssueParagraph no-op when textarea missing setSelectionRange', () => {
    const ctx = mountTools();
    const textarea = { focus: vi.fn() }; // 缺少 setSelectionRange
    ctx.chapterBodyTextareaRef.value = textarea;
    expect(() => ctx.focusIssueParagraph({ paragraph: 1 }, 0, 'recheck')).not.toThrow();
  });

  it('batchDeviationsInRange filters visibleDeviations by chapter range', () => {
    const ctx = mountTools();
    ctx.visibleDeviations.value = [
      { chapter: 1 }, { chapter: 3 }, { chapter: 5 }, { chapter: 7 },
    ];
    const result = ctx.batchDeviationsInRange(2, 6);
    expect(result).toHaveLength(2);
    expect(result[0].chapter).toBe(3);
    expect(result[1].chapter).toBe(5);
  });

  it('updateBatchDeviationInlineSummary sets summary with items', () => {
    const ctx = mountTools();
    ctx.visibleDeviations.value = [
      { chapter: 1 }, { chapter: 3 }, { chapter: 5 },
    ];
    ctx.updateBatchDeviationInlineSummary(1, 5);
    const summary = ctx.batchDeviationInlineSummary.value as { start: number; end: number; items: unknown[] };
    expect(summary.items).toHaveLength(3);
  });

  it('updateBatchDeviationInlineSummary null when uiProfile disabled', () => {
    const ctx = mountTools({ batch_deviation_inline_summary: false });
    ctx.visibleDeviations.value = [{ chapter: 1 }];
    ctx.updateBatchDeviationInlineSummary(1, 3);
    expect(ctx.batchDeviationInlineSummary.value).toBeNull();
  });

  it('dismissBatchDeviationInlineSummary clears summary', () => {
    const ctx = mountTools();
    ctx.batchDeviationInlineSummary.value = { count: 1, items: [] };
    ctx.dismissBatchDeviationInlineSummary();
    expect(ctx.batchDeviationInlineSummary.value).toBeNull();
  });

  it('linkBatchDeviationInlineSummary opens volume summary', async () => {
    const ctx = mountTools();
    ctx.visibleDeviations.value = [{ chapter: 1 }];
    await ctx.linkBatchDeviationInlineSummary(1, 3);
    expect(ctx.openVolumeSummaryForRange).toHaveBeenCalledWith(1, 3);
  });
});