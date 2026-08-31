/**
 * useWriteFlow 子模块独立测试
 *
 * Phase 29: 为 Phase 19.5 useWriteFlow 子模块添加专门测试。
 * 重点测试：选章节 + 保存正文 + 自动保存 + 记忆同步（API 调用 + return shape）。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref, computed } from 'vue';
import type { CreatorChapterPreview } from '@lingwen/dashboard-contracts/shared';

// Mock API
const writeMocks = vi.hoisted(() => ({
  fetchCreatorChapterPreview: vi.fn(),
  saveCreatorChapterBody: vi.fn(),
  saveCreatorChapterOutline: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorChapterPreview: (...args: unknown[]) => writeMocks.fetchCreatorChapterPreview(...args),
  saveCreatorChapterBody: (...args: unknown[]) => writeMocks.saveCreatorChapterBody(...args),
  saveCreatorChapterOutline: (...args: unknown[]) => writeMocks.saveCreatorChapterOutline(...args),
}));

// v16.2.7 T6a: also mock the typed wrapper module so useWriteFlow (which now
// imports from @/api/content) resolves the same mocks. Per v16.2.5 §5.1 lesson 3.
vi.mock('../../src/api/content', () => ({
  fetchCreatorChapterPreview: (...args: unknown[]) => writeMocks.fetchCreatorChapterPreview(...args),
  saveCreatorChapterBody: (...args: unknown[]) => writeMocks.saveCreatorChapterBody(...args),
  saveCreatorChapterOutline: (...args: unknown[]) => writeMocks.saveCreatorChapterOutline(...args),
}));

vi.mock('../../src/utils/writeResumeStorage.js', () => ({
  saveWriteResume: vi.fn(),
}));
vi.mock('../../src/utils/creatorChapterEntityUtils.js', () => ({
  extractMentionedEntityNames: vi.fn(() => []),
}));

import { useWriteFlow } from '../../src/composables/useCreatorWrite/useWriteFlow';

describe('useWriteFlow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // N.13 T2.P1.c: mocks now use canonical CreatorChapterPreview field names
    // (body/outline). Legacy body_text/outline_text fields were never in the
    // backend response and were silently ``undefined`` — see useWriteFlow.ts
    // selectChapter JSDoc.
    writeMocks.fetchCreatorChapterPreview.mockResolvedValue({
      chapter_id: 1,
      project_slug: 'test',
      body: 'ch1 body',
      outline: 'ch1 outline',
    });
    writeMocks.saveCreatorChapterBody.mockResolvedValue({
      chapter_id: 1,
      project_slug: 'test',
      body: 'new body',
      outline: 'new outline',
    });
    writeMocks.saveCreatorChapterOutline.mockResolvedValue({
      chapter_id: 1,
      project_slug: 'test',
      body: 'b',
      outline: 'o',
    });
  });

  it('initial state has empty visibleChapters', () => {
    const uiProfile = computed(() => ({}));
    const overview = ref<Record<string, unknown> | null>(null);
    const error = ref<string | null>(null);
    const saveMessage = ref('');
    const handleSaveError = vi.fn();
    const onAfterChapterSave = vi.fn(async () => {});
    const flow = useWriteFlow({
      uiProfile, overview, error, saveMessage, handleSaveError, onAfterChapterSave,
      selectedChapter: ref<number | null>(null),
      chapterPreview: ref<CreatorChapterPreview | null>(null),
      chapterBodyDraft: ref(''),
      chapterOutlineDraft: ref(''),
      chapterBodySaving: ref(false),
      chapterOutlineSaving: ref(false),
      chapterBodyTextareaRef: ref<unknown>(null),
      bodyLastSavedAt: ref<Date | null>(null),
      bodyAutoSaveStatus: ref('idle'),
      chapterRecheckResult: ref<Record<string, unknown> | null>(null),
      previewLoading: ref(false),
      memoryAssetsCache: ref<Array<Record<string, unknown>>>([]),
      lastPersistedBodyRef: ref(''),
    });
    expect(flow.visibleChapters.value).toEqual([]);
    expect(flow.deviationChapters.value.size).toBe(0);
    expect(flow.alertChapters.value.size).toBe(0);
    expect(flow.showCompanionLogicCheckInWrite.value).toBe(false);
  });

  it('visibleChapters filters chapters by chapter <= 15', () => {
    const overview = ref<Record<string, unknown> | null>({
      chapters: [
        { chapter: 10, has_body: false },
        { chapter: 20, has_body: false },
      ],
    });
    const flow = useWriteFlow({
      uiProfile: computed(() => ({})), overview,
      error: ref<string | null>(null), saveMessage: ref(''), handleSaveError: vi.fn(),
      onAfterChapterSave: vi.fn(async () => {}),
      selectedChapter: ref<number | null>(null),
      chapterPreview: ref<CreatorChapterPreview | null>(null),
      chapterBodyDraft: ref(''), chapterOutlineDraft: ref(''),
      chapterBodySaving: ref(false), chapterOutlineSaving: ref(false),
      chapterBodyTextareaRef: ref<unknown>(null),
      bodyLastSavedAt: ref<Date | null>(null), bodyAutoSaveStatus: ref('idle'),
      chapterRecheckResult: ref<Record<string, unknown> | null>(null),
      previewLoading: ref(false),
      memoryAssetsCache: ref<Array<Record<string, unknown>>>([]),
      lastPersistedBodyRef: ref(''),
    });
    expect(flow.visibleChapters.value).toHaveLength(1);
    expect(flow.visibleChapters.value[0].chapter).toBe(10);
  });

  it('deviationChapters extracts chapters from overview deviations', () => {
    const overview = ref<Record<string, unknown> | null>({
      deviations: [
        { chapter: 5, severity: 'info' },
        { chapter: 8, severity: 'alert' },
      ],
    });
    const flow = useWriteFlow({
      uiProfile: computed(() => ({})), overview,
      error: ref<string | null>(null), saveMessage: ref(''), handleSaveError: vi.fn(),
      onAfterChapterSave: vi.fn(async () => {}),
      selectedChapter: ref<number | null>(null),
      chapterPreview: ref<CreatorChapterPreview | null>(null),
      chapterBodyDraft: ref(''), chapterOutlineDraft: ref(''),
      chapterBodySaving: ref(false), chapterOutlineSaving: ref(false),
      chapterBodyTextareaRef: ref<unknown>(null),
      bodyLastSavedAt: ref<Date | null>(null), bodyAutoSaveStatus: ref('idle'),
      chapterRecheckResult: ref<Record<string, unknown> | null>(null),
      previewLoading: ref(false),
      memoryAssetsCache: ref<Array<Record<string, unknown>>>([]),
      lastPersistedBodyRef: ref(''),
    });
    expect(flow.deviationChapters.value.has(5)).toBe(true);
    expect(flow.deviationChapters.value.has(8)).toBe(true);
  });

  it('alertChapters filters by severity alert', () => {
    const overview = ref<Record<string, unknown> | null>({
      deviations: [
        { chapter: 5, severity: 'info' },
        { chapter: 8, severity: 'alert' },
      ],
    });
    const flow = useWriteFlow({
      uiProfile: computed(() => ({})), overview,
      error: ref<string | null>(null), saveMessage: ref(''), handleSaveError: vi.fn(),
      onAfterChapterSave: vi.fn(async () => {}),
      selectedChapter: ref<number | null>(null),
      chapterPreview: ref<CreatorChapterPreview | null>(null),
      chapterBodyDraft: ref(''), chapterOutlineDraft: ref(''),
      chapterBodySaving: ref(false), chapterOutlineSaving: ref(false),
      chapterBodyTextareaRef: ref<unknown>(null),
      bodyLastSavedAt: ref<Date | null>(null), bodyAutoSaveStatus: ref('idle'),
      chapterRecheckResult: ref<Record<string, unknown> | null>(null),
      previewLoading: ref(false),
      memoryAssetsCache: ref<Array<Record<string, unknown>>>([]),
      lastPersistedBodyRef: ref(''),
    });
    expect(flow.alertChapters.value.has(5)).toBe(false);
    expect(flow.alertChapters.value.has(8)).toBe(true);
  });

  it('selectChapter loads preview and resets autosave', async () => {
    const selectedChapter = ref<number | null>(null);
    const chapterBodyDraft = ref('');
    const bodyAutoSaveStatus = ref('idle');
    const previewLoading = ref(false);
    const flow = useWriteFlow({
      uiProfile: computed(() => ({})), overview: ref<Record<string, unknown> | null>(null),
      error: ref<string | null>(null), saveMessage: ref(''), handleSaveError: vi.fn(),
      onAfterChapterSave: vi.fn(async () => {}),
      selectedChapter, chapterPreview: ref<CreatorChapterPreview | null>(null),
      chapterBodyDraft, chapterOutlineDraft: ref(''),
      chapterBodySaving: ref(false), chapterOutlineSaving: ref(false),
      chapterBodyTextareaRef: ref<unknown>(null),
      bodyLastSavedAt: ref<Date | null>(null),
      bodyAutoSaveStatus: bodyAutoSaveStatus,
      chapterRecheckResult: ref<Record<string, unknown> | null>(null),
      previewLoading,
      memoryAssetsCache: ref<Array<Record<string, unknown>>>([]),
      lastPersistedBodyRef: ref(''),
    });
    await flow.selectChapter(1);
    expect(selectedChapter.value).toBe(1);
    expect(chapterBodyDraft.value).toBe('ch1 body');
    expect(bodyAutoSaveStatus.value).toBe('idle');
    expect(previewLoading.value).toBe(false);
  });

  it('jumpToChapter delegates to selectChapter', async () => {
    const selectedChapter = ref<number | null>(null);
    const flow = useWriteFlow({
      uiProfile: computed(() => ({})), overview: ref<Record<string, unknown> | null>(null),
      error: ref<string | null>(null), saveMessage: ref(''), handleSaveError: vi.fn(),
      onAfterChapterSave: vi.fn(async () => {}),
      selectedChapter, chapterPreview: ref<CreatorChapterPreview | null>(null),
      chapterBodyDraft: ref(''), chapterOutlineDraft: ref(''),
      chapterBodySaving: ref(false), chapterOutlineSaving: ref(false),
      chapterBodyTextareaRef: ref<unknown>(null),
      bodyLastSavedAt: ref<Date | null>(null), bodyAutoSaveStatus: ref('idle'),
      chapterRecheckResult: ref<Record<string, unknown> | null>(null),
      previewLoading: ref(false),
      memoryAssetsCache: ref<Array<Record<string, unknown>>>([]),
      lastPersistedBodyRef: ref(''),
    });
    await flow.jumpToChapter(3);
    expect(selectedChapter.value).toBe(3);
  });

  it('saveChapterBody posts and shows chXXX message', async () => {
    const selectedChapter = ref<number | null>(1);
    const saveMessage = ref('');
    const flow = useWriteFlow({
      uiProfile: computed(() => ({})), overview: ref<Record<string, unknown> | null>(null),
      error: ref<string | null>(null), saveMessage, handleSaveError: vi.fn(),
      onAfterChapterSave: vi.fn(async () => {}),
      selectedChapter, chapterPreview: ref<CreatorChapterPreview | null>(null),
      chapterBodyDraft: ref('test'), chapterOutlineDraft: ref(''),
      chapterBodySaving: ref(false), chapterOutlineSaving: ref(false),
      chapterBodyTextareaRef: ref<unknown>(null),
      bodyLastSavedAt: ref<Date | null>(null), bodyAutoSaveStatus: ref('idle'),
      chapterRecheckResult: ref<Record<string, unknown> | null>(null),
      previewLoading: ref(false),
      memoryAssetsCache: ref<Array<Record<string, unknown>>>([]),
      lastPersistedBodyRef: ref(''),
    });
    await flow.saveChapterBody();
    expect(writeMocks.saveCreatorChapterBody).toHaveBeenCalled();
    expect(saveMessage.value).toContain('ch001');
    expect(saveMessage.value).toContain('正文已保存');
  });

  it('saveChapterOutline posts outline', async () => {
    const selectedChapter = ref<number | null>(5);
    const saveMessage = ref('');
    const flow = useWriteFlow({
      uiProfile: computed(() => ({})), overview: ref<Record<string, unknown> | null>(null),
      error: ref<string | null>(null), saveMessage, handleSaveError: vi.fn(),
      onAfterChapterSave: vi.fn(async () => {}),
      selectedChapter, chapterPreview: ref<CreatorChapterPreview | null>(null),
      chapterBodyDraft: ref(''), chapterOutlineDraft: ref('test-outline'),
      chapterBodySaving: ref(false), chapterOutlineSaving: ref(false),
      chapterBodyTextareaRef: ref<unknown>(null),
      bodyLastSavedAt: ref<Date | null>(null), bodyAutoSaveStatus: ref('idle'),
      chapterRecheckResult: ref<Record<string, unknown> | null>(null),
      previewLoading: ref(false),
      memoryAssetsCache: ref<Array<Record<string, unknown>>>([]),
      lastPersistedBodyRef: ref(''),
    });
    await flow.saveChapterOutline();
    expect(writeMocks.saveCreatorChapterOutline).toHaveBeenCalled();
    expect(saveMessage.value).toContain('大纲已保存');
  });

  it('autoSaveChapterBody no-op when draft unchanged', async () => {
    const selectedChapter = ref<number | null>(1);
    const chapterBodyDraft = ref('unchanged');
    const lastPersistedBody = ref('unchanged');
    const flow = useWriteFlow({
      uiProfile: computed(() => ({})), overview: ref<Record<string, unknown> | null>(null),
      error: ref<string | null>(null), saveMessage: ref(''), handleSaveError: vi.fn(),
      onAfterChapterSave: vi.fn(async () => {}),
      selectedChapter, chapterPreview: ref<CreatorChapterPreview | null>(null),
      chapterBodyDraft, chapterOutlineDraft: ref(''),
      chapterBodySaving: ref(false), chapterOutlineSaving: ref(false),
      chapterBodyTextareaRef: ref<unknown>(null),
      bodyLastSavedAt: ref<Date | null>(null), bodyAutoSaveStatus: ref('idle'),
      chapterRecheckResult: ref<Record<string, unknown> | null>(null),
      previewLoading: ref(false),
      memoryAssetsCache: ref<Array<Record<string, unknown>>>([]),
      lastPersistedBodyRef: lastPersistedBody,
    });
    await flow.autoSaveChapterBody();
    expect(writeMocks.saveCreatorChapterBody).not.toHaveBeenCalled();
  });

  it('bindChapterBodyTextareaRef sets ref', () => {
    const chapterBodyTextareaRef = ref<unknown>(null);
    const flow = useWriteFlow({
      uiProfile: computed(() => ({})), overview: ref<Record<string, unknown> | null>(null),
      error: ref<string | null>(null), saveMessage: ref(''), handleSaveError: vi.fn(),
      onAfterChapterSave: vi.fn(async () => {}),
      selectedChapter: ref<number | null>(null),
      chapterPreview: ref<CreatorChapterPreview | null>(null),
      chapterBodyDraft: ref(''), chapterOutlineDraft: ref(''),
      chapterBodySaving: ref(false), chapterOutlineSaving: ref(false),
      chapterBodyTextareaRef,
      bodyLastSavedAt: ref<Date | null>(null), bodyAutoSaveStatus: ref('idle'),
      chapterRecheckResult: ref<Record<string, unknown> | null>(null),
      previewLoading: ref(false),
      memoryAssetsCache: ref<Array<Record<string, unknown>>>([]),
      lastPersistedBodyRef: ref(''),
    });
    const fakeTextarea = { setSelectionRange: vi.fn(), focus: vi.fn() };
    flow.bindChapterBodyTextareaRef(fakeTextarea);
    expect(chapterBodyTextareaRef.value).toEqual(fakeTextarea);
  });

  it('maybeAutoSelectWritingChapter respects focusChapter deep link', () => {
    const selectedChapter = ref<number | null>(null);
    const focusChapter = ref<number | null>(5);
    const overview = ref<Record<string, unknown> | null>({
      creation_mode: 'companion',
      chapters: [{ chapter: 5, has_body: false }, { chapter: 1, has_body: false }],
    });
    const flow = useWriteFlow({
      uiProfile: computed(() => ({})), overview,
      error: ref<string | null>(null), saveMessage: ref(''), handleSaveError: vi.fn(),
      onAfterChapterSave: vi.fn(async () => {}),
      selectedChapter, chapterPreview: ref<CreatorChapterPreview | null>(null),
      chapterBodyDraft: ref(''), chapterOutlineDraft: ref(''),
      chapterBodySaving: ref(false), chapterOutlineSaving: ref(false),
      chapterBodyTextareaRef: ref<unknown>(null),
      bodyLastSavedAt: ref<Date | null>(null), bodyAutoSaveStatus: ref('idle'),
      chapterRecheckResult: ref<Record<string, unknown> | null>(null),
      previewLoading: ref(false),
      memoryAssetsCache: ref<Array<Record<string, unknown>>>([]),
      lastPersistedBodyRef: ref(''),
      focusChapter,
    });
    flow.maybeAutoSelectWritingChapter();
    expect(selectedChapter.value).toBe(5);
  });
});
