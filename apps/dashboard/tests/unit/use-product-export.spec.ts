/**
 * useProductExport 子模块独立测试
 *
 * Phase 27: 为 Phase 19.1 useProductExport 子模块添加专门测试。
 * 重点测试：导出向导状态控制 + 简单配置场景。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref } from 'vue';

// Mock API
const exportMocks = vi.hoisted(() => ({
  fetchCreatorChapterPreview: vi.fn(),
  fetchChapters: vi.fn(),
  exportCreatorEpub: vi.fn(),
  exportCreatorDocx: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorChapterPreview: (...args: unknown[]) => exportMocks.fetchCreatorChapterPreview(...args),
  fetchChapters: (...args: unknown[]) => exportMocks.fetchChapters(...args),
}));

vi.mock('../../src/api/export.js', () => ({
  exportCreatorEpub: (...args: unknown[]) => exportMocks.exportCreatorEpub(...args),
  exportCreatorDocx: (...args: unknown[]) => exportMocks.exportCreatorDocx(...args),
}));

vi.mock('../../src/api/content.js', () => ({
  fetchCreatorChapterPreview: (...args: unknown[]) => exportMocks.fetchCreatorChapterPreview(...args),
}));

// Mock utils（导出相关）
vi.mock('../../src/utils/creatorExportUtils.js', () => ({
  buildFullBookMarkdown: vi.fn(() => '# Full Book\nContent'),
  buildSubmissionPackMarkdown: vi.fn(() => '# Submission\nPack'),
  defaultSubmissionChapterNums: vi.fn((nums: number[]) => nums),
  downloadTextFile: vi.fn(),
  downloadBlobFile: vi.fn(),
  safeExportFilename: (slug: string, suffix: string) => `${slug}-${suffix}`,
}));

vi.mock('../../src/utils/displayProjectName.js', () => ({
  normalizeVolumePlanVolumes: (v: unknown) => v,
}));

import { useProductExport } from '../../src/composables/useCreatorProductTools/useProductExport';

function mountExport(overviewData: Record<string, unknown> | null = null) {
  const overview = ref<Record<string, unknown> | null>(overviewData);
  const error = ref<string | null>(null);
  const saveMessage = ref('');
  const activeSlug = ref('demo-novel');
  return { ...useProductExport({
    overview, error, saveMessage,
    pillarsText: ref(''), globalOutlineText: ref(''), activeSlug,
  }), saveMessage };
}

describe('useProductExport', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initial state has closed modal and idle', () => {
    const exp = mountExport();
    expect(exp.exportModalOpen.value).toBe(false);
    expect(exp.exportBusy.value).toBe(false);
    expect(exp.exportPreview.value).toBe('');
    expect(exp.exportMode.value).toBe('full');
  });

  it('openExportModal opens with default full mode', () => {
    const exp = mountExport();
    exp.openExportModal();
    expect(exp.exportModalOpen.value).toBe(true);
    expect(exp.exportMode.value).toBe('full');
    expect(exp.exportPreview.value).toBe('');
  });

  it('openExportModal accepts custom mode', () => {
    const exp = mountExport();
    exp.openExportModal('submission');
    expect(exp.exportMode.value).toBe('submission');
  });

  it('openExportModal sets range to max_chapter when present', () => {
    const exp = mountExport({ max_chapter: 12 });
    exp.openExportModal();
    expect(exp.exportRangeEnd.value).toBe(12);
  });

  it('closeExportModal closes and resets busy', () => {
    const exp = mountExport();
    exp.exportBusy.value = true;
    exp.closeExportModal();
    expect(exp.exportModalOpen.value).toBe(false);
    expect(exp.exportBusy.value).toBe(false);
  });

  it('setExportMode updates mode', () => {
    const exp = mountExport();
    exp.setExportMode('range');
    expect(exp.exportMode.value).toBe('range');
  });

  it('resolveExportChapterNums generates range for range mode', async () => {
    const exp = mountExport();
    exp.setExportMode('range');
    exp.exportRangeStart.value = 2;
    exp.exportRangeEnd.value = 5;
    const nums = await exp.resolveExportChapterNums();
    expect(nums).toEqual([2, 3, 4, 5]);
  });

  it('resolveExportChapterNums inverts range when start > end', async () => {
    const exp = mountExport();
    exp.setExportMode('range');
    exp.exportRangeStart.value = 5;
    exp.exportRangeEnd.value = 2;
    const nums = await exp.resolveExportChapterNums();
    expect(nums).toEqual([2, 3, 4, 5]);
  });

  it('resolveExportChapterNums handles full mode via fetchChapters', async () => {
    exportMocks.fetchChapters.mockResolvedValueOnce({
      chapters: [
        { chapter: 1, has_body: true },
        { chapter: 2, has_body: true },
        { chapter: 3, has_body: true },
      ],
    });
    const exp = mountExport({
      chapters: [{ chapter: 1, has_body: true }, { chapter: 2, has_body: true }, { chapter: 3, has_body: true }],
      max_chapter: 3,
    });
    exp.setExportMode('full');
    const nums = await exp.resolveExportChapterNums();
    expect(nums).toEqual([1, 2, 3]);
  });

  it('runExportEpub calls API and closes modal', async () => {
    exportMocks.exportCreatorEpub.mockResolvedValueOnce(new Blob(['epub']));
    const exp = mountExport();
    exp.openExportModal();
    await exp.runExportEpub();
    expect(exportMocks.exportCreatorEpub).toHaveBeenCalledTimes(1);
    expect(exp.exportModalOpen.value).toBe(false);
  });

  it('runExportDocx calls API and closes modal', async () => {
    exportMocks.exportCreatorDocx.mockResolvedValueOnce(new Blob(['docx']));
    const exp = mountExport();
    exp.openExportModal();
    await exp.runExportDocx();
    expect(exportMocks.exportCreatorDocx).toHaveBeenCalledTimes(1);
    expect(exp.exportModalOpen.value).toBe(false);
  });

  it('runExportEpub sets error on API failure', async () => {
    exportMocks.exportCreatorEpub.mockRejectedValueOnce(new Error('epub-failed'));
    const exp = mountExport();
    exp.openExportModal();
    await exp.runExportEpub();
    expect(exp.exportModalOpen.value).toBe(true); // modal stays open on error
  });
});
