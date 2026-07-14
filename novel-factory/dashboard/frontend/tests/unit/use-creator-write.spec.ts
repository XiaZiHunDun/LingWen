// tests/unit/use-creator-write.spec.ts — useCreatorWrite 章节写栏编排

import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { computed, defineComponent, ref } from 'vue';
import { flushPromises, mount } from '@vue/test-utils';

const writeMocks = vi.hoisted(() => ({
  fetchCreatorChapterPreview: vi.fn(),
  saveCreatorChapterBody: vi.fn(),
  saveCreatorChapterOutline: vi.fn(),
  runCreatorLogicCheck: vi.fn(),
  saveWriteResume: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorChapterPreview: (...args: unknown[]) => writeMocks.fetchCreatorChapterPreview(...args),
  saveCreatorChapterBody: (...args: unknown[]) => writeMocks.saveCreatorChapterBody(...args),
  saveCreatorChapterOutline: (...args: unknown[]) => writeMocks.saveCreatorChapterOutline(...args),
  runCreatorLogicCheck: (...args: unknown[]) => writeMocks.runCreatorLogicCheck(...args),
}));

vi.mock('../../src/utils/writeResumeStorage.js', () => ({
  saveWriteResume: (...args: unknown[]) => writeMocks.saveWriteResume(...args),
}));

import { useCreatorWrite } from '../../src/composables/useCreatorWrite.js';

type WriteApi = ReturnType<typeof useCreatorWrite>;

function mountWrite(overrides: Record<string, unknown> = {}) {
  const uiProfile = computed(() => ({
    chapter_inline_edit: true,
    chapter_full_preview: true,
    chapter_outline_inline_edit: true,
    chapter_recheck_inline: true,
    chapter_save_p0_recheck: false,
    recheck_issue_paragraph_jump: true,
    recheck_issue_highlight: true,
    deviation_chapter_jump: true,
    batch_deviation_inline_summary: true,
    batch_scroll_deviation_list: false,
    batch_open_first_deviation: false,
    batch_deviation_summary_link: false,
    issue_keyboard_navigation: true,
    logic_check_issue_highlight: true,
    primary_action: 'logic_check',
    creator_write_workbench: true,
    ...(overrides.uiProfile as object | undefined),
  }));

  const overview = ref({
    slug: 'test-book',
    name: '测试书',
    creation_mode: 'companion',
    chapters: [
      { chapter: 1, has_body: true, has_outline: true, word_count: 120 },
      { chapter: 2, has_body: false, has_outline: true, word_count: 0 },
      { chapter: 16, has_body: false, has_outline: false, word_count: 0 },
    ],
    deviations: [
      { chapter: 1, severity: 'alert', message: '缺卷摘要', volume_label: '卷一' },
      { chapter: 2, severity: 'warn', message: '仅大纲' },
    ],
    ...(overrides.overview as object | undefined),
  });

  const error = ref<string | null>(null);
  const saveMessage = ref('');
  const logicCheckRunning = ref(false);
  const logicCheckResult = ref<{ passed: boolean; p0_count: number; issues: object[] } | null>(null);
  const highlightedDeviationChapter = ref<number | null>(null);
  const focusChapter = ref<number | null>(
    (overrides.focusChapter as number | null | undefined) ?? null,
  );

  const deps = {
    uiProfile,
    overview,
    error,
    saveMessage,
    handleSaveError: (err: unknown) => {
      error.value = err instanceof Error ? err.message : String(err);
    },
    onAfterChapterSave: vi.fn(async () => undefined),
    isWorkspaceColumnVisible: () => true,
    workspaceTabsEnabled: computed(() => overrides.workspaceTabsEnabled !== false),
    visibleDeviations: computed(() => overview.value?.deviations || []),
    deviationHighlightEnabled: computed(() => true),
    highlightedDeviationChapter,
    logicCheckRunning,
    logicCheckResult,
    runCompanionLogicCheck: vi.fn(async () => undefined),
    openVolumeSummaryForRange: vi.fn(),
    focusChapter,
  };

  let api!: WriteApi;
  const Comp = defineComponent({
    setup() {
      api = useCreatorWrite(deps);
      return () => null;
    },
  });

  const wrapper = mount(Comp);

  return {
    wrapper,
    api,
    deps,
    overview,
    error,
    saveMessage,
    logicCheckResult,
    logicCheckRunning,
    highlightedDeviationChapter,
    focusChapter,
  };
}

