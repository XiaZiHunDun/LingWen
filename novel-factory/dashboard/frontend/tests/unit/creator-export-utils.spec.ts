import { describe, it, expect } from 'vitest';
import {
  buildFullBookMarkdown,
  buildSubmissionPackMarkdown,
  defaultSubmissionChapterNums,
  formatChapterMarkdown,
  safeExportFilename,
} from '../../src/utils/creatorExportUtils.js';

describe('creatorExportUtils', () => {
  it('formatChapterMarkdown includes title and body', () => {
    const md = formatChapterMarkdown({ chapter: 1, title: '开端', body: '正文内容' });
    expect(md).toContain('## 开端');
    expect(md).toContain('正文内容');
  });

  it('buildFullBookMarkdown stitches pillars outline and chapters', () => {
    const md = buildFullBookMarkdown({
      projectTitle: '测试书',
      pillars: '支柱',
      outline: '大纲',
      chapters: [{ chapter: 1, body: '第一章' }],
    });
    expect(md).toContain('# 测试书');
    expect(md).toContain('创作支柱');
    expect(md).toContain('全局大纲');
    expect(md).toContain('第一章');
  });

  it('buildSubmissionPackMarkdown includes intro and samples', () => {
    const md = buildSubmissionPackMarkdown({
      projectTitle: '投稿',
      intro: '简介',
      sampleChapters: [{ chapter: 1, body: '试读' }],
    });
    expect(md).toContain('投稿包');
    expect(md).toContain('简介');
    expect(md).toContain('试读');
  });

  it('defaultSubmissionChapterNums returns up to sample count chapters', () => {
    expect(defaultSubmissionChapterNums([1, 2, 3, 4, 5])).toEqual([1, 2, 3]);
    expect(defaultSubmissionChapterNums([1, 2, 3, 4, 5], 12, 5)).toEqual([1, 2, 3, 4, 5]);
    expect(defaultSubmissionChapterNums([1, 2])).toEqual([1, 2]);
  });

  it('safeExportFilename sanitizes slug', () => {
    expect(safeExportFilename('我的书!', 'full')).toBe('我的书-full.md');
  });
});
