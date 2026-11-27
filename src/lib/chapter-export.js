/**
 * 单章导出的纯函数实现。
 *
 * 语义与整书导出（src/app/api/books/[id]/export/route.ts）保持一致：
 * format 只接受 'md' / 'txt'，其它值（含 undefined / null / 大小写不符）一律按 'md' 处理。
 * 本文件不依赖数据库、不产生副作用，便于单元测试直接引入。
 */

/** 支持的导出格式。 */
export const CHAPTER_EXPORT_FORMATS = ['md', 'txt'];

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
 * 章节序号：优先取 seq，非法（缺失 / 非数字 / NaN / Infinity）时退回 1。
 * @param {unknown} value
 * @returns {number}
 */
function chapterSeq(value) {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  return 1;
}

/**
 * 规范化 format：只认 'txt'，其余一律 'md'（与整书导出同口径）。
 * @param {unknown} format
 * @returns {'md' | 'txt'}
 */
function normalizeFormat(format) {
  return format === 'txt' ? 'txt' : 'md';
}

/**
 * 生成单章导出内容。
 *
 * - md：首行 `# 第 N 章 标题`，空一行后接正文；contentType 为 text/markdown; charset=utf-8
 * - txt：首行 `第 N 章 标题`，空一行后接正文；contentType 为 text/plain; charset=utf-8
 * - 正文为空时只输出标题行
 * - filename 经过 encodeURIComponent，可直接放进 Content-Disposition 的 filename*=UTF-8''
 *
 * @param {unknown} chapter 章节记录（使用 seq / title / content 三个字段）
 * @param {unknown} [format] 'md' 或 'txt'，其它值按 'md' 处理
 * @returns {{ body: string, contentType: string, filename: string }}
 */
export function buildChapterExport(chapter, format) {
  const source = chapter !== null && typeof chapter === 'object' ? chapter : {};
  const seq = chapterSeq(source.seq);
  const title = titleOr(source.title, '未命名');
  const content = text(source.content);
  const normalizedFormat = normalizeFormat(format);

  const heading = normalizedFormat === 'md'
    ? `# 第 ${seq} 章 ${title}`
    : `第 ${seq} 章 ${title}`;

  const lines = [heading];
  if (content !== '') {
    // 标题行后留一个空行，再接正文。
    lines.push('');
    lines.push(content);
  }

  return {
    body: lines.join('\n').trimEnd() + '\n',
    contentType:
      normalizedFormat === 'md' ? 'text/markdown; charset=utf-8' : 'text/plain; charset=utf-8',
    filename: encodeURIComponent(`第 ${seq} 章 ${title}.${normalizedFormat}`),
  };
}
