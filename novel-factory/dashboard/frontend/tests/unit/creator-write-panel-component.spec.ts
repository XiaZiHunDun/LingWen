// tests/unit/creator-write-panel-component.spec.ts — CreatorWritePanel.vue 挂载

import { describe, test, expect, vi } from 'vitest';
import { ref, computed, reactive } from 'vue';
import { mount, flushPromises } from '@vue/test-utils';
import CreatorWritePanel from '../../src/components/creator/CreatorWritePanel.vue';
import { CREATOR_WRITE_KEY } from '../../src/components/creator/creatorWriteKey.js';
import { byTestid } from '../helpers/by-testid';

vi.mock('../../src/components/creator/CreatorWriteWorkbench.vue', () => ({
  default: {
    name: 'CreatorWriteWorkbench',
    template: '<div data-testid="stub-write-workbench"><slot name="chapters" /><slot /></div>',
  },
}));

vi.mock('../../src/components/creator/CreatorChapterList.vue', () => ({
  default: { template: '<div data-testid="stub-chapter-list" />' },
}));

type PanelOverrides = {
  workbenchEnabled?: boolean;
  humanFirstDesk?: boolean;
  showLogicCheck?: boolean;
  chapterPreview?: Record<string, unknown> | null;
  previewLoading?: boolean;
  batchSummary?: Record<string, unknown> | null;
  recheckResult?: Record<string, unknown> | null;
  uiProfile?: Record<string, unknown>;
};

function buildPanelContext(overrides: PanelOverrides = {}) {
  const chapterBodyDraft = ref('测试正文');
  const chapterOutlineDraft = ref('测试大纲');
  const selectedChapter = ref(1);
  const captureBodySelection = vi.fn();
  const saveChapterBody = vi.fn();
  const runCompanionLogicCheck = vi.fn();
  const handleLogicCheckIssueClick = vi.fn();
  const dismissBatchDeviationInlineSummary = vi.fn();
  const handleDeviationClick = vi.fn();

  const wb = {
    workbenchEnabled: overrides.workbenchEnabled ?? true,
    humanFirstDesk: overrides.humanFirstDesk ?? true,
    showInlineConflictGutter: true,
    inlineConflictMarkers: [{ id: 'm1', line: 1, label: '引号' }],
    activeInlineConflictId: null,
    focusInlineConflict: vi.fn(),
    captureBodySelection,
    chapterBodyConflictHighlightActive: false,
  };

  return reactive({
    isWorkspaceColumnVisible: (col: string) => col === 'write',
    wb,
    showCompanionLogicCheckInWrite: overrides.showLogicCheck ?? false,
    logicCheckRunning: false,
    logicCheckResult: overrides.showLogicCheck
      ? { passed: false, p0_count: 1, issues: [{ severity: 'P0', title: '时间线', chapter: 1 }] }
      : null,
    runCompanionLogicCheck,
    handleLogicCheckIssueClick,
    onLogicCheckIssueKeydown: vi.fn(),
    activeLogicCheckIssueIdx: null,
    uiProfile: {
      chapter_inline_edit: true,
      chapter_outline_inline_edit: true,
      logic_check_inline_issues: true,
      batch_deviation_inline_summary: true,
      batch_deviation_summary_link: true,
      batch_deviation_inline_dismiss: true,
      deviation_chapter_jump: true,
      chapter_recheck_inline: true,
      ...overrides.uiProfile,
    },
    batchDeviationInlineSummary: overrides.batchSummary ?? null,
    deviationHighlightEnabled: true,
    highlightedDeviationChapter: null,
    openVolumeSummaryForRange: vi.fn(),
    dismissBatchDeviationInlineSummary,
    handleDeviationClick,
    chapterPreview: overrides.chapterPreview ?? {
      chapter: 1,
      has_body: true,
      has_outline: true,
      word_count: 120,
      body_text: '测试正文',
      outline_text: '测试大纲',
    },
    previewLoading: overrides.previewLoading ?? false,
    chapterBodyDraft,
    chapterOutlineDraft,
    selectedChapter,
    chapterBodySaving: false,
    chapterOutlineSaving: false,
    bodySaveStatusLabel: '',
    bodyAutoSaveStatus: 'idle',
    saveChapterBody,
    bindChapterBodyTextareaRef: vi.fn(),
    chapterBodyHighlightActive: false,
    chapterRecheckResult: overrides.recheckResult ?? null,
    activeRecheckIssueIdx: null,
    focusIssueParagraph: vi.fn(),
    onRecheckIssueKeydown: vi.fn(),
  });
}

