/**
 * useWriteFlow — 写作流（选章节/保存/自动保存/记忆同步）
 *
 * Phase 19 Task 5：从 useCreatorWrite.js 拆出（完整实现）。
 * 负责: selectChapter/jumpToChapter + saveChapterBody/saveChapterOutline +
 *       autoSaveChapterBody + syncMemoryAssets + bindChapterBodyTextareaRef +
 *       maybeAutoSelectWritingChapter + visibleChapters/deviationChapters/alertChapters computed +
 *       showCompanionLogicCheckInWrite computed。
 *
 * 注: 接收 main hook 的 ref 通过 deps，保持状态由 main hook 拥有。
 */
import { computed, nextTick, onUnmounted } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import {
  fetchCreatorChapterPreview,
  saveCreatorChapterBody,
  saveCreatorChapterOutline,
} from '../../api/index.js';

export interface ChapterRow {
  chapter: number;
  has_body?: boolean;
}

export interface Deviation {
  chapter?: number;
  severity?: string;
  volume_label?: string;
}

export interface WriteFlowDeps {
  uiProfile: ComputedRef<Record<string, unknown>>;
  overview: Ref<Record<string, unknown> | null>;
  error: Ref<string | null>;
  saveMessage: Ref<string>;
  handleSaveError: (err: unknown) => void;
  onAfterChapterSave: () => Promise<void>;
  selectedChapter: Ref<number | null>;
  chapterPreview: Ref<Record<string, unknown> | null>;
  chapterBodyDraft: Ref<string>;
  chapterOutlineDraft: Ref<string>;
  chapterBodySaving: Ref<boolean>;
  chapterOutlineSaving: Ref<boolean>;
  chapterBodyTextareaRef: Ref<unknown>;
  bodyLastSavedAt: Ref<Date | null>;
  bodyAutoSaveStatus: Ref<string>;
  chapterRecheckResult: Ref<Record<string, unknown> | null>;
  previewLoading: Ref<boolean>;
  focusChapter?: Ref<number | null>;
}

export interface WriteFlowReturn {
  deviationChapters: ComputedRef<Set<number>>;
  alertChapters: ComputedRef<Set<number>>;
  visibleChapters: ComputedRef<ChapterRow[]>;
  showCompanionLogicCheckInWrite: ComputedRef<boolean>;
  syncMemoryAssets: (items: Array<Record<string, unknown>>) => void;
  selectChapter: (chapter: number) => Promise<void>;
  jumpToChapter: (chapter: number) => Promise<void>;
  saveChapterBody: () => Promise<void>;
  saveChapterOutline: () => Promise<void>;
  autoSaveChapterBody: () => Promise<void>;
  bindChapterBodyTextareaRef: (el: unknown) => void;
  maybeAutoSelectWritingChapter: () => void;
}

