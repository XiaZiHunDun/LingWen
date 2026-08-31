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
import { computed, nextTick, onUnmounted, ref } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import type { CreatorChapterPreview, CreatorLogicCheckResponse } from '@lingwen/dashboard-contracts/shared';
import {
  fetchCreatorChapterPreview,
  saveCreatorChapterBody,
  saveCreatorChapterOutline,
} from '@/api/content';
import { saveWriteResume } from '../../utils/writeResumeStorage.js';
import { extractMentionedEntityNames } from '../../utils/creatorChapterEntityUtils.js';

interface ChapterRow {
  chapter: number;
  has_body?: boolean;
}

interface Deviation {
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
  chapterPreview: Ref<CreatorChapterPreview | null>;
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
  memoryAssetsCache?: Ref<Array<Record<string, unknown>>>;
  lastPersistedBodyRef?: Ref<string>;
}

export interface WriteFlowReturn {
  deviationChapters: ComputedRef<Set<number>>;
  alertChapters: ComputedRef<Set<number>>;
  visibleChapters: ComputedRef<ChapterRow[]>;
  showCompanionLogicCheckInWrite: ComputedRef<boolean>;
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
    memoryAssetsCache,
    lastPersistedBodyRef,
  } = deps;

  const memCache = memoryAssetsCache || ref<Array<Record<string, unknown>>>([]);
  const lastPersistedBody = lastPersistedBodyRef || ref<string>('');

  let autoSaveTimer: ReturnType<typeof setTimeout> | null = null;

  function syncMemoryAssets(items: Array<Record<string, unknown>>): void {
    memCache.value = Array.isArray(items) ? items : [];
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
    chapterPreview.value = null;
    chapterBodyDraft.value = '';
    chapterOutlineDraft.value = '';
    if (chapterRecheckResult.value?.chapter !== chapter) {
      chapterRecheckResult.value = null;
    }
    try {
      const full = Boolean(
        (uiProfile.value as { chapter_inline_edit?: boolean }).chapter_inline_edit
          || (uiProfile.value as { chapter_full_preview?: boolean }).chapter_full_preview
          || (uiProfile.value as { chapter_outline_inline_edit?: boolean }).chapter_outline_inline_edit
          || (uiProfile.value as { chapter_outline_read_preview?: boolean }).chapter_outline_read_preview,
      );
      // N.13 T2.P1.c: typed wrapper returns CreatorChapterPreview (body/outline).
      // The legacy ``body_text``/``body_preview``/``outline_text``/``outline_preview``
      // field names were never in the backend response — the cast was masking a latent
      // bug where the body/outline draft was always populated as ``''``. Read the
      // canonical fields directly.
      chapterPreview.value = await fetchCreatorChapterPreview(chapter, { full });
      chapterBodyDraft.value = chapterPreview.value?.body ?? '';
      chapterOutlineDraft.value = chapterPreview.value?.outline ?? '';
      lastPersistedBody.value = chapterBodyDraft.value;
      bodyLastSavedAt.value = null;
      bodyAutoSaveStatus.value = 'idle';
      const slug = (overview.value as { slug?: string } | null)?.slug;
      if (slug) {
        saveWriteResume(slug, { chapter, projectName: (overview.value as { name?: string } | null)?.name });
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      previewLoading.value = false;
    }
  }

  async function jumpToChapter(chapter: number): Promise<void> {
    await selectChapter(chapter);
    await nextTick();
    try {
      document.querySelector('[data-testid="chapter-preview-panel"]')?.scrollIntoView?.({
        behavior: 'smooth',
        block: 'start',
      });
    } catch { /* jsdom */ }
  }

  async function saveChapterBody(): Promise<void> {
    if (!selectedChapter.value) return;
    chapterBodySaving.value = true;
    saveMessage.value = '';
    try {
      chapterPreview.value = await saveCreatorChapterBody({
        chapter_id: selectedChapter.value,
        body: chapterBodyDraft.value,
      });
      chapterBodyDraft.value = chapterPreview.value?.body ?? chapterBodyDraft.value;
      chapterOutlineDraft.value = chapterPreview.value?.outline ?? chapterOutlineDraft.value;
      lastPersistedBody.value = chapterBodyDraft.value;
      bodyLastSavedAt.value = new Date();
      bodyAutoSaveStatus.value = 'saved';
      const mentioned = extractMentionedEntityNames(
        chapterBodyDraft.value,
        memCache.value as Array<{ kind: string; name: string }>,
      );
      saveMessage.value = mentioned.length
        ? `ch${String(selectedChapter.value).padStart(3, '0')} 正文已保存 · 涉及：${mentioned.join('、')}`
        : `ch${String(selectedChapter.value).padStart(3, '0')} 正文已保存`;
      const slug = (overview.value as { slug?: string } | null)?.slug;
      if (slug) {
        saveWriteResume(slug, {
          chapter: selectedChapter.value,
          projectName: (overview.value as { name?: string } | null)?.name,
        });
      }
      await onAfterChapterSave();
      if ((uiProfile.value as { chapter_save_p0_recheck?: boolean }).chapter_save_p0_recheck) {
        const { runCreatorLogicCheck } = await import('@/api/content');
        // v16.2.7 T8: typed wrapper's runCreatorLogicCheck takes `chapter?: number`,
        // legacy caller passes object. Cast preserves runtime behavior. (T3.P2.b carryover.)
        // N.13 T2.P1.c: ``CreatorLogicCheckResponse`` now exposes ``p0_count`` (canonical
        // field per v16.5 #N backend); drop the local ``{ p0_count?: number }`` cast.
        const result: CreatorLogicCheckResponse = await runCreatorLogicCheck({ chapter: selectedChapter.value } as unknown as Parameters<typeof runCreatorLogicCheck>[0]);
        chapterRecheckResult.value = { ...result, chapter: selectedChapter.value };
        if ((result.p0_count || 0) > 0) {
          saveMessage.value = `ch${String(selectedChapter.value).padStart(3, '0')} 保存后复查：发现 ${result.p0_count} 条 P0`;
        }
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      chapterBodySaving.value = false;
    }
  }

  async function saveChapterOutline(): Promise<void> {
    if (!selectedChapter.value) return;
    chapterOutlineSaving.value = true;
    saveMessage.value = '';
    try {
      chapterPreview.value = await saveCreatorChapterOutline({
        chapter_id: selectedChapter.value,
        outline: chapterOutlineDraft.value,
      });
      const slug = (overview.value as { slug?: string } | null)?.slug;
      if (slug) {
        saveWriteResume(slug, {
          chapter: selectedChapter.value,
          projectName: (overview.value as { name?: string } | null)?.name,
        });
      }
      saveMessage.value = `ch${String(selectedChapter.value).padStart(3, '0')} 大纲已保存`;
      await onAfterChapterSave();
    } catch (e) {
      handleSaveError(e);
    } finally {
      chapterOutlineSaving.value = false;
    }
  }

  async function autoSaveChapterBody(): Promise<void> {
    if (!selectedChapter.value || chapterBodySaving.value) return;
    if (chapterBodyDraft.value === lastPersistedBody.value) return;
    chapterBodySaving.value = true;
    bodyAutoSaveStatus.value = 'saving';
    try {
      chapterPreview.value = await saveCreatorChapterBody({
        chapter_id: selectedChapter.value,
        body: chapterBodyDraft.value,
      });
      lastPersistedBody.value = chapterBodyDraft.value;
      bodyLastSavedAt.value = new Date();
      bodyAutoSaveStatus.value = 'saved';
      const slug = (overview.value as { slug?: string } | null)?.slug;
      if (slug) {
        saveWriteResume(slug, {
          chapter: selectedChapter.value,
          projectName: (overview.value as { name?: string } | null)?.name,
        });
      }
      await onAfterChapterSave();
    } catch {
      bodyAutoSaveStatus.value = 'error';
    } finally {
      chapterBodySaving.value = false;
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
    selectChapter,
    jumpToChapter,
    saveChapterBody,
    saveChapterOutline,
    autoSaveChapterBody,
    bindChapterBodyTextareaRef,
    maybeAutoSelectWritingChapter,
  };
}
