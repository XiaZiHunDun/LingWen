/**
 * useProductExport — 导出向导 + Markdown/EPUB/DOCX 生成
 *
 * Phase 19 Task 1：从 useCreatorProductTools.js 拆出。
 * 负责: exportModal state + Markdown/EPUB/DOCX 三种格式下载 + 范围/投稿模式。
 *
 * 依赖 (deps):
 * - overview: 全局概览（含 max_chapter, chapters, pillars_excerpt, global_outline_excerpt）
 * - error, saveMessage
 * - pillarsText, globalOutlineText
 * - activeSlug: 项目 slug（用于文件名）
 */
import { computed, ref, watch } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import {
  fetchChapters,
  fetchCreatorChapterPreview,
  exportCreatorEpub,
  exportCreatorDocx,
} from '../../api/index.js';
import {
  buildFullBookMarkdown,
  buildSubmissionPackMarkdown,
  defaultSubmissionChapterNums,
  downloadTextFile,
  downloadBlobFile,
  safeExportFilename,
} from '../../utils/creatorExportUtils.js';

export interface ExportDeps {
  overview: Ref<Record<string, unknown> | null>;
  error: Ref<string | null>;
  saveMessage: Ref<string>;
  pillarsText: Ref<string>;
  globalOutlineText: Ref<string>;
  activeSlug: ComputedRef<string> | Ref<string>;
}

export interface ProductExportReturn {
  exportModalOpen: Ref<boolean>;
  exportMode: Ref<string>;
  exportRangeStart: Ref<number>;
  exportRangeEnd: Ref<number>;
  exportIntro: Ref<string>;
  exportAuthor: Ref<string>;
  exportDescription: Ref<string>;
  exportSubmissionSampleCount: Ref<number>;
  exportBusy: Ref<boolean>;
  exportPreview: Ref<string>;
  openExportModal: (mode?: string) => void;
  closeExportModal: () => void;
  refreshExportPreview: () => Promise<void>;
  runExportDownload: () => Promise<void>;
  runExportEpub: () => Promise<void>;
  runExportDocx: () => Promise<void>;
  setExportMode: (mode: string) => void;
  buildExportMarkdown: () => Promise<string>;
  resolveExportChapterNums: () => Promise<number[]>;
}

