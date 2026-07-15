/**
 * 作品导出纯函数（前端拼 Markdown，后端 ZIP/EPUB 可后接）
 */

/**
 * @param {string} filename
 * @param {string} content
 * @param {string} [mime]
 */
export function downloadTextFile(filename, content, mime = 'text/markdown;charset=utf-8') {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

/**
 * @param {{ chapter: number, title?: string, body?: string, excerpt?: string }} ch
 */
export function formatChapterMarkdown(ch) {
  const title = ch.title || `第${ch.chapter}章`;
  const body = ch.body || ch.excerpt || '（暂无正文）';
  return `## ${title}\n\n${body}\n`;
}

/**
 * @param {{
 *   projectTitle?: string,
 *   pillars?: string,
 *   outline?: string,
 *   chapters: Array<{ chapter: number, title?: string, body?: string, excerpt?: string }>,
 * }} opts
 */
export function buildFullBookMarkdown(opts) {
  const lines = [
    `# ${opts.projectTitle || '未命名作品'}`,
    '',
    '> 由灵文创作伴侣导出',
    '',
  ];
  if (opts.pillars?.trim()) {
    lines.push('## 创作支柱', '', opts.pillars.trim(), '');
  }
  if (opts.outline?.trim()) {
    lines.push('## 全局大纲', '', opts.outline.trim(), '');
  }
  lines.push('---', '');
  for (const ch of opts.chapters) {
    lines.push(formatChapterMarkdown(ch));
  }
  return `${lines.join('\n')}\n`;
}

/**
 * @param {{
 *   projectTitle?: string,
 *   intro?: string,
 *   pillars?: string,
 *   outline?: string,
 *   sampleChapters: Array<{ chapter: number, title?: string, body?: string, excerpt?: string }>,
 * }} opts
 */
export function buildSubmissionPackMarkdown(opts) {
  const lines = [
    `# ${opts.projectTitle || '未命名作品'} · 投稿包`,
    '',
    '## 作品简介',
    '',
    opts.intro?.trim() || '（请在导出前补充简介）',
    '',
    '## 创作支柱（节选）',
    '',
    (opts.pillars?.trim() || '（暂无）').slice(0, 1200),
    '',
    '## 全局大纲（节选）',
    '',
    (opts.outline?.trim() || '（暂无）').slice(0, 2000),
    '',
    '## 试读章节',
    '',
  ];
  for (const ch of opts.sampleChapters) {
    lines.push(formatChapterMarkdown(ch));
  }
  lines.push('---', '', '_投稿包由灵文导出，发布前请按平台规则调整格式。_');
  return `${lines.join('\n')}\n`;
}

/**
 * @param {number[]} chapterNums
 * @param {number} [maxChapter]
 * @param {number} [sampleCount]
 */
export function defaultSubmissionChapterNums(chapterNums, maxChapter = 12, sampleCount = 3) {
  const written = chapterNums.filter((n) => n > 0).sort((a, b) => a - b);
  const count = Math.max(1, Math.min(sampleCount || 3, 12));
  if (written.length <= count) return written;
  return written.slice(0, count);
}

/**
 * @param {string} slug
 * @param {string} suffix
 */
export function safeExportFilename(slug, suffix) {
  const raw = (slug || 'lingwen-novel').replace(/[^\w\u4e00-\u9fff-]+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
  const base = raw || 'lingwen-novel';
  return `${base}-${suffix}.md`;
}

/**
 * @param {string} filename
 * @param {Blob} blob
 */
export function downloadBlobFile(filename, blob) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