describe('useCreatorWrite', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    writeMocks.fetchCreatorChapterPreview.mockResolvedValue({
      body_text: '第一段\n\n第二段',
      outline_text: '大纲 A',
    });
    writeMocks.saveCreatorChapterBody.mockImplementation(async (_ch: number, body: string) => ({
      body_text: body,
      outline_text: '大纲 A',
    }));
    writeMocks.saveCreatorChapterOutline.mockImplementation(async (_ch: number, outline: string) => ({
      body_text: '第一段\n\n第二段',
      outline_text: outline,
    }));
    writeMocks.runCreatorLogicCheck.mockResolvedValue({
      passed: false,
      p0_count: 1,
      issues: [{ severity: 'P0', title: '时间线', paragraph: 2 }],
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  test('chapterRowClass and chapterRowTitle reflect deviation and body state', () => {
    const { api } = mountWrite();
    const ctx = api.panelContext;
    expect(ctx.chapterRowClass(1)).toBe('chapter-row--alert');
    expect(ctx.chapterRowClass(2)).toBe('chapter-row--warn');
    expect(ctx.chapterRowClass(999)).toBe('');
    expect(ctx.chapterVolumeLabel(1)).toBe('卷一');
    expect(ctx.chapterRowTitle(1)).toContain('缺卷摘要');
    expect(ctx.chapterRowTitle(2)).toBe('仅大纲');
  });

  test('visibleChapters caps companion list at chapter 15', () => {
    const { api } = mountWrite();
    expect(api.panelContext.visibleChapters.value.map((ch: any) => ch.chapter)).toEqual([1, 2]);
  });

  test('maybeAutoSelectWritingChapter picks first chapter without body', async () => {
    const { api } = mountWrite();
    api.maybeAutoSelectWritingChapter();
    await flushPromises();
    expect(writeMocks.fetchCreatorChapterPreview).toHaveBeenCalledWith(2, { full: true });
    expect(api.selectedChapter.value).toBe(2);
  });

  test('maybeAutoSelectWritingChapter honors focusChapter deep link', async () => {
    const { api } = mountWrite({ focusChapter: 1 });
    api.maybeAutoSelectWritingChapter();
    await flushPromises();
    expect(writeMocks.fetchCreatorChapterPreview).toHaveBeenCalledWith(1, { full: true });
    expect(api.selectedChapter.value).toBe(1);
  });

  test('selectChapter loads preview drafts and resets autosave state', async () => {
    const { api } = mountWrite();
    await api.panelContext.selectChapter(1);
    await flushPromises();
    expect(api.panelContext.chapterBodyDraft.value).toBe('第一段\n\n第二段');
    expect(api.panelContext.chapterOutlineDraft.value).toBe('大纲 A');
    expect(api.panelContext.bodyAutoSaveStatus.value).toBe('idle');
    expect(writeMocks.saveWriteResume).toHaveBeenCalledWith('test-book', {
      chapter: 1,
      projectName: '测试书',
    });
  });

  test('saveChapterBody persists body and shows save message', async () => {
    const { api, saveMessage } = mountWrite();
    await api.panelContext.selectChapter(1);
    await flushPromises();
    api.panelContext.chapterBodyDraft.value = '保存后的正文';
    await api.panelContext.saveChapterBody();
    expect(writeMocks.saveCreatorChapterBody).toHaveBeenCalledWith(1, '保存后的正文');
    expect(saveMessage.value).toContain('ch001 正文已保存');
  });

  test('autoSaveChapterBody runs after draft debounce', async () => {
    vi.useFakeTimers();
    const { api } = mountWrite();
    await api.panelContext.selectChapter(1);
    await flushPromises();
    api.panelContext.chapterBodyDraft.value = '自动保存草稿';
    await vi.advanceTimersByTimeAsync(2100);
    await flushPromises();
    expect(writeMocks.saveCreatorChapterBody).toHaveBeenCalledWith(1, '自动保存草稿');
    expect(api.panelContext.bodyAutoSaveStatus.value).toBe('saved');
  });

  test('saveChapterBody triggers P0 recheck when chapter_save_p0_recheck enabled', async () => {
    const { api, saveMessage } = mountWrite({
      uiProfile: { chapter_save_p0_recheck: true },
    });
    await api.panelContext.selectChapter(1);
    await flushPromises();
    await api.panelContext.saveChapterBody();
    expect(writeMocks.runCreatorLogicCheck).toHaveBeenCalledWith({ chapter: 1 });
    expect((api.panelContext.chapterRecheckResult.value as any)?.chapter).toBe(1);
    expect(saveMessage.value).toContain('P0');
  });

  test('batch deviation inline summary can be built and dismissed', () => {
    const { api } = mountWrite();
    api.updateBatchDeviationInlineSummary(1, 3);
    expect((api.panelContext.batchDeviationInlineSummary.value as any)?.items).toHaveLength(2);
    api.dismissBatchDeviationInlineSummary();
    expect(api.panelContext.batchDeviationInlineSummary.value).toBeNull();
  });

  test('focusIssueParagraph selects target paragraph in textarea', async () => {
    const { api } = mountWrite();
    await api.panelContext.selectChapter(1);
    await flushPromises();
    const textarea = {
      focus: vi.fn(),
      setSelectionRange: vi.fn(),
      scrollHeight: 200,
      scrollTop: 0,
    };
    api.panelContext.bindChapterBodyTextareaRef(textarea);
    api.focusIssueParagraph({ paragraph: 2 }, 0, 'recheck');
    expect(textarea.setSelectionRange).toHaveBeenCalled();
    expect(api.panelContext.activeRecheckIssueIdx.value).toBe(0);
  });

  test('syncMemoryAssets enables entity mention detection on save', async () => {
    writeMocks.fetchCreatorChapterPreview.mockResolvedValue({
      body_text: '林默在雨里写下第一段。',
      outline_text: '大纲 A',
    });
    const { api, saveMessage } = mountWrite();
    await api.panelContext.selectChapter(1);
    await flushPromises();
    api.syncMemoryAssets([{ name: '林默', kind: 'character' }]);
    await api.panelContext.saveChapterBody();
    expect(saveMessage.value).toContain('林默');
  });
});