export function useWriteFlow(deps: WriteFlowDeps): WriteFlowReturn {
  const {
    uiProfile,
    overview,
    error,
    saveMessage,
    handleSaveError,
    onAfterChapterSave,
    selectedChapter,
    chapterPreview,
    chapterBodyDraft,
    chapterOutlineDraft,
    chapterBodySaving,
    chapterOutlineSaving,
    chapterBodyTextareaRef,
    bodyLastSavedAt,
    bodyAutoSaveStatus,
    chapterRecheckResult,
    previewLoading,
    focusChapter,
  } = deps;

  let lastPersistedBody = '';
  let autoSaveTimer: ReturnType<typeof setTimeout> | null = null;

  const memoryAssetsCache = (() => {
    const r = { value: [] as Array<Record<string, unknown>> };
    return r;
  })();

  function syncMemoryAssets(items: Array<Record<string, unknown>>): void {
    memoryAssetsCache.value = Array.isArray(items) ? items : [];
  }

  const deviationChapters = computed<Set<number>>(() => {
    const set = new Set<number>();
    const deviations = (overview.value as { deviations?: Deviation[] } | null)?.deviations || [];
    for (const d of deviations) {
      if (d.chapter) set.add(d.chapter);
    }
    return set;
  });

  const alertChapters = computed<Set<number>>(() => {
    const set = new Set<number>();
    const deviations = (overview.value as { deviations?: Deviation[] } | null)?.deviations || [];
    for (const d of deviations) {
      if (d.severity === 'alert' && d.chapter) set.add(d.chapter);
    }
    return set;
  });

  const visibleChapters = computed<ChapterRow[]>(() =>
    ((overview.value as { chapters?: ChapterRow[] } | null)?.chapters || []).filter((ch) => ch.chapter <= 15),
  );

  const showCompanionLogicCheckInWrite = computed<boolean>(
    () => (uiProfile.value as { primary_action?: string }).primary_action === 'logic_check',
  );

  async function selectChapter(chapter: number): Promise<void> {
    selectedChapter.value = chapter;
    previewLoading.value = true;
    try {
      const preview = await fetchCreatorChapterPreview(chapter, { full: true }) as Record<string, unknown>;
      chapterPreview.value = preview;
      chapterBodyDraft.value = String(preview.body_draft || preview.body_text || '');
      chapterOutlineDraft.value = String(preview.outline_text || '');
      lastPersistedBody = chapterBodyDraft.value;
      bodyLastSavedAt.value = preview.saved_at ? new Date(String(preview.saved_at)) : null;
      bodyAutoSaveStatus.value = 'idle';
      chapterRecheckResult.value = null;
      await nextTick();
      const textarea = chapterBodyTextareaRef.value as (HTMLElement & { focus?: () => void }) | null;
      try { textarea?.focus?.(); } catch { /* jsdom */ }
    } catch (e) {
      handleSaveError(e);
    } finally {
      previewLoading.value = false;
    }
  }

  async function jumpToChapter(chapter: number): Promise<void> {
    await selectChapter(chapter);
  }

  async function saveChapterBody(): Promise<void> {
    if (selectedChapter.value == null) return;
    chapterBodySaving.value = true;
    try {
      await saveCreatorChapterBody({
        chapter: selectedChapter.value,
        body: chapterBodyDraft.value,
      });
      lastPersistedBody = chapterBodyDraft.value;
      bodyLastSavedAt.value = new Date();
      bodyAutoSaveStatus.value = 'saved';
      saveMessage.value = '章节正文已保存';
      // 调用 saveWriteResume（与原实现一致）
      try {
        const { saveWriteResume } = await import('../../utils/writeResumeStorage.js');
        saveWriteResume(String(selectedChapter.value), chapterBodyDraft.value);
      } catch { /* ignore */ }
      await onAfterChapterSave();
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
      bodyAutoSaveStatus.value = 'idle';
    } finally {
      chapterBodySaving.value = false;
    }
  }

  async function saveChapterOutline(): Promise<void> {
    if (selectedChapter.value == null) return;
    chapterOutlineSaving.value = true;
    try {
      await saveCreatorChapterOutline({
        chapter: selectedChapter.value,
        outline: chapterOutlineDraft.value,
      });
      saveMessage.value = '章节大纲已保存';
      await onAfterChapterSave();
    } catch (e) {
      handleSaveError(e);
    } finally {
      chapterOutlineSaving.value = false;
    }
  }

  async function autoSaveChapterBody(): Promise<void> {
    if (!selectedChapter.value) return;
    if (chapterBodyDraft.value === lastPersistedBody) return;
    bodyAutoSaveStatus.value = 'saving';
    try {
      await saveCreatorChapterBody({
        chapter: selectedChapter.value,
        body: chapterBodyDraft.value,
        autosave: true,
      });
      lastPersistedBody = chapterBodyDraft.value;
      bodyLastSavedAt.value = new Date();
      bodyAutoSaveStatus.value = 'saved';
    } catch {
      bodyAutoSaveStatus.value = 'idle';
    }
  }

  function bindChapterBodyTextareaRef(el: unknown): void {
    (chapterBodyTextareaRef as Ref<unknown>).value = el;
    if (autoSaveTimer) {
      clearTimeout(autoSaveTimer);
      autoSaveTimer = null;
    }
    if (!el) return;
    autoSaveTimer = setTimeout(() => {
      void autoSaveChapterBody();
    }, 1500);
  }

  function maybeAutoSelectWritingChapter(): void {
    const ov = overview.value;
    if (!ov) return;
    const chapters = (ov as { chapters?: ChapterRow[] }).chapters || [];
    const focus = focusChapter?.value;
    if (focus != null && chapters.some((ch) => ch.chapter === focus)) {
      void selectChapter(focus);
      return;
    }
    const target = chapters.find((ch) => !ch.has_body) || chapters[0];
    if (target?.chapter != null) {
      void selectChapter(target.chapter);
    }
  }

  onUnmounted(() => {
    if (autoSaveTimer) clearTimeout(autoSaveTimer);
  });

  return {
    deviationChapters,
    alertChapters,
    visibleChapters,
    showCompanionLogicCheckInWrite,
    syncMemoryAssets,
    selectChapter,
    jumpToChapter,
    saveChapterBody,
    saveChapterOutline,
    autoSaveChapterBody,
    bindChapterBodyTextareaRef,
    maybeAutoSelectWritingChapter,
  };
}