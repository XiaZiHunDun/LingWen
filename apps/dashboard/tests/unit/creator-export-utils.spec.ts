import { describe, it, expect } from 'vitest';
import {
  buildFullBookMarkdown,
  buildSubmissionPackMarkdown,
  defaultSubmissionChapterNums,
  formatChapterMarkdown,
  safeExportFilename,
} from '../../src/utils/creatorExportUtils.js';

describe('creatorExportUtils', () => {
  it('formatChapterMarkdown falls back to excerpt', () => {
    expect(formatChapterMarkdown({ chapter: 2, excerpt: '片段' })).toContain('片段');
    expect(formatChapterMarkdown({ chapter: 3 })).toContain('暂无正文');
  });

  it('buildFullBookMarkdown includes pillars outline and chapters', () => {
    const md = buildFullBookMarkdown({
      projectTitle: '测试书',
      pillars: '支柱',
      outline: '大纲',
      chapters: [{ chapter: 1, title: '开篇', body: '正文' }],
    });
    expect(md).toContain('测试书');
    expect(md).toContain('创作支柱');
    expect(md).toContain('开篇');
  });

  it('buildSubmissionPackMarkdown truncates long pillars', () => {
    const md = buildSubmissionPackMarkdown({
      projectTitle: '投稿',
      pillars: 'x'.repeat(1300),
      sampleChapters: [{ chapter: 1, body: '试读' }],
    });
    expect(md).toContain('投稿包');
    expect(md.length).toBeLessThan(5000);
  });

  it('defaultSubmissionChapterNums picks first N written chapters', () => {
    expect(defaultSubmissionChapterNums([1, 2, 3, 4], 12, 2)).toEqual([1, 2]);
    expect(defaultSubmissionChapterNums([1], 12, 3)).toEqual([1]);
  });

  it('safeExportFilename sanitizes slug', () => {
    expect(safeExportFilename('我的书!!', 'full')).toBe('我的书-full.md');
    expect(safeExportFilename('', 'pack')).toBe('lingwen-novel-pack.md');
  });
});