function mountPanel(overrides: PanelOverrides = {}) {
  const ctx = buildPanelContext(overrides);
  const wrapper = mount(CreatorWritePanel, {
    global: { provide: { [CREATOR_WRITE_KEY]: ctx } },
  });
  return { wrapper, ctx };
}

describe('CreatorWritePanel component', () => {
  test('renders workbench desk column when workbench enabled', () => {
    const { wrapper } = mountPanel();
    expect(wrapper.find(byTestid('column-write')).exists()).toBe(true);
    expect(wrapper.find(byTestid('column-write')).classes()).toContain('creator-column--write-desk');
    expect(wrapper.find(byTestid('stub-write-workbench')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-chapter-list')).exists()).toBe(true);
  });

  test('legacy layout shows chapter list without workbench shell', () => {
    const { wrapper } = mountPanel({ workbenchEnabled: false, humanFirstDesk: false });
    expect(wrapper.find(byTestid('column-write')).classes()).toContain('pixel-card');
    expect(wrapper.text()).toContain('写');
    expect(wrapper.find(byTestid('stub-chapter-list')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-write-workbench')).exists()).toBe(false);
  });

  test('shows companion logic check block outside human-first desk', () => {
    const { wrapper, ctx } = mountPanel({
      humanFirstDesk: false,
      workbenchEnabled: true,
      showLogicCheck: true,
    });
    expect(wrapper.find(byTestid('companion-logic-check-write')).exists()).toBe(true);
    expect(wrapper.find(byTestid('companion-logic-check-write-result')).text()).toContain('未通过');
    wrapper.find(byTestid('run-companion-logic-check-btn')).trigger('click');
    expect(ctx.runCompanionLogicCheck).toHaveBeenCalled();
  });

  test('inline edit shows body textarea and save footer', async () => {
    const { wrapper, ctx } = mountPanel();
    expect(wrapper.find(byTestid('chapter-preview-panel')).exists()).toBe(true);
    expect(wrapper.find(byTestid('chapter-inline-edit')).exists()).toBe(true);
    const textarea = wrapper.find(byTestid('chapter-body-textarea'));
    expect(textarea.exists()).toBe(true);
    await textarea.setValue('新正文段落');
    expect(ctx.chapterBodyDraft).toBe('新正文段落');
    await wrapper.find(byTestid('save-chapter-body-btn')).trigger('click');
    expect(ctx.saveChapterBody).toHaveBeenCalled();
  });

  test('body textarea interaction forwards selection to workbench', async () => {
    const { wrapper, ctx } = mountPanel();
    const textarea = wrapper.find(byTestid('chapter-body-textarea'));
    await textarea.trigger('select');
    expect(ctx.wb.captureBodySelection).toHaveBeenCalled();
  });

  test('batch deviation inline summary supports dismiss and jump', async () => {
    const { wrapper, ctx } = mountPanel({
      batchSummary: {
        start: 1,
        end: 3,
        items: [{ chapter: 2, severity: 'warn', message: '缺正文' }],
      },
    });
    expect(wrapper.find(byTestid('batch-deviation-inline-summary')).exists()).toBe(true);
    await wrapper.find(byTestid('batch-deviation-inline-ch2')).trigger('click');
    expect(ctx.handleDeviationClick).toHaveBeenCalled();
    await wrapper.find(byTestid('dismiss-batch-deviation-inline-btn')).trigger('click');
    expect(ctx.dismissBatchDeviationInlineSummary).toHaveBeenCalled();
  });

  test('shows chapter recheck panel after save for active chapter', () => {
    const { wrapper } = mountPanel({
      recheckResult: {
        chapter: 1,
        passed: true,
        p0_count: 0,
        issues: [],
      },
    });
    expect(wrapper.find(byTestid('chapter-recheck-inline-panel')).exists()).toBe(true);
    expect(wrapper.find(byTestid('chapter-recheck-inline-summary')).text()).toContain('通过');
  });

  test('logic check issue row triggers click handler', async () => {
    const { wrapper, ctx } = mountPanel({
      humanFirstDesk: false,
      showLogicCheck: true,
    });
    await wrapper.find(byTestid('logic-check-issue-0')).trigger('click');
    expect(ctx.handleLogicCheckIssueClick).toHaveBeenCalled();
  });
});
