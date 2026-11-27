/**
 * 整本书导出的纯函数实现（无数据库依赖、无副作用）。
 *
 * 与单章导出（src/lib/chapter-export.js）保持同一风格与 format 口径：
 * format 只接受 'md' / 'txt'，其它值（含 undefined / null / 大小写不符）一律按 'md' 处理。
 * 章节顺序由调用方（repo.getBookExport 的 listChapters）保证为 seq ASC, id ASC。
 */

import { countWords } from './wordcount.js';

/** 支持的导出格式。 */
export const BOOK_EXPORT_FORMATS = ['md', 'txt'];

/**
 * 文本字段：非字符串按空串处理。
 * @param {unknown} value
 * @returns {string}
 */
function text(value) {
  return typeof value === 'string' ? value : '';
}

/**
 * 标题字段：空串（或全空白）时给出兜底文案。
 * @param {unknown} value
 * @param {string} fallback
 * @returns {string}
 */
function titleOr(value, fallback) {
  const raw = text(value).trim();
  return raw === '' ? fallback : raw;
}

/**
 * 章节序号：优先取 seq，非法（缺失 / 非数字 / NaN / Infinity）时按数组下标 + 1 兜底。
 * @param {unknown} value
 * @param {number} index 章节在数组中的下标
 * @returns {number}
 */
function chapterSeq(value, index) {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  return index + 1;
}

/**
 * 规范化 format：只认 'txt'，其余一律 'md'。
 * @param {unknown} format
 * @returns {'md' | 'txt'}
 */
function normalizeFormat(format) {
  return format === 'txt' ? 'txt' : 'md';
}

/**
 * 转义单行的「行首」Markdown 活性字符：标题（#）、引用（>）、列表（- + *）、
 * 有序列表（1.）、表格（|）。行首允许前置空白。
 * @param {string} line
 * @returns {string}
 */
function escapeLineStart(line) {
  return line
    .replace(/^(\s*)(#{1,6}|>|\|)/u, '$1\\$2')
    .replace(/^(\s*)([-+*])(\s)/u, '$1\\$2$3')
    .replace(/^(\s*)(\d+)(\.)(\s)/u, '$1$2\\$3$4');
}

/**
 * 把正文字面化，保证渲染后仍是原文而不是 Markdown 结构。
 *
 * 顺序很重要：先转义反斜杠（\ → \\），再逐行处理行首活性字符，
 * 否则新加出来的反斜杠会被二次转义。
 *
 * @param {unknown} content 章节正文
 * @returns {string} 转义后的正文（txt 格式不使用本函数）
 */
export function escapeMarkdownBody(content) {
  const source = text(content).replace(/\r\n/gu, '\n');
  if (source === '') return '';
  const escaped = source.split('\\').join('\\\\');
  return escaped.split('\n').map(escapeLineStart).join('\n');
}

/**
 * 生成整书导出内容。
 *
 * - md：首行 `# 书名`（可选 `> 类型：` / `> 简介：` 两行元信息），每章
 *   `## 第 N 章 标题` + 空行 + 转义后的正文；末尾 `---` 分隔的统计段。
 * - txt：纯文本、**不**转义，末尾同样附带统计段。
 * - 空正文只输出标题行。
 * - filename 经过 encodeURIComponent，可直接放进 Content-Disposition 的 filename*=UTF-8''
 *
 * @param {{ book?: unknown, chapters?: unknown }} input 书籍与章节（章节顺序即输出顺序）
 * @param {unknown} [format] 'md' 或 'txt'，其它值按 'md' 处理
 * @returns {{ body: string, contentType: string, filename: string,
 *   chapterCount: number, wordCount: number }}
 */
export function buildBookExport({ book, chapters } = {}, format) {
  const source = book !== null && typeof book === 'object' ? book : {};
  const list = Array.isArray(chapters) ? chapters : [];
  const normalizedFormat = normalizeFormat(format);
  const title = titleOr(source.title, '未命名');

  let wordCount = 0;
  for (const chapter of list) {
    const row = chapter !== null && typeof chapter === 'object' ? chapter : {};
    wordCount += countWords(row.content);
  }

  const stats = `共 ${list.length} 章，总字数 ${wordCount} 字。`;
  /** @type {string[]} */
  const blocks = [];

  if (normalizedFormat === 'md') {
    const header = [`# ${title}`];
    const genre = text(source.genre).trim();
    const summary = text(source.summary).trim();
    if (genre !== '') header.push(`> 类型：${genre}`);
    if (summary !== '') header.push(`> 简介：${summary}`);
    blocks.push(header.join('\n'));

    list.forEach((chapter, index) => {
      const row = chapter !== null && typeof chapter === 'object' ? chapter : {};
      const heading = `## 第 ${chapterSeq(row.seq, index)} 章 ${titleOr(row.title, '未命名')}`;
      const content = text(row.content);
      // 正文必须转义，避免正文里的 `# 开头` 被渲染成标题。
      blocks.push(content === '' ? heading : `${heading}\n\n${escapeMarkdownBody(content)}`);
    });

    blocks.push(`---\n\n${stats}`);
  } else {
    blocks.push(title);

    list.forEach((chapter, index) => {
      const row = chapter !== null && typeof chapter === 'object' ? chapter : {};
      const heading = `第 ${chapterSeq(row.seq, index)} 章 ${titleOr(row.title, '未命名')}`;
      const content = text(row.content);
      // txt 保持原文，不做任何转义。
      blocks.push(content === '' ? heading : `${heading}\n${content}`);
    });

    blocks.push(stats);
  }

  return {
    body: blocks.join('\n\n').trimEnd() + '\n',
    contentType:
      normalizedFormat === 'md' ? 'text/markdown; charset=utf-8' : 'text/plain; charset=utf-8',
    filename: encodeURIComponent(`${title}.${normalizedFormat}`),
    chapterCount: list.length,
    wordCount,
  };
}