export function useProductExport(deps: ExportDeps): ProductExportReturn {
  const { overview, error, saveMessage, pillarsText, globalOutlineText, activeSlug } = deps;

  const exportModalOpen = ref(false);
  const exportMode = ref('full');
  const exportRangeStart = ref(1);
  const exportRangeEnd = ref(10);
  const exportIntro = ref('');
  const exportAuthor = ref('');
  const exportDescription = ref('');
  const exportSubmissionSampleCount = ref(3);
  const exportBusy = ref(false);
  const exportPreview = ref('');

  watch(
    () => (overview.value as { max_chapter?: number } | null)?.max_chapter,
    (max) => {
      if (max) exportRangeEnd.value = max;
    },
    { immediate: true },
  );

  watch(
    () => [activeSlug.value, (overview.value as { pillars_excerpt?: string } | null)?.pillars_excerpt],
    () => {
      if (!exportAuthor.value) {
        exportAuthor.value = activeSlug.value || '';
      }
      if (!exportDescription.value && (overview.value as { pillars_excerpt?: string } | null)?.pillars_excerpt) {
        exportDescription.value = (overview.value as { pillars_excerpt?: string }).pillars_excerpt!.slice(0, 280);
      }
    },
    { immediate: true },
  );

  function openExportModal(mode: string = 'full'): void {
    exportMode.value = mode;
    exportModalOpen.value = true;
    exportPreview.value = '';
    const maxCh = (overview.value as { max_chapter?: number } | null)?.max_chapter;
    if (maxCh) {
      exportRangeEnd.value = maxCh;
    }
  }

  function closeExportModal(): void {
    exportModalOpen.value = false;
    exportBusy.value = false;
  }

  async function loadChapterBodies(chapterNums: number[]): Promise<Array<Record<string, unknown>>> {
    const chapters: Array<Record<string, unknown>> = [];
    for (const num of chapterNums) {
      try {
        const preview = await fetchCreatorChapterPreview(num, { full: true }) as { title?: string; body_text?: string; body_preview?: string; excerpt?: string };
        chapters.push({
          chapter: num,
          title: preview.title || `第${num}章`,
          body: preview.body_text || preview.body_preview || preview.excerpt || '',
          excerpt: preview.excerpt,
        });
      } catch {
        const row = ((overview.value as { chapters?: Array<{ chapter: number; excerpt?: string }> } | null)?.chapters || []).find((c) => c.chapter === num);
        chapters.push({
          chapter: num,
          title: `第${num}章`,
          body: row?.excerpt || '',
          excerpt: row?.excerpt,
        });
      }
    }
    return chapters;
  }

  async function resolveExportChapterNums(): Promise<number[]> {
    if (exportMode.value === 'range') {
      const start = Math.min(exportRangeStart.value, exportRangeEnd.value);
      const end = Math.max(exportRangeStart.value, exportRangeEnd.value);
      const nums: number[] = [];
      for (let n = start; n <= end; n += 1) nums.push(n);
      return nums;
    }
    if (exportMode.value === 'submission') {
      const resp = await fetchChapters() as { chapters?: Array<{ chapter: number; has_body?: boolean }> };
      const nums = (resp.chapters || [])
        .filter((c) => c.has_body)
        .map((c) => c.chapter);
      return defaultSubmissionChapterNums(
        nums,
        (overview.value as { max_chapter?: number } | null)?.max_chapter,
        exportSubmissionSampleCount.value,
      );
    }
    const resp = await fetchChapters() as { chapters?: Array<{ chapter: number; has_body?: boolean }> };
    return (resp.chapters || [])
      .filter((c) => c.has_body)
      .map((c) => c.chapter)
      .sort((a, b) => a - b);
  }

  async function buildExportMarkdown(): Promise<string> {
    const chapterNums = await resolveExportChapterNums();
    const chapters = await loadChapterBodies(chapterNums);
    const projectTitle = activeSlug.value || '灵文作品';
    const pillars = pillarsText.value || (overview.value as { pillars_excerpt?: string } | null)?.pillars_excerpt || '';
    const outline = globalOutlineText.value || (overview.value as { global_outline_excerpt?: string } | null)?.global_outline_excerpt || '';

    if (exportMode.value === 'submission') {
      return buildSubmissionPackMarkdown({
        projectTitle,
        intro: exportIntro.value,
        pillars,
        outline,
        sampleChapters: chapters as Parameters<typeof buildSubmissionPackMarkdown>[0]['sampleChapters'],
      });
    }
    return buildFullBookMarkdown({
      projectTitle,
      pillars,
      outline,
      chapters: chapters as Parameters<typeof buildFullBookMarkdown>[0]['chapters'],
    });
  }

  function exportRequestBody(): Record<string, unknown> {
    const body: Record<string, unknown> = {
      mode: exportMode.value,
      title: activeSlug.value || '灵文作品',
      author: exportAuthor.value || undefined,
      description: exportDescription.value || undefined,
    };
    if (exportMode.value === 'range') {
      body.start_chapter = Math.min(exportRangeStart.value, exportRangeEnd.value);
      body.end_chapter = Math.max(exportRangeStart.value, exportRangeEnd.value);
    }
    if (exportMode.value === 'submission') {
      body.submission_sample_count = exportSubmissionSampleCount.value;
    }
    return body;
  }

  async function refreshExportPreview(): Promise<void> {
    exportBusy.value = true;
    try {
      exportPreview.value = await buildExportMarkdown();
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      exportBusy.value = false;
    }
  }

  async function runExportDownload(): Promise<void> {
    exportBusy.value = true;
    try {
      const markdown = await buildExportMarkdown();
      const slug = activeSlug.value || 'novel';
      const suffix = exportMode.value === 'submission' ? 'submission' : exportMode.value;
      downloadTextFile(safeExportFilename(slug, suffix), markdown);
      saveMessage.value = '作品已导出为 Markdown';
      closeExportModal();
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      exportBusy.value = false;
    }
  }

  async function runExportEpub(): Promise<void> {
    exportBusy.value = true;
    try {
      const slug = activeSlug.value || 'novel';
      const blob = await exportCreatorEpub(exportRequestBody());
      downloadBlobFile(safeExportFilename(slug, exportMode.value).replace(/\.md$/, '.epub'), blob);
      saveMessage.value = '作品已导出为 EPUB';
      closeExportModal();
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      exportBusy.value = false;
    }
  }

  async function runExportDocx(): Promise<void> {
    exportBusy.value = true;
    try {
      const slug = activeSlug.value || 'novel';
      const blob = await exportCreatorDocx(exportRequestBody());
      downloadBlobFile(safeExportFilename(slug, exportMode.value).replace(/\.md$/, '.docx'), blob);
      saveMessage.value = '作品已导出为 DOCX';
      closeExportModal();
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      exportBusy.value = false;
    }
  }

  function setExportMode(mode: string): void {
    exportMode.value = mode;
  }

  return {
    exportModalOpen,
    exportMode,
    exportRangeStart,
    exportRangeEnd,
    exportIntro,
    exportAuthor,
    exportDescription,
    exportSubmissionSampleCount,
    exportBusy,
    exportPreview,
    openExportModal,
    closeExportModal,
    refreshExportPreview,
    runExportDownload,
    runExportEpub,
    runExportDocx,
    setExportMode,
    buildExportMarkdown,
    resolveExportChapterNums,
  };
}
